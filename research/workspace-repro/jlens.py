"""Scaled-down reproduction of the Jacobian lens (J-lens) from
"Verbalizable Representations Form a Global Workspace in Language Models"
(Gurnee et al., Transformer Circuits, 2026-07).

Approximations relative to the paper (documented deviations):
  * Concept lens vectors v_t(l) = E[ d logit_t(last) / d h_{l,p} ] are computed
    by batched backprop, averaged over a pretraining-like corpus and over the
    last few content positions p. This equals row t of W_U @ J_l with the
    target restricted to the final position (the paper averages over t' >= t).
  * Full-vocabulary readouts W_U @ E[J_l] @ h_hat are estimated by central
    finite differences (perturb h_l by +/- eps * h_hat at a sampled position,
    read delta logits at the final position), averaged over the corpus. The
    linearization therefore includes the final RMSNorm Jacobian, which the
    paper applies explicitly via norm().
  * Model: Qwen2.5-1.5B-Instruct on Apple MPS, fp32 (the paper uses Claude
    Sonnet/Haiku/Opus internals, unavailable externally).
"""

import json
import os
import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

from corpus import AVERAGING_CORPUS

_LOCAL_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "models", "qwen2.5-1.5b-instruct")
MODEL_NAME = _LOCAL_MODEL if os.path.isdir(_LOCAL_MODEL) else "Qwen/Qwen2.5-1.5B-Instruct"
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def pick_device():
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class JLens:
    def __init__(self, model_name=MODEL_NAME, device=None, dtype=torch.float32):
        self.device = device or pick_device()
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.tok.padding_side = "left"
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, dtype=dtype, attn_implementation="eager"
        ).to(self.device)
        self.model.eval()
        for p in self.model.parameters():
            p.requires_grad_(False)
        self.layers = self.model.model.layers
        self.n_layers = len(self.layers)
        self.d_model = self.model.config.hidden_size
        self._captured = {}
        self._capture_grad = False
        self._perturb = None  # (layer_idx, delta_tensor [B,T,D]) added to layer output
        self._hooks = []
        for i, layer in enumerate(self.layers):
            self._hooks.append(layer.register_forward_hook(self._make_hook(i)))

    def _make_hook(self, idx):
        def hook(module, inputs, output):
            hs = output[0] if isinstance(output, tuple) else output
            if self._perturb is not None and self._perturb[0] == idx:
                hs = hs + self._perturb[1]
                self._captured[idx] = hs
                if isinstance(output, tuple):
                    return (hs,) + tuple(output[1:])
                return hs
            if self._capture_grad and hs.requires_grad:
                hs.retain_grad()
            self._captured[idx] = hs
            return output
        return hook

    # ---------------- basic passes ----------------

    def encode(self, texts, max_len=96):
        return self.tok(
            texts, return_tensors="pt", padding=True, truncation=True,
            max_length=max_len,
        ).to(self.device)

    def chat(self, user_msg, system=None):
        msgs = ([{"role": "system", "content": system}] if system else []) + [
            {"role": "user", "content": user_msg}
        ]
        return self.tok.apply_chat_template(
            msgs, tokenize=False, add_generation_prompt=True
        )

    def forward_capture(self, enc, grad=False):
        """Run forward, capturing residual stream at every layer output.

        With grad=True, the input embeddings are used as the autograd root
        (all parameters are frozen, so without this no graph would be built).
        """
        self._captured = {}
        self._capture_grad = grad
        if grad:
            with torch.enable_grad():
                emb = self.model.get_input_embeddings()(enc["input_ids"])
                emb = emb.detach().requires_grad_(True)
                out = self.model(inputs_embeds=emb,
                                 attention_mask=enc["attention_mask"])
        else:
            with torch.no_grad():
                out = self.model(**enc)
        self._capture_grad = False
        return out

    def content_positions(self, enc, window=6):
        """Per-sample list of the last `window` content positions (left pad)."""
        mask = enc["attention_mask"]
        T = mask.shape[1]
        pos = []
        for b in range(mask.shape[0]):
            n = int(mask[b].sum().item())
            start = T - n
            w = min(window, n - 1)
            pos.append(list(range(T - w, T)))
        return pos

    # ---------------- concept lens vectors (backprop) ----------------

    def concept_lens_vectors(self, token_ids, layers=None, corpus=None,
                             batch_size=6, window=6, save_path=None):
        """v_t(l) for each token t and layer l, averaged over corpus and the
        last `window` content positions. Returns dict layer -> [n_tok, D]."""
        corpus = corpus or AVERAGING_CORPUS
        layers = layers if layers is not None else list(range(self.n_layers))
        acc = {l: torch.zeros(len(token_ids), self.d_model) for l in layers}
        count = 0
        for i in range(0, len(corpus), batch_size):
            batch = corpus[i:i + batch_size]
            enc = self.encode(batch)
            out = self.forward_capture(enc, grad=True)
            logits_last = out.logits[:, -1, :]  # [B, V]
            pos = self.content_positions(enc, window)
            for ti, t in enumerate(token_ids):
                S = logits_last[:, t].sum()
                S.backward(retain_graph=(ti < len(token_ids) - 1))
                for l in layers:
                    g = self._captured[l].grad  # [B,T,D]
                    if g is None:
                        continue
                    for b in range(g.shape[0]):
                        acc[l][ti] += g[b, pos[b], :].mean(0).float().cpu()
                    self._captured[l].grad = None
            count += len(batch)
            del out
            print(f"  concept grads: {min(i+batch_size, len(corpus))}/{len(corpus)} prompts", flush=True)
        vecs = {l: (acc[l] / count) for l in layers}
        if save_path:
            torch.save({"token_ids": token_ids, "vecs": vecs}, save_path)
        return vecs

    # ---------------- full-vocab FD readout ----------------

    def fd_readout(self, layer, h_vec, corpus=None, batch_size=6,
                   eps_frac=0.05, window=6, n_prompts=36):
        """Estimate W_U E[J_layer] h_hat via central finite differences.

        Perturbs the layer output at the last `window` content positions of
        each averaging prompt by +/- eps * h_hat and reads delta logits at the
        final position. eps is eps_frac * (per-sample local residual norm).
        Returns [V] tensor of averaged directional logit derivatives.
        """
        corpus = (corpus or AVERAGING_CORPUS)[:n_prompts]
        h_hat = (h_vec / h_vec.norm()).to(self.device, torch.float32)
        total = torch.zeros(self.model.config.vocab_size)
        count = 0
        with torch.no_grad():
            for i in range(0, len(corpus), batch_size):
                batch = corpus[i:i + batch_size]
                enc = self.encode(batch)
                # clean pass to get local residual norms at perturb positions
                self.forward_capture(enc, grad=False)
                hs = self._captured[layer]  # [B,T,D]
                B, T, D = hs.shape
                pos = self.content_positions(enc, window)
                delta = torch.zeros(B, T, D, device=self.device)
                eps_b = torch.zeros(B, device=self.device)
                for b in range(B):
                    local_norm = hs[b, pos[b], :].norm(dim=-1).mean()
                    eps = eps_frac * local_norm
                    eps_b[b] = eps * len(pos[b])  # total perturbation scale
                    delta[b, pos[b], :] = eps * h_hat
                self._perturb = (layer, delta)
                lp = self.model(**enc).logits[:, -1, :]
                self._perturb = (layer, -delta)
                lm = self.model(**enc).logits[:, -1, :]
                self._perturb = None
                d = (lp - lm) / (2 * eps_b[:, None])
                total += d.float().sum(0).cpu()
                count += B
        return total / count

    # ---------------- corpus statistics ----------------

    _corpus_mean_cache = None

    def corpus_mean(self, layer, n_prompts=36):
        """Average residual-stream activation at `layer` over corpus content
        positions. Subtracting it from probe activations removes the large
        context-independent component that otherwise dominates lens readouts."""
        if self._corpus_mean_cache is None:
            self._corpus_mean_cache = {}
        if layer not in self._corpus_mean_cache:
            with torch.no_grad():
                enc = self.encode(AVERAGING_CORPUS[:n_prompts])
                self.forward_capture(enc, grad=False)
                for l in range(self.n_layers):
                    hs = self._captured[l]
                    mask = enc["attention_mask"].bool()
                    self._corpus_mean_cache[l] = hs[mask].mean(0).float().cpu()
        return self._corpus_mean_cache[layer]

    # ---------------- baselines & utilities ----------------

    def logit_lens(self, h_vec):
        """Standard logit lens: final RMSNorm then unembed."""
        with torch.no_grad():
            h = h_vec.to(self.device, torch.float32).unsqueeze(0)
            h = self.model.model.norm(h)
            return self.model.lm_head(h).squeeze(0).float().cpu()

    def get_activation(self, text, layer, position=-1):
        """Residual stream at (layer, position) for a single text."""
        enc = self.encode([text], max_len=512)
        self.forward_capture(enc, grad=False)
        return self._captured[layer][0, position, :].detach().float().cpu()

    def topk_tokens(self, scores, k=10):
        vals, idx = torch.topk(scores, k)
        return [(self.tok.decode([i]), float(v)) for i, v in zip(idx.tolist(), vals.tolist())]

    def token_rank(self, scores, token_id):
        return int((scores > scores[token_id]).sum().item()) + 1

    # ---------------- generation with interventions ----------------

    def _mean_resid_norm(self, layer, n=12):
        with torch.no_grad():
            enc = self.encode(AVERAGING_CORPUS[:n])
            self.forward_capture(enc, grad=False)
            hs = self._captured[layer]
            mask = enc["attention_mask"].unsqueeze(-1)
            norms = (hs * mask).norm(dim=-1)
            return float((norms.sum() / enc["attention_mask"].sum()).item())

    def generate(self, prompt_text, max_new_tokens=40, do_sample=False,
                 temperature=1.0, steer=None, ablate=None, seed=0):
        """Generate with optional interventions.

        steer:  list of (layer, vec[D], alpha) -> h += alpha * mean_norm(l) * vec_hat
                applied at every position, every step.
        ablate: dict layer -> Q [D, r] orthonormal basis; h -= (h @ Q) @ Q.T
        """
        handles = []
        try:
            if steer:
                for (l, vec, alpha) in steer:
                    v = (vec / vec.norm()).to(self.device, torch.float32)
                    scale = alpha * self._mean_resid_norm(l)
                    handles.append(self.layers[l].register_forward_hook(
                        self._steer_hook(v, scale)))
            if ablate:
                for l, Q in ablate.items():
                    Qd = Q.to(self.device, torch.float32)
                    handles.append(self.layers[l].register_forward_hook(
                        self._ablate_hook(Qd)))
            enc = self.tok([prompt_text], return_tensors="pt").to(self.device)
            if do_sample:
                torch.manual_seed(seed)
            with torch.no_grad():
                out = self.model.generate(
                    **enc, max_new_tokens=max_new_tokens, do_sample=do_sample,
                    temperature=temperature if do_sample else None,
                    top_p=0.95 if do_sample else None,
                    pad_token_id=self.tok.eos_token_id,
                )
            return self.tok.decode(out[0, enc["input_ids"].shape[1]:],
                                   skip_special_tokens=True)
        finally:
            for h in handles:
                h.remove()

    @staticmethod
    def _steer_hook(v_hat, scale):
        def hook(module, inputs, output):
            hs = output[0] if isinstance(output, tuple) else output
            hs = hs + scale * v_hat
            if isinstance(output, tuple):
                return (hs,) + tuple(output[1:])
            return hs
        return hook

    @staticmethod
    def _ablate_hook(Q):
        def hook(module, inputs, output):
            hs = output[0] if isinstance(output, tuple) else output
            coeff = hs @ Q          # [B,T,r]
            hs = hs - coeff @ Q.T
            if isinstance(output, tuple):
                return (hs,) + tuple(output[1:])
            return hs
        return hook

    def nll_of_text(self, text, ablate=None):
        """Mean per-token NLL of text under the model, optional ablation."""
        handles = []
        try:
            if ablate:
                for l, Q in ablate.items():
                    Qd = Q.to(self.device, torch.float32)
                    handles.append(self.layers[l].register_forward_hook(
                        self._ablate_hook(Qd)))
            enc = self.tok([text], return_tensors="pt").to(self.device)
            with torch.no_grad():
                out = self.model(**enc)
            logits = out.logits[0, :-1]
            targets = enc["input_ids"][0, 1:]
            return float(F.cross_entropy(logits, targets).item())
        finally:
            for h in handles:
                h.remove()


def save_json(name, obj):
    path = os.path.join(RESULTS_DIR, name)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    print(f"saved {path}")

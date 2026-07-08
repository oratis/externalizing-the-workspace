"""Concept vocabulary for lens vectors, filtered to single-token words."""

CONCEPTS = {
    "sports": ["soccer", "basketball", "tennis", "golf", "baseball", "hockey",
               "cricket", "rugby", "boxing", "swimming"],
    "animals": ["dog", "cat", "lion", "tiger", "eagle", "shark", "spider",
                "elephant", "horse", "snake", "penguin", "rabbit"],
    "colors": ["red", "blue", "green", "yellow", "purple", "orange", "white"],
    "countries": ["France", "China", "Japan", "Brazil", "Egypt", "Canada",
                  "Italy", "Germany"],
    "fruits": ["apple", "banana", "lemon", "mango", "cherry", "grape"],
    "misc": ["violin", "gold", "milk", "Jupiter", "Shakespeare", "Rome",
             "piano", "coffee", "winter", "ocean"],
}


def single_token_id(tok, word):
    """Token id of ' word' if it is a single token, else None."""
    ids = tok.encode(" " + word, add_special_tokens=False)
    return ids[0] if len(ids) == 1 else None


def build_concept_table(tok):
    """Returns (words, ids, category_of) for all single-token concepts."""
    words, ids, cat_of = [], [], {}
    for cat, ws in CONCEPTS.items():
        for w in ws:
            tid = single_token_id(tok, w)
            if tid is not None:
                words.append(w)
                ids.append(tid)
                cat_of[w] = cat
    return words, ids, cat_of

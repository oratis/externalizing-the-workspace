// Seed each arm's isolated LISA_HOME from a single common founding snapshot,
// so all arms start from an IDENTICAL real identity and any divergence is the
// arm's doing. Founding snapshot = the deployed soul at ~/.lisa (or $SEED_HOME).
//
// Usage: node seed-arms.mjs [--force]
//   creates research/longitudinal/runs/<arm>/{soul,config.env,memory}
//   snapshots the founding soul to runs/founding-soul/ for drift baselines.

import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";

const HERE = path.dirname(new URL(import.meta.url).pathname);
// COHORT unset/"main" → flat runs/ (the original cohort); "c1" → runs/c1/ etc.
const COHORT = process.env.COHORT && process.env.COHORT !== "main" ? process.env.COHORT : "";
const RUNS = COHORT ? path.join(HERE, "runs", COHORT) : path.join(HERE, "runs");
const SEED_HOME = process.env.SEED_HOME || path.join(os.homedir(), ".lisa");
const FORCE = process.argv.includes("--force");
const ARMS = JSON.parse(await fs.readFile(path.join(HERE, "arms.json"), "utf8")).arms;

async function exists(p) { try { await fs.access(p); return true; } catch { return false; } }

async function copyDir(src, dst) {
  await fs.mkdir(dst, { recursive: true });
  for (const e of await fs.readdir(src, { withFileTypes: true })) {
    const s = path.join(src, e.name), d = path.join(dst, e.name);
    if (e.isDirectory()) await copyDir(s, d);
    else if (e.isFile()) await fs.copyFile(s, d);
  }
}

const soulSrc = path.join(SEED_HOME, "soul");
if (!(await exists(path.join(soulSrc, "seed.json")))) {
  console.error(`No born soul at ${soulSrc}. Run \`lisa birth\` first (or set SEED_HOME).`);
  process.exit(1);
}

// Founding baseline snapshot (immutable reference for B1 drift).
const founding = path.join(RUNS, "founding-soul");
if (!(await exists(founding)) || FORCE) {
  await fs.rm(founding, { recursive: true, force: true });
  await copyDir(soulSrc, founding);
  console.log(`founding snapshot -> ${path.relative(HERE, founding)}`);
}

const cfgSrc = path.join(SEED_HOME, "config.env");
const haveCfg = await exists(cfgSrc);

for (const arm of Object.keys(ARMS)) {
  const home = path.join(RUNS, arm);
  const armSoul = path.join(home, "soul");
  if ((await exists(armSoul)) && !FORCE) {
    console.log(`arm ${arm}: exists, skip (use --force to reseed)`);
    continue;
  }
  await fs.rm(home, { recursive: true, force: true });
  await fs.mkdir(home, { recursive: true });
  await copyDir(soulSrc, armSoul);
  // fresh soul.lock, drop any stale lock from the snapshot
  await fs.rm(path.join(armSoul, "soul.lock.json"), { force: true });
  if (haveCfg) await fs.copyFile(cfgSrc, path.join(home, "config.env"));
  await fs.mkdir(path.join(home, "memory"), { recursive: true });
  console.log(`arm ${arm}: seeded ${path.relative(HERE, home)}` +
    (haveCfg ? " (+config.env)" : " (NO config.env — set keys manually)"));
}

// day counter starts at 0
const statePath = path.join(RUNS, "state.json");
if (!(await exists(statePath)) || FORCE) {
  await fs.writeFile(statePath, JSON.stringify({ nextDay: 0 }, null, 1));
  console.log("state.json: nextDay=0");
}
console.log("seed complete.");

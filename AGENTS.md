# Kural

> Local-first voice typing + voice control for Windows. English and Tamil. GPU-accelerated Whisper, no cloud.

---

## Role

You are a senior Python engineer (Windows desktop, audio, speech recognition) working with Mohamed Aashir S on **Kural**, a merge of two MIT-licensed projects:

- **Base:** `drajb/whisper-local` (fork of Pin Wang's `whisper-key-local`) — the GPU speech engine, onboarding, diagnostics, settings.
- **Donor:** `ROHITCRAFTSYT/WhispLocal` — the voice-control engine (app index, fuzzy command matching, guardrails), adaptive learning, recovery features.

Target machine: Windows 11, NVIDIA RTX 3050 6 GB, 16 GB RAM. Languages: English and Tamil.

Priorities, in order: correctness and privacy → dictation latency on the GPU → voice-control reliability → polish.

Rules of engagement:
- Read the relevant module in BOTH source repos before writing a new one. Port and adapt; do not rewrite from memory.
- Never add a runtime network call. The only allowed network use is the one-time model download.
- If a claim in this file is marked **(verify)**, confirm it in the code before building on it.

---

## Project context

### What each source repo gives us

**drajb/whisper-local (base)**

| Pros | Cons / gaps |
|---|---|
| CUDA/float16 path with onboarding that installs the CUDA libraries; `doctor.py` checks them | Voice commands are marked experimental |
| Models include `large-v3-turbo` and `distil-large-v3.5`; setup wizard recommends Turbo for GPUs | Command matching is plain substring, first match wins, no fuzzy or misheard-word recovery |
| Tamil is in the dictation language list | No app index: every "open X" must be hand-written in `commands.yaml` |
| `commands.yaml` actions: `run`, `hotkey`, `type`, `rephrase` (Ollama), macros with `then:` and `delay:` | Command mode needs a separate hotkey plus a stop key |
| Settings UI, history window, stats, snippets, dictionary, app rules/styles, streaming, noise suppression, local OpenAI-compatible server | Large module count; some features may overlap with the donor (**verify** before porting anything) |
| Packaging dirs, tests, self-test, CI-style tooling | No Tamil trigger phrases or Tamil command aliases |

**ROHITCRAFTSYT/WhispLocal (donor)**

| Pros | Cons / gaps |
|---|---|
| Rich voice control: open/close/switch apps, web fallback, window management, media/volume, pointer, screenshot, lock, notes to Obsidian | `transcriber.py` hardcodes `device="cpu", compute_type="int8"`, so the RTX 3050 is never used |
| Indexes Start Menu shortcuts and Store apps; fuzzy app matching; second-pass fix of misheard leading verb ("oben chrome") | Practical models are tiny/base/small on CPU; weak for Tamil |
| `GUARDRAILS.md`: never deletes files, never purchases or books, graceful close only | Command parser assumes English verbs and phrasing |
| Adaptive vocabulary/corrections, voice editing, never-lose-a-dictation (paste last, retry last, DPAPI-encrypted take), config validation | 1 star, no releases; source install needs Python 3.11/3.12 |
| Native-script Indic prompting and optional Roman-script output | Windows-only; elevated (admin) windows ignore injected input |
| Mocked tests and CI that need no mic, model or network | Clipboard-based insertion by default |

### Gaps in both (the reason Kural exists)

1. **No project combines GPU Turbo with rich voice control.** Base has the GPU, donor has the control engine.
2. **Tamil voice commands are unsupported.** Matching in both is English-phrased. Need Tamil and Tanglish aliases ("திற chrome", "open chrome பண்ணு").
3. **Tanglish (mixed Tamil-English) accuracy is unmeasured.** No test set exists in either repo.
4. **No EN/TA benchmark harness** comparing Turbo, Large v3, distil and Q5 variants on the RTX 3050 (speed and WER).
5. **Neither appears to offer hands-free activation** (wake word or always-listening mode). Both are hotkey-driven (**verify**).
6. **Safety models differ.** Base runs any shell string from user YAML; donor has fixed guardrails. Kural needs one consistent policy.
7. **GPU memory is shared.** Nothing unloads the model after idle, so other GPU apps on a 6 GB card can run out of VRAM.
8. **Two packaging approaches** (base: pyapp/packaging; donor: PyInstaller). Pick one.
9. **Elevated windows** ignore injected keystrokes. Needs a clear user-facing message, not a silent failure.

### Licensing

Both sources are MIT. Keep all upstream copyright lines (Pin Wang, Rohit Burani, ROHITCRAFTSYT) in `LICENSE` and `THIRD_PARTY_NOTICES.md`. Note the origin of every ported file in its header comment.

---

## Architecture decisions

- **Base = `drajb/whisper-local`, imported by copy.** `main` starts as a bare skeleton, so the upstream code arrives in the first PR (`chore/import-base-engine`), not as a git fork. Record the upstream commit SHA in `THIRD_PARTY_NOTICES.md`. Rename the package to `kural`. Keep its engine, onboarding, doctor, settings, packaging.
- **Port from donor, as a `kural/control/` package:** command parser, app index (Start Menu + Store), fuzzy/second-pass matching, volume/media, window ops, guardrails. Adapt to base's `commands.yaml` so user-defined commands still work.
- **Command resolution order:** user `commands.yaml` exact → built-in commands → fuzzy app match → (optional, later) local-LLM intent fallback → "not understood" feedback. Never guess a destructive action.
- **Engine:** faster-whisper on CUDA, `float16`, default model `large-v3-turbo`. CPU `int8` fallback with a visible warning. Unload the model after a configurable idle time.
- **Language:** set manually (`en` / `ta`), no auto-detect by default. Native Tamil script output; Roman option kept from donor.
- **Text pipeline stays deterministic** (no LLM touches dictated words). LLM use is opt-in and only for rephrase/intent fallback.
- **Config:** `%APPDATA%\kural\`. Validate every key on load; a bad value falls back to its default and logs a warning (port donor's `configcheck.py`).
- **Privacy:** no telemetry. Transcripts are not logged at INFO. Retained audio only DPAPI-encrypted, one take, short expiry, off in Incognito.

### Roadmap

| Milestone | Outcome | Done when |
|---|---|---|
| M0 | Import base, rename, upstream tests green | `pytest` passes on Windows 11 (PRs: `chore/import-base-engine`, `refactor/rename-to-kural`) |
| M1 | GPU Turbo for EN + TA, benchmark harness | Report: latency and WER for Turbo / Large v3 / distil / Q5 on RTX 3050 |
| M2 | Voice-control engine ported | Open/close/switch/media/window commands work with fuzzy match and guardrails |
| M3 | Tamil + Tanglish command aliases and test set | Tamil triggers pass an agreed accuracy bar on recorded samples |
| M4 | One installer, idle VRAM unload, elevated-window message | Fresh Windows 11 install works end to end |
| M5 (optional) | Local-LLM intent fallback, wake word | Behind a setting, off by default |

---

## Code standards

- Python 3.12, type hints on all public functions, `ruff` clean, `pytest` for everything.
- Small modules, one responsibility each. No new module over ~300 lines without a reason.
- **Tests must not need a mic, GPU, model or network.** Mock audio devices and faster-whisper (the donor's test suite is the pattern to follow). GPU behaviour gets a separate marked test run on the real machine.
- Every ported file: keep the upstream license header, add a one-line "ported from <repo>/<path>" comment, and cover it with a test before changing its behaviour.
- Voice-control actions are an allowlist. No file deletion, purchases, payments or bookings by voice. Shutdown, restart and sign-out need a confirmation step and a cancel window.
- Errors reach the user as a plain sentence in the UI and a full traceback in `kural.log` (rotating, 1 MB x 3).
- Never swallow exceptions in the audio or transcription threads; log and surface them.
- Do not commit models, recordings, history files or `config.json`.
- Commit and branch rules are in **Git workflow** below. They apply to every change, including docs and config.

---

## Git workflow

`main` holds only the simple folder structure and default files. All real work lands through pull requests that the user merges. Claude never merges.

**Per task (one feature, function or requirement = one branch = one PR):**

1. Make sure local `main` is up to date: `git checkout main && git pull`.
2. Create a branch from `main` named for the work, as `<type>/<short-kebab-name>`:
   - Types: `feat`, `fix`, `port`, `test`, `docs`, `chore`, `refactor`.
   - Examples: `chore/import-base-engine`, `feat/gpu-turbo-engine`, `port/app-index`, `feat/tamil-command-aliases`, `test/benchmark-harness`.
3. Build the change in small steps. **Every change is committed**, however small, and nothing is left uncommitted when a session or task ends (`git status` must be clean).
4. Verify before opening the PR (all of these, in order):
   - `ruff check .` and `ruff format --check .` pass.
   - `pytest` passes, with new or changed behaviour covered by new tests.
   - Run the feature itself where it can be run (CLI, `--doctor`, self-test, or a manual check on the real machine for GPU/mic/hotkey work) and note what was run.
   - Review your own diff: no stray files, no secrets, license headers present on ported code.
5. Push the branch and open a PR into `main`.
6. **Stop and wait.** The user reviews and merges. Do not start the next task on top of an unmerged branch.
7. After the user confirms the merge: `git checkout main && git pull`, delete the merged local branch, then start the next task from step 2.

**Commits:**

- Conventional commit subjects: `feat:`, `fix:`, `port:`, `test:`, `docs:`, `chore:`, `refactor:`. Imperative mood, subject under 72 characters, body explains *why* when it is not obvious.
- One logical change per commit. Tests go in the same commit as the code they cover, or in the commit just before it.
- **No `Co-Authored-By` trailer, no `Claude-Session` line, no "Generated with" line, and no other attribution lines in any commit message.** Commits carry only the user's configured git identity. Do not edit `git config`.
- Never commit to `main` directly, force-push `main`, or rewrite history that is already pushed. Do not use `--no-verify` to skip hooks.

**Pull requests:**

- Title follows the commit style. Description has: **Summary** (what and why), **Changes** (bullets), **Verification** (the exact commands run and their result), **Notes** (known gaps, follow-ups, anything marked verify).
- Keep PRs small enough to review in one sitting. If a task grows past that, split it into several branches and PRs and say so.

---

## Skills

Use these custom skills at the right moment:

| Skill | When |
|---|---|
| `/architect` | Before building anything non-trivial with no plan yet (M2 control engine, M3 Tamil matching, VRAM unload). Output: a short design with module boundaries and test plan. |
| `/review` | When a feature is done. Production check: privacy, guardrails, threading, error paths, test coverage, license headers on ported code. |
| `/recover` | When something is broken and the fix isn't obvious (CUDA load hangs, hotkeys not firing, text not arriving, model won't load). Diagnose from `kural.log` and `doctor` output before changing code. |
| `/remember` | Session start: restore context from `SESSION.md`. Session end: save progress there. |

---

## Session continuity

- Each milestone is delivered as several small PRs, one per feature or requirement (see **Git workflow**). After opening a PR, stop and wait for the user to merge it before starting the next.
- Keep `SESSION.md` at the repo root. It holds: current milestone, current branch and PR link, last completed step, next step, open questions, and any **(verify)** items resolved or still open. Update it in a commit on the same branch as the work it describes.
- At session start run `/remember`, read `SESSION.md`, then state the current milestone and next step in two lines before doing anything.
- At session end run `/remember` to update `SESSION.md`. Record decisions with a one-line reason.
- When a **(verify)** item is checked, update this file with the result so it is not checked twice.
- Do not rely on chat history. Anything that matters goes in `SESSION.md` or this file.

# Progress log

One entry per milestone and test session, newest last. Forward-looking notes live here, not in code comments.

## 2026-10-06: M0, tooling and safety

Done:

- `tools/tools.lock.json` pins MBINCompiler v7.04.1-pre3 (with release hashes), hgpaktool 1.1.3, lz4, zstandard, pytest, and game build 180836 (Steam buildid 25732212). `tools/bootstrap.ps1` fetches and verifies them.
- `tools/testmode.py` (enter, exit, status, resolve) with 35 tests on a fake game tree, including a real fake `NMS.exe` process. Machine paths live in the gitignored `scratch/testmode.local.json`; tests refuse to build the real environment.
- `tools/extract.py`, `tools/check_build.py`, `tools/save_inspect.py`, `tools/merge_preview.py`, and the shared `tools/nmsenv.py` (game discovery through Steam's library list, running-game check).
- Verified from a fresh clone: bootstrap, extract, check_build and all 73 tests pass.

Findings:

- **Globals sit at the pak root** (`gcbuildingglobals.global.mbin`), not under `GLOBALS/`. gBase Boundary ships `GLOBALS/GCBUILDINGGLOBALS.GLOBAL.EXML`, so it may not load at all on this build. Our patches use the pak path; P4 confirms it.
- **Patch semantics seen in installed mods:** `_id` matches or appends, `_index` matches, keyless list items append, `_overwrite="true"` replaces a list. `merge_preview.py` models this, and installed mods' table patches merge and compile under it.
- **Custom text:** three installed mods ship a `LocTable.MXML` (template `cTkLocalisationTable`) at the mod root. P3 tries that convention.
- `GCMODSETTINGS.MXML` has a BOM, CRLF line endings and no trailing newline. `testmode` round-trips the real file byte for byte.
- NMS.py's latest release (180383.0) is still one build behind the game.
- Save slots 1 to 5 are in use, so a new creative game should land in slot 6 (`save11.hg`, `save12.hg`). `testmode exit` learns the slot the first time it appears.

Open for later:

- `save_inspect.py` matches bases to settlements by address. The settlement address format is assumed and must be checked against the first real test-slot copy.

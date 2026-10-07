"""The only way into and out of an in-game test session.

enter: back up saves and settings, install dev modules as _OTDEV_* folders,
       and point the game's mod list at them.
exit:  remove the dev folders, restore the mod list byte for byte, and prove
       that nothing outside the test slot changed.
status: report whether a session is open and how the last one ended.

Every command refuses while the game runs. Backups are never deleted.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from nmsenv import game_running

REPO_ROOT = Path(__file__).resolve().parent.parent

# Module key -> source folder under mod/.
MODULES = {
    "core": "OverseersToolkit",
    "open": "OverseersToolkit-OpenSettlements",
    "defense": "OverseersToolkit-Defense",
    "testtuning": "OverseersToolkit-TestTuning",
    "probes": "OverseersToolkit-Probes",
    "decor": "OverseersToolkit-SettlementDecor",
}
DEV_PREFIX = "_OTDEV_"
# The game writes its merged mod data here when the test-only debug flag is on.
EXPORT_DIR = "EXPORTED"
FIRST_FREE_SLOT = 6  # slots 1 to 5 hold real games and may never change

# Files in the profile folder the game rewrites on any load, whatever the slot.
ACCOUNT_FILES = {"accountdata.hg", "mf_accountdata.hg"}

SESSION_WARNING = """\
=====================================================================
 TEST SESSION OPEN
 Load the test slot from the LOAD menu. NEVER press Continue:
 Continue may open the main save while only test mods are active.
 When done: save, quit to desktop, then run `testmode.py exit`.
====================================================================="""


class Refused(Exception):
    """A precondition failed; nothing was changed."""


@dataclass(frozen=True)
class Env:
    game_root: Path
    save_root: Path
    profile: str
    backup_root: Path
    repo_root: Path
    process_name: str = "NMS.exe"

    @property
    def mods_dir(self):
        return Path(self.game_root) / "GAMEDATA" / "MODS"

    @property
    def settings_dir(self):
        return Path(self.game_root) / "Binaries" / "SETTINGS"

    @property
    def gcmodsettings(self):
        return self.settings_dir / "GCMODSETTINGS.MXML"

    @property
    def scratch(self):
        return Path(self.repo_root) / "scratch"

    @property
    def state_file(self):
        return self.scratch / "testmode.state.json"

    @property
    def history_dir(self):
        return self.scratch / "testmode.history"

    @property
    def local_file(self):
        return self.scratch / "testmode.local.json"

    @property
    def saves_copy_dir(self):
        return self.scratch / "saves"


@dataclass
class EnterResult:
    backup_dir: str
    dev_folders: list


@dataclass
class ExitResult:
    ok: bool
    failures: list = field(default_factory=list)
    test_slot: int | None = None
    copied: list = field(default_factory=list)


@dataclass
class Status:
    open: bool
    ok: bool
    problems: list = field(default_factory=list)
    detail: dict = field(default_factory=dict)


# --- environment -------------------------------------------------------------


def real_env():
    """Build the environment for this PC from scratch/testmode.local.json."""
    if "PYTEST_CURRENT_TEST" in os.environ:
        raise RuntimeError("tests must never build the real environment")
    local = REPO_ROOT / "scratch" / "testmode.local.json"
    if not local.is_file():
        raise Refused(
            f"{local} is missing. Create it with game_root, save_root, profile and backup_root."
        )
    cfg = json.loads(local.read_text(encoding="utf-8"))
    missing = [k for k in ("game_root", "save_root", "profile", "backup_root") if not cfg.get(k)]
    if missing:
        raise Refused(f"{local} lacks {', '.join(missing)}")
    return Env(
        game_root=Path(cfg["game_root"]),
        save_root=Path(cfg["save_root"]),
        profile=cfg["profile"],
        backup_root=Path(cfg["backup_root"]),
        repo_root=REPO_ROOT,
    )


def refuse_if_game_running(env):
    try:
        running = game_running(env.process_name)
    except RuntimeError as e:
        raise Refused(f"{e}; assuming the game runs") from e
    if running:
        raise Refused(f"{env.process_name} is running. Quit the game first.")


# --- hashing and listings ----------------------------------------------------


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def files_under(root):
    """Relative POSIX paths of every regular file under root. Refuses links rather than skip them."""
    root = Path(root)
    files, links = [], []
    for p in root.rglob("*"):
        if p.is_symlink() or p.is_junction():
            links.append(str(p))
        elif p.is_file():
            files.append(p.relative_to(root).as_posix())
    if links:
        raise Refused(f"links are not supported here, so they cannot be verified: {', '.join(sorted(links))}")
    return sorted(files)


def is_dev_path(rel):
    return rel.split("/", 1)[0].upper().startswith(DEV_PREFIX)


def mods_listing(mods_dir, skip_export=False):
    """Size and sha256 of everything in MODS except our dev folders (and a session-owned export)."""
    listing = {}
    for rel in files_under(mods_dir):
        if skip_export and rel.split("/", 1)[0].upper() == EXPORT_DIR:
            continue
        if not is_dev_path(rel):
            path = Path(mods_dir) / rel
            listing[rel] = [path.stat().st_size, sha256_file(path)]
    return listing


# --- save slots --------------------------------------------------------------

SAVE_RE = re.compile(r"^(?:mf_)?save(\d*)\.hg$", re.IGNORECASE)


def slot_of(name):
    """Slot number for a save file name; save.hg counts as save1."""
    m = SAVE_RE.match(name)
    if not m:
        return None
    k = int(m.group(1) or 1)
    return (k + 1) // 2


def slot_files(slot):
    first = "save.hg" if slot == 1 else f"save{2 * slot - 1}.hg"
    second = f"save{2 * slot}.hg"
    return [first, second, "mf_" + first, "mf_" + second]


# --- GCMODSETTINGS -----------------------------------------------------------


def _serialize(elem, depth, nl):
    pad = "\t" * depth
    attrs = "".join(f' {k}="{_escape(v)}"' for k, v in elem.attrib.items())
    if len(elem) == 0:
        return f"{pad}<{elem.tag}{attrs} />{nl}"
    inner = "".join(_serialize(child, depth + 1, nl) for child in elem)
    return f"{pad}<{elem.tag}{attrs}>{nl}{inner}{pad}</{elem.tag}>{nl}"


def _escape(value):
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _mod_infos(root):
    data = root.find("Property[@name='Data']")
    if data is None:
        raise Refused("GCMODSETTINGS.MXML has no Data list; refusing to edit an unknown format")
    return data


def _field(info, name):
    node = info.find(f"Property[@name='{name}']")
    if node is None:
        raise Refused(f"GCMODSETTINGS entry lacks {name}; refusing to edit an unknown format")
    return node


def rewrite_mod_settings(original, dev_names, keep_user_mods):
    """Return GCMODSETTINGS bytes with dev mods enabled and, unless kept, user mods disabled."""
    bom = original.startswith(b"\xef\xbb\xbf")
    text = original.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in text else "\n"
    trailing = text.endswith(("\n", "\r\n"))
    root = ET.fromstring(text)
    if root.tag != "Data" or root.get("template") != "GcModSettings":
        raise Refused("GCMODSETTINGS.MXML is not a GcModSettings file")
    data = _mod_infos(root)

    wanted = [n.upper() for n in dev_names]
    present = set()
    priorities = []
    for info in data:
        name = _field(info, "Name").get("value", "")
        priorities.append(int(_field(info, "ModPriority").get("value", "0")))
        is_dev = name.upper().startswith(DEV_PREFIX)
        if is_dev and name.upper() in wanted:
            on = "true"
            present.add(name.upper())
        elif is_dev or not keep_user_mods:
            on = "false"
        else:
            continue
        _field(info, "Enabled").set("value", on)
        _field(info, "EnabledVR").set("value", on)

    next_priority = max(priorities, default=-1) + 1
    next_index = len(data)
    for name in wanted:
        if name in present:
            continue
        info = ET.SubElement(
            data, "Property", {"name": "Data", "value": "GcModSettingsInfo", "_index": str(next_index)}
        )
        for key, value in (
            ("Name", name),
            ("Author", ""),
            ("ID", "0"),
            ("AuthorID", "0"),
            ("LastUpdated", "0"),
            ("ModPriority", str(next_priority)),
            ("Enabled", "true"),
            ("EnabledVR", "true"),
        ):
            ET.SubElement(info, "Property", {"name": key, "value": value})
        ET.SubElement(info, "Property", {"name": "Dependencies"})
        next_index += 1
        next_priority += 1

    body = f'<?xml version="1.0" encoding="utf-8"?>{nl}' + _serialize(root, 0, nl)
    if not trailing:
        body = body[: -len(nl)]
    return (b"\xef\xbb\xbf" if bom else b"") + body.encode("utf-8")


# --- backup ------------------------------------------------------------------


def _now():
    return datetime.now()


def _new_backup_dir(env):
    """A backup folder that did not exist before; never reuses or overwrites an older one."""
    base = _now().strftime("%Y%m%d-%H%M%S")
    for n in range(100):
        stamp = base if n == 0 else f"{base}-{n}"
        path = Path(env.backup_root) / stamp
        try:
            path.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            continue
        return stamp, path
    raise Refused(f"no free backup folder name under {env.backup_root}")


def make_backup(env):
    """Copy the save folder and SETTINGS, write a manifest, and verify every copy."""
    stamp, backup = _new_backup_dir(env)
    manifest = {}
    for label, src_root in (("saves", Path(env.save_root)), ("SETTINGS", env.settings_dir)):
        for rel in files_under(src_root):
            src = src_root / rel
            dst = backup / label / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            src_hash = sha256_file(src)
            shutil.copy2(src, dst)
            if sha256_file(dst) != src_hash:
                raise Refused(f"backup copy of {src} does not match its source")
            manifest[f"{label}/{rel}"] = src_hash
    (backup / "manifest.json").write_text(
        json.dumps({"created": stamp, "files": manifest}, indent=1), encoding="utf-8"
    )
    for rel, digest in manifest.items():
        if sha256_file(backup / rel) != digest:
            raise Refused(f"backup verification failed for {rel}")
    return stamp, backup, manifest


# --- state -------------------------------------------------------------------


def read_json(path, default=None):
    path = Path(path)
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def known_test_slot(env):
    return (read_json(env.local_file, {}) or {}).get("test_slot")


def dev_folders_present(env):
    if not env.mods_dir.is_dir():
        return []
    return sorted(p.name for p in env.mods_dir.iterdir() if p.name.upper().startswith(DEV_PREFIX))


# --- enter -------------------------------------------------------------------


def enter(env, modules, with_user_mods=False):
    refuse_if_game_running(env)
    state = read_json(env.state_file)
    if state is not None:
        raise Refused(f"a session is already {state.get('status', 'open')}: {env.state_file}")
    unknown = [m for m in modules if m not in MODULES]
    if unknown:
        raise Refused(f"unknown module(s): {', '.join(unknown)}; known: {', '.join(MODULES)}")
    if not modules:
        raise Refused("no modules requested")
    sources = {m: Path(env.repo_root) / "mod" / MODULES[m] for m in modules}
    missing = [str(p) for p in sources.values() if not p.is_dir()]
    if missing:
        raise Refused(f"module source missing: {', '.join(missing)}")
    stale = dev_folders_present(env)
    if stale:
        raise Refused(f"dev folders already in MODS without an open session: {', '.join(stale)}")
    if not env.gcmodsettings.is_file():
        raise Refused(f"{env.gcmodsettings} not found")
    original_settings = env.gcmodsettings.read_bytes()
    dev_names = [DEV_PREFIX + m.upper() for m in modules]
    new_settings = rewrite_mod_settings(original_settings, dev_names, keep_user_mods=with_user_mods)

    # Listing first: it refuses links before any backup folder exists.
    files_under(env.save_root)
    files_under(env.settings_dir)
    listing = mods_listing(env.mods_dir)
    stamp, backup, manifest = make_backup(env)
    write_json(backup / "mods_listing.json", listing)

    state = {
        "status": "open",
        "opened": stamp,
        "backup_dir": str(backup),
        "modules": list(modules),
        "with_user_mods": with_user_mods,
        "dev_folders": dev_names,
        "test_slot": known_test_slot(env),
        # Only an export folder the game creates during the session is ours to move out.
        "export_owned": not (env.mods_dir / EXPORT_DIR).exists(),
    }
    # Record the session before touching the game, so a crash mid-way still leaves exit able to clean up.
    write_json(env.state_file, state)

    for module, name in zip(modules, dev_names):
        shutil.copytree(sources[module], env.mods_dir / name)
    env.gcmodsettings.write_bytes(new_settings)
    return EnterResult(backup_dir=str(backup), dev_folders=dev_names)


# --- exit --------------------------------------------------------------------


def _remove_dev_folders(env, failures):
    for name in dev_folders_present(env):
        path = env.mods_dir / name
        if path.is_symlink() or path.is_junction() or not path.is_dir():
            failures.append(f"MODS/{name} is not a plain folder; left in place")
            continue
        shutil.rmtree(path)


def _move_export_out(env, opened, failures):
    """Keep the game's merged-data export for inspection, then take it out of MODS."""
    export = env.mods_dir / EXPORT_DIR
    if not export.exists():
        return
    if export.is_symlink() or export.is_junction() or not export.is_dir():
        failures.append(f"MODS/{EXPORT_DIR} is not a plain folder; left in place")
        return
    files_under(export)  # refuses links inside it
    target = env.scratch / "exported" / opened
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(export, target)
    shutil.rmtree(export)


def _compare_saves(env, manifest, test_slot):
    """Return (failures, changed slot numbers) for the save folder versus the backup."""
    before = {k[len("saves/"):]: v for k, v in manifest.items() if k.startswith("saves/")}
    now = {rel: sha256_file(Path(env.save_root) / rel) for rel in files_under(env.save_root)}
    changed = sorted(
        rel for rel in set(before) | set(now) if before.get(rel) != now.get(rel)
    )
    failures = []
    slot_changes = {}
    for rel in changed:
        parts = rel.split("/")
        kind = "deleted" if rel not in now else "new" if rel not in before else "changed"
        if parts[0] == env.profile and len(parts) >= 2 and parts[1].lower() == "cache":
            continue
        if parts[0] == env.profile and len(parts) == 2:
            name = parts[1]
            if name.lower() in ACCOUNT_FILES and kind != "deleted":
                continue
            slot = slot_of(name)
            # A tester may delete the known test slot to start a fresh game there.
            if slot is not None and (kind != "deleted" or slot == test_slot):
                slot_changes.setdefault(slot, []).append(rel)
                continue
        failures.append(f"save folder: {rel} was {kind}")

    learned = None
    if test_slot is not None:
        for slot, rels in slot_changes.items():
            if slot != test_slot:
                failures.extend(f"save folder: {rel} changed outside test slot {test_slot}" for rel in rels)
    else:
        low = {s: r for s, r in slot_changes.items() if s < FIRST_FREE_SLOT}
        for rels in low.values():
            failures.extend(f"save folder: {rel} changed in a protected slot" for rel in rels)
        high = sorted(s for s in slot_changes if s >= FIRST_FREE_SLOT)
        if len(high) > 1:
            failures.append(f"save folder: several new slots changed ({high}); cannot tell which is the test slot")
        elif len(high) == 1 and not failures:
            learned = high[0]
    return failures, learned


def _verified_backup(backup):
    """Everything exit needs from the backup, checked before exit changes anything."""
    manifest_doc = read_json(backup / "manifest.json")
    if manifest_doc is None:
        raise Refused(f"backup manifest missing at {backup}; nothing was changed")
    manifest = manifest_doc["files"]
    settings = backup / "SETTINGS" / "GCMODSETTINGS.MXML"
    want = manifest.get("SETTINGS/GCMODSETTINGS.MXML")
    if want is None or not settings.is_file() or sha256_file(settings) != want:
        raise Refused(f"backup GCMODSETTINGS.MXML at {settings} is missing or damaged; nothing was changed")
    listing = read_json(backup / "mods_listing.json")
    if listing is None:
        raise Refused(f"backup mods_listing.json missing at {backup}; nothing was changed")
    return manifest, settings, listing


def exit_session(env):
    refuse_if_game_running(env)
    state = read_json(env.state_file)
    if state is None:
        raise Refused("no test session is open")
    if state.get("status") != "open":
        raise Refused(f"session status is {state.get('status')}; resolve it with Ethan first")
    backup = Path(state["backup_dir"])
    manifest, settings_backup, before = _verified_backup(backup)
    failures = []

    # Put the game back first, then check what happened. The mod list goes back before the
    # dev folders go, so a failure part-way never leaves the user's own mods switched off.
    errors = []
    try:
        shutil.copy2(settings_backup, env.gcmodsettings)
    except OSError as e:
        errors.append(f"restoring GCMODSETTINGS.MXML failed: {e}")
    try:
        _remove_dev_folders(env, failures)
    except OSError as e:
        errors.append(f"removing dev folders failed: {e}")
    if state.get("export_owned"):
        try:
            _move_export_out(env, state["opened"], failures)
        except OSError as e:
            errors.append(f"moving the game's export out of MODS failed: {e}")
    if errors:
        state["exit_error"] = "; ".join(errors)
        write_json(env.state_file, state)
        raise Refused(state["exit_error"] + "; fix the cause and run exit again")
    state.pop("exit_error", None)
    if sha256_file(env.gcmodsettings) != manifest["SETTINGS/GCMODSETTINGS.MXML"]:
        failures.append("GCMODSETTINGS.MXML does not match its backup after restore")

    after = mods_listing(env.mods_dir, skip_export=state.get("export_owned", False))
    for rel in sorted(set(before) | set(after)):
        if rel not in after:
            failures.append(f"MODS: {rel} disappeared")
        elif rel not in before:
            failures.append(f"MODS: {rel} appeared")
        elif before[rel] != after[rel]:
            failures.append(f"MODS: {rel} changed")

    test_slot = state.get("test_slot")
    save_failures, learned = _compare_saves(env, manifest, test_slot)
    failures.extend(save_failures)
    if learned is not None:
        test_slot = learned
        local = read_json(env.local_file, {}) or {}
        local["test_slot"] = learned
        write_json(env.local_file, local)

    copied = []
    if test_slot is not None and not failures:
        profile = Path(env.save_root) / env.profile
        env.saves_copy_dir.mkdir(parents=True, exist_ok=True)
        for name in slot_files(test_slot):
            if (profile / name).is_file():
                shutil.copy2(profile / name, env.saves_copy_dir / name)
                copied.append(name)

    closed = _now().strftime("%Y%m%d-%H%M%S")
    record = dict(state, closed=closed, test_slot=test_slot, failures=failures, copied=copied)
    if failures:
        record["status"] = "failed"
        write_json(env.state_file, record)
    else:
        record["status"] = "closed"
        write_json(env.history_dir / f"{state['opened']}.json", record)
        env.state_file.unlink()
    return ExitResult(ok=not failures, failures=failures, test_slot=test_slot, copied=copied)


# --- status ------------------------------------------------------------------


def last_closed(env):
    if not env.history_dir.is_dir():
        return None
    records = sorted(env.history_dir.glob("*.json"))
    return read_json(records[-1]) if records else None


def status(env):
    problems = []
    state = read_json(env.state_file)
    if state is not None and state.get("status") == "failed":
        problems.append("the last session failed its safety checks:")
        problems.extend("  " + f for f in state.get("failures", []))
        return Status(open=False, ok=False, problems=problems, detail=state)
    if state is not None:
        if state.get("exit_error"):
            problems.append(f"exit stopped part-way: {state['exit_error']}")
        return Status(open=True, ok=not problems, problems=problems, detail=state)
    stale = dev_folders_present(env)
    if stale:
        problems.append(f"dev folders in MODS without an open session: {', '.join(stale)}")
    return Status(open=False, ok=not problems, problems=problems, detail=last_closed(env) or {})


def resolve(env, note):
    """Archive a failed session after Ethan has reviewed it. Never touches game or save files."""
    state = read_json(env.state_file)
    if state is None or state.get("status") != "failed":
        raise Refused("there is no failed session to resolve")
    state["status"] = "resolved"
    state["resolution"] = note
    write_json(env.history_dir / f"{state['opened']}.json", state)
    env.state_file.unlink()


# --- CLI ---------------------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_enter = sub.add_parser("enter")
    p_enter.add_argument("--modules", default="core", help=f"comma list of: {', '.join(MODULES)}")
    p_enter.add_argument("--with-user-mods", action="store_true")
    sub.add_parser("exit")
    sub.add_parser("status")
    p_resolve = sub.add_parser("resolve", help="archive a failed session after Ethan approved")
    p_resolve.add_argument("--note", required=True)
    args = parser.parse_args(argv)

    try:
        env = real_env()
        if args.cmd == "enter":
            modules = [m.strip() for m in args.modules.split(",") if m.strip()]
            result = enter(env, modules, with_user_mods=args.with_user_mods)
            print(f"Backup: {result.backup_dir}")
            print(f"Installed: {', '.join(result.dev_folders)}")
            print(SESSION_WARNING)
            return 0
        if args.cmd == "exit":
            result = exit_session(env)
            if result.ok:
                print(f"Session closed. All safety checks passed. Test slot: {result.test_slot}")
                if result.copied:
                    print(f"Copied to {env.saves_copy_dir}: {', '.join(result.copied)}")
                return 0
            print("SAFETY CHECK FAILED. Stop and report these to Ethan:")
            for f in result.failures:
                print("  " + f)
            return 2
        if args.cmd == "status":
            st = status(env)
            try:
                running = "yes" if game_running(env.process_name) else "no"
            except RuntimeError as e:
                running = "unknown"
                st.ok = False
                st.problems.append(f"cannot tell whether the game runs: {e}")
            print("running: " + running)
            print("session: " + ("open" if st.open else "none open"))
            if st.open:
                print(f"  opened {st.detail.get('opened')}, modules {st.detail.get('modules')}")
            elif st.detail.get("closed"):
                print(f"  last session {st.detail.get('opened')} ended {st.detail.get('status')}")
            print("safety: " + ("ok" if st.ok else "PROBLEM"))
            for p in st.problems:
                print("  " + p)
            return 0 if st.ok and not st.open else 1
        if args.cmd == "resolve":
            resolve(env, args.note)
            print("Failed session archived.")
            return 0
    except Refused as e:
        print(f"Refused: {e}", file=sys.stderr)
        return 3
    return 1


if __name__ == "__main__":
    sys.exit(main())

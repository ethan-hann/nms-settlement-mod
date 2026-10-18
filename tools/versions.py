"""Per-module versions and the all-in-one bundle, checked against the last release.

versions.json at the repo root holds each shipped module's version and the bundle's
version and contents. Each module is a separate file on the Nexus page, and Vortex
offers an update only for the files a player installed, so a module's version moves
only when its own files change. The bundle carries the page version and moves when
anything in it does.

The last release is the newest vX.Y.Z tag. Releases before versions.json kept one
VERSION file for every module.

Usage: versions.py check      report version problems against the last release
       versions.py changed    list the modules whose version moved since the last release
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")
TAG_RE = re.compile(r"v(\d+\.\d+\.\d+)")


class VersionError(Exception):
    pass


def parse(version, owner):
    match = VERSION_RE.fullmatch(version) if isinstance(version, str) else None
    if not match:
        raise VersionError(f"{owner}: version {version!r} is not MAJOR.MINOR.PATCH")
    return tuple(int(n) for n in match.groups())


def _validate(data, owner):
    modules, bundle = data.get("modules"), data.get("bundle")
    if not isinstance(modules, dict) or not modules or not isinstance(bundle, dict):
        raise VersionError(f"{owner}: needs a modules map and a bundle")
    for name, version in modules.items():
        parse(version, name)
    parse(bundle.get("version"), "bundle")
    unknown = [m for m in bundle.get("modules", []) if m not in modules]
    if unknown:
        raise VersionError(f"bundle lists {', '.join(unknown)}, which have no version")
    return data


def load(path):
    path = Path(path)
    return _validate(json.loads(path.read_text(encoding="utf-8")), path.name)


def _git(repo, *args, check=True):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=check)


def last_release(repo):
    """(tag, released data) for the newest vX.Y.Z tag."""
    tags = [t for t in _git(repo, "tag", "--list", "v*").stdout.split() if TAG_RE.fullmatch(t)]
    if not tags:
        raise VersionError("no vX.Y.Z release tag")
    tag = max(tags, key=lambda t: parse(t[1:], t))
    shown = _git(repo, "show", f"{tag}:versions.json", check=False)
    if shown.returncode == 0:
        return tag, _validate(json.loads(shown.stdout), f"{tag}:versions.json")
    # Before versions.json, one VERSION covered every module, so it acts as a bundle of all of them.
    version = _git(repo, "show", f"{tag}:VERSION").stdout.strip()
    folders = _git(repo, "ls-tree", "--name-only", f"{tag}:mod").stdout.split()
    return tag, {"modules": {f: version for f in folders}, "bundle": {"version": version, "modules": folders}}


def _files_changed(repo, tag, module):
    path = f"mod/{module}"
    if _git(repo, "diff", "--quiet", tag, "--", path, check=False).returncode != 0:
        return True
    return bool(_git(repo, "ls-files", "--others", "--exclude-standard", "--", path).stdout.strip())


def _expect(name, version, released, moved):
    current, before = parse(version, name), parse(released, name)
    if moved and current <= before:
        return f"{name} changed since the last release but its version {version} is not above {released}"
    if not moved and current != before:
        return f"{name} is unchanged since the last release, so it keeps {released}, not {version}"
    return None


def check(data, repo):
    """Problems with data's versions against the last release; empty when they follow it."""
    tag, released = last_release(repo)
    problems = []
    for name, version in data["modules"].items():
        if name not in released["modules"]:
            continue
        problems.append(_expect(name, version, released["modules"][name], _files_changed(repo, tag, name)))
    bundle, old = data["bundle"], released["bundle"]
    now = {m: data["modules"][m] for m in bundle["modules"]}
    before = {m: released["modules"].get(m) for m in old["modules"]}
    problems.append(_expect("bundle", bundle["version"], old["version"], now != before))
    return [p for p in problems if p]


def changed(data, repo):
    """Modules to upload: new ones and ones whose version moved since the last release."""
    _, released = last_release(repo)
    return [n for n, v in data["modules"].items() if released["modules"].get(n) != v]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("check", "changed"))
    args = parser.parse_args(argv)
    try:
        data = load(REPO / "versions.json")
        if args.command == "changed":
            print("\n".join(changed(data, REPO)))
            return 0
        problems = check(data, REPO)
    except VersionError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

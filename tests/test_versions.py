import json
import subprocess
from pathlib import Path

import pytest

import package
import versions

REPO = Path(__file__).resolve().parent.parent


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


def write(repo, rel, text):
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_versions(repo, modules, bundle_version, bundle_modules):
    data = {"modules": modules, "bundle": {"version": bundle_version, "modules": bundle_modules}}
    write(repo, "versions.json", json.dumps(data))


def commit_and_tag(repo, tag):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", tag)
    git(repo, "tag", tag)


@pytest.fixture
def repo(tmp_path):
    # A release from before versions.json: one VERSION file covered every module.
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "t")
    write(tmp_path, "mod/Alpha/X.EXML", "<a/>")
    write(tmp_path, "mod/Beta/X.EXML", "<b/>")
    write(tmp_path, "VERSION", "1.1.0\n")
    commit_and_tag(tmp_path, "v1.1.0")
    return tmp_path


def problems(repo):
    return versions.check(versions.load(repo / "versions.json"), repo)


def test_unchanged_modules_keep_their_released_version(repo):
    write_versions(repo, {"Alpha": "1.1.0", "Beta": "1.1.0"}, "1.1.0", ["Alpha", "Beta"])
    assert problems(repo) == []
    write_versions(repo, {"Alpha": "1.2.0", "Beta": "1.1.0"}, "1.1.0", ["Alpha", "Beta"])
    assert any("Alpha" in p and "unchanged" in p for p in problems(repo))


def test_a_changed_module_needs_a_higher_version(repo):
    write(repo, "mod/Alpha/X.EXML", "<a2/>")
    write_versions(repo, {"Alpha": "1.1.0", "Beta": "1.1.0"}, "1.2.0", ["Alpha", "Beta"])
    assert any("Alpha" in p and "changed" in p for p in problems(repo))
    write_versions(repo, {"Alpha": "1.0.9", "Beta": "1.1.0"}, "1.2.0", ["Alpha", "Beta"])
    assert any("Alpha" in p and "changed" in p for p in problems(repo))
    write_versions(repo, {"Alpha": "1.1.1", "Beta": "1.1.0"}, "1.2.0", ["Alpha", "Beta"])
    assert problems(repo) == []


def test_versions_compare_as_numbers_not_text(repo):
    write(repo, "mod/Alpha/X.EXML", "<a2/>")
    write_versions(repo, {"Alpha": "1.10.0", "Beta": "1.1.0"}, "1.2.0", ["Alpha", "Beta"])
    assert problems(repo) == []


def test_a_new_module_may_start_at_any_version(repo):
    write(repo, "mod/Gamma/X.EXML", "<g/>")
    write_versions(repo, {"Alpha": "1.1.0", "Beta": "1.1.0", "Gamma": "1.0.0"}, "1.1.0", ["Alpha", "Beta"])
    assert problems(repo) == []


def test_the_bundle_moves_up_when_anything_in_it_changes(repo):
    write(repo, "mod/Alpha/X.EXML", "<a2/>")
    write_versions(repo, {"Alpha": "1.1.1", "Beta": "1.1.0"}, "1.1.0", ["Alpha", "Beta"])
    assert any("bundle" in p for p in problems(repo))


def test_the_bundle_moves_up_when_a_module_joins_it(repo):
    write(repo, "mod/Gamma/X.EXML", "<g/>")
    modules = {"Alpha": "1.1.0", "Beta": "1.1.0", "Gamma": "1.0.0"}
    write_versions(repo, modules, "1.1.0", ["Alpha", "Beta", "Gamma"])
    assert any("bundle" in p for p in problems(repo))
    write_versions(repo, modules, "1.2.0", ["Alpha", "Beta", "Gamma"])
    assert problems(repo) == []


def test_the_bundle_keeps_its_version_when_nothing_in_it_changed(repo):
    write(repo, "mod/Gamma/X.EXML", "<g/>")
    write_versions(repo, {"Alpha": "1.1.0", "Beta": "1.1.0", "Gamma": "1.0.0"}, "1.2.0", ["Alpha", "Beta"])
    assert any("bundle" in p and "unchanged" in p for p in problems(repo))


def test_the_bundle_holds_only_listed_modules(repo):
    write_versions(repo, {"Alpha": "1.1.0", "Beta": "1.1.0"}, "1.1.0", ["Alpha", "Nope"])
    with pytest.raises(versions.VersionError, match="Nope"):
        versions.load(repo / "versions.json")


def test_a_malformed_version_is_refused(repo):
    write_versions(repo, {"Alpha": "1.1", "Beta": "1.1.0"}, "1.1.0", ["Alpha", "Beta"])
    with pytest.raises(versions.VersionError, match="Alpha"):
        versions.load(repo / "versions.json")


def test_a_release_with_versions_json_is_read_from_it(repo):
    write(repo, "mod/Alpha/X.EXML", "<a2/>")
    write_versions(repo, {"Alpha": "1.2.0", "Beta": "1.1.0"}, "1.2.0", ["Alpha", "Beta"])
    git(repo, "rm", "-q", "VERSION")
    commit_and_tag(repo, "v1.2.0")
    # The newest tag counts, compared as a version: v1.10.0 would beat v1.2.0.
    assert versions.last_release(repo)[0] == "v1.2.0"
    write_versions(repo, {"Alpha": "1.2.0", "Beta": "1.1.0"}, "1.2.0", ["Alpha", "Beta"])
    assert problems(repo) == []


def test_changed_lists_modules_whose_version_moved(repo):
    write(repo, "mod/Alpha/X.EXML", "<a2/>")
    write(repo, "mod/Gamma/X.EXML", "<g/>")
    write_versions(repo, {"Alpha": "1.1.1", "Beta": "1.1.0", "Gamma": "1.0.0"}, "1.2.0", ["Alpha", "Beta"])
    assert versions.changed(versions.load(repo / "versions.json"), repo) == ["Alpha", "Gamma"]


def test_the_shipped_modules_are_the_ones_versioned():
    assert package.SHIPPED == list(versions.load(REPO / "versions.json")["modules"])


def test_the_repo_versions_follow_the_last_release():
    try:
        versions.last_release(REPO)
    except versions.VersionError:
        pytest.skip("no release tags in this clone")
    assert problems(REPO) == []


def test_the_bundle_holds_the_full_overseer_set():
    # Decor and Rebalance change vanilla content broadly, so they stay opt-in.
    bundle = versions.load(REPO / "versions.json")["bundle"]
    assert bundle["modules"] == [
        "OverseersToolkit",
        "OverseersToolkit-Defense",
        "OverseersToolkit-SettlerStories",
        "OverseersToolkit-FairLedger",
    ]

"""Fail CI if deployable changes lack a version bump."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path("custom_components/samsungtv_max/manifest.json")
CONST_PATH = Path("custom_components/samsungtv_max/const.py")

DEPLOYABLE_PREFIXES: tuple[str, ...] = ("custom_components/samsungtv_max/",)
DEPLOYABLE_FILES: frozenset[str] = frozenset(
    {
        "scripts/deploy-ha-scp.ps1",
        "scripts/deploy-ha-rsync.sh",
    }
)


def _run(*args: str) -> str:
    res = subprocess.run(
        list(args),
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return res.stdout


def _read_version_from_manifest_bytes(raw: str) -> str:
    data = json.loads(raw)
    version = data.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("manifest.json has no string 'version'")
    return version


def _read_current_manifest_version() -> str:
    raw = (ROOT / MANIFEST_PATH).read_text(encoding="utf-8")
    return _read_version_from_manifest_bytes(raw)


def _read_current_integration_version() -> str:
    raw = (ROOT / CONST_PATH).read_text(encoding="utf-8")
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("INTEGRATION_VERSION"):
            # INTEGRATION_VERSION = "x.y.z"
            _, rhs = line.split("=", 1)
            val = rhs.strip().strip('"').strip("'")
            if val:
                return val
    raise ValueError("const.py is missing INTEGRATION_VERSION")


def _read_base_file(base_ref: str, relpath: Path) -> str:
    return _run("git", "show", f"{base_ref}:{relpath.as_posix()}")


def _changed_files(base_ref: str) -> list[str]:
    out = _run("git", "diff", "--name-only", f"{base_ref}...HEAD")
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def _is_deployable(path: str) -> bool:
    if path in DEPLOYABLE_FILES:
        return True
    return path.startswith(DEPLOYABLE_PREFIXES)


def main() -> int:
    # On pushes (no PR), still enforce internal consistency.
    base_branch = os.environ.get("GITHUB_BASE_REF", "").strip()
    current_manifest_version = _read_current_manifest_version()
    current_integration_version = _read_current_integration_version()

    if current_manifest_version != current_integration_version:
        print(
            "ERROR: Version mismatch.\n"
            f"- manifest: {current_manifest_version}\n"
            f"- const.py:  {current_integration_version}"
        )
        return 1

    if not base_branch:
        return 0

    base_ref = f"origin/{base_branch}"
    changed = _changed_files(base_ref)
    if not any(_is_deployable(p) for p in changed):
        return 0

    base_manifest_raw = _read_base_file(base_ref, MANIFEST_PATH)
    base_const_raw = _read_base_file(base_ref, CONST_PATH)
    base_manifest_version = _read_version_from_manifest_bytes(base_manifest_raw)

    # Reuse the same parsing logic for const.py by writing temporarily would be overkill;
    # do a small parse here to avoid file I/O.
    base_integration_version: str | None = None
    for line in base_const_raw.splitlines():
        line = line.strip()
        if line.startswith("INTEGRATION_VERSION"):
            _, rhs = line.split("=", 1)
            base_integration_version = rhs.strip().strip('"').strip("'")
            break
    if not base_integration_version:
        print("ERROR: base branch const.py is missing INTEGRATION_VERSION")
        return 1

    if current_manifest_version == base_manifest_version and current_integration_version == base_integration_version:
        print(
            "ERROR: Deployable files changed but integration version was not bumped.\n"
            f"- base:    {base_manifest_version}\n"
            f"- current: {current_manifest_version}\n"
            "Bump BOTH:\n"
            f"- {MANIFEST_PATH}\n"
            f"- {CONST_PATH}"
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


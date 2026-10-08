"""Shared helpers for the throwaway runtime mods. UNTESTED SKETCH: never run, only read against upstream sources.

Pattern borrowed (as an idea, code written fresh) from ShadowsKeep/nms-tracker-mod, a working NMS.py mod:
- the build gate reads NMS.exe's FileVersion string, which is the same number NMS.py uses as its version;
- key and button callbacks only set a flag, and the real work runs on the game's own thread from
  the main-loop hook, because calling game functions from the GUI thread is not known to be safe.
"""

import ctypes
import logging
from ctypes import wintypes
from functools import lru_cache

from pymhf.core import _internal

logger = logging.getLogger("OTCommon")

# NMS.py 180383.0 is the newest release on PyPI (2026-10-01). The game on this PC is 180836.
# Add "180836" here only after an NMS.py release for that build exists, or after the hooks the mod
# uses have been checked one by one against the newer exe.
SUPPORTED_BUILDS = {"180383"}


@lru_cache(maxsize=4)
def _file_version(path: str) -> str:
    if not path:
        return ""
    ver = ctypes.WinDLL("version")
    size = ver.GetFileVersionInfoSizeW(str(path), None)
    if not size:
        return ""
    buf = ctypes.create_string_buffer(size)
    if not ver.GetFileVersionInfoW(str(path), 0, size, buf):
        return ""
    ptr, length = ctypes.c_void_p(), wintypes.UINT()
    if not ver.VerQueryValueW(buf, "\\VarFileInfo\\Translation", ctypes.byref(ptr), ctypes.byref(length)):
        return ""
    lang, codepage = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_uint16 * 2)).contents
    key = f"\\StringFileInfo\\{lang:04x}{codepage:04x}\\FileVersion"
    if not ver.VerQueryValueW(buf, key, ctypes.byref(ptr), ctypes.byref(length)) or not length.value:
        return ""
    return ctypes.wstring_at(ptr.value, length.value).rstrip("\x00").strip()


def running_build() -> str:
    return _file_version(getattr(_internal, "BINARY_PATH", "") or "")


def build_supported(extra_ok: set | None = None) -> bool:
    build = running_build()
    return build in SUPPORTED_BUILDS or build in (extra_ok or set())


def vec_str(v) -> str:
    return f"({v.x:.3f}, {v.y:.3f}, {v.z:.3f})"


def mat34_str(m) -> str:
    """Works for cTkMatrix34 (pos is a Vector3f) and cTkPhysRelMat34 (pos is a cTkPhysRelVec3)."""
    pos = m.pos
    pos_s = vec_str(pos) if hasattr(pos, "x") else f"local {vec_str(pos.local)} offset {vec_str(pos.offset)}"
    return f"right {vec_str(m.right)} up {vec_str(m.up)} at {vec_str(m.at)} pos {pos_s}"


def dot(a, b) -> float:
    return a.x * b.x + a.y * b.y + a.z * b.z


def world_to_matrix_local(world, right, up, at, origin):
    """Local coordinates of `world` in the rigid frame (right, up, at, origin); all Vector3f-like."""
    dx, dy, dz = world.x - origin.x, world.y - origin.y, world.z - origin.z

    def d(axis):
        return dx * axis.x + dy * axis.y + dz * axis.z

    return d(right), d(up), d(at)

# /// script
# [tool.pymhf]
# exe = "NMS.exe"
# steam_gameid = 275850
# start_exe = true
# start_paused = true
# default_mod_save_dir = "{CURR_DIR}"
#
# [tool.pymhf.gui]
# shown = true
# always_on_top = true
#
# [tool.pymhf.logging]
# shown = true
# log_dir = "{CURR_DIR}"
# log_level = "info"
# window_name_override = "OT spike 2: world to base-local"
# ///
"""UNTESTED SKETCH. Convert the player's position into base-local coordinates three ways and compare.

Run as spike 1. Stand on the base computer's flag (the ^BASE_FLAG object sits at local (0, 0, 0) in the
save copy), press F9: every method that is right prints roughly (0, 0, 0). Walk 10 m forward and press
again: a right method changes by about 10 on one axis.

Methods, each from upstream declarations (nmspy 180383.0 data/types.py):
 A. The base's root scene node: cGcBaseBuildingManager.GetBaseRootNode (line 2606) then
    Engine.GetNodeAbsoluteTransMatrix (nmspy/engine.py) gives a scene-space matrix; invert it.
 B. cGcPlayerBasePersistentBuffer.mBaseMatrix (0x50, cTkPhysRelMat34, line 1215); use pos.local only and
    log pos.offset so it is clear whether offset matters.
 C. Planet-centred maths (base_frame.py): needs the base Position and Forward, which are in the save
    but not in these structs, so the planet-centred player position is logged for comparison only:
    player scene position minus cGcPlayerEnvironment.mNearestPlanetPos (0x2D0, line 1932).

Stub warnings that matter here:
- GetBaseBuildingRootMatrix's mangled name says it returns a cTkPhysRelMat34 by value (tools/data.json line
  1666), but the stub types `result` as cTkPhysRelVec3 (0x20 bytes, types.py line 2634). A Mat34 is 0x50
  bytes, so this sketch allocates a Mat34 and passes that. The stub's base-index argument is a pointer to a
  uint16, while the mangled name says BaseIndex by value; the call below passes a pointer as the stub says
  and the result is only trusted if it matches method B.
"""

import ctypes
import logging
import sys
from pathlib import Path

from pymhf import Mod
from pymhf.core.hooking import on_key_pressed
from pymhf.gui.decorators import gui_button

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import ot_common  # noqa: E402
import nmspy.data.basic_types as basic  # noqa: E402
import nmspy.data.types as nms  # noqa: E402
from nmspy.common import gameData  # noqa: E402
from nmspy.decorators import main_loop  # noqa: E402
from nmspy.engine import GetNodeAbsoluteTransMatrix  # noqa: E402

logger = logging.getLogger("OTSpike2")


def player_scene_position():
    player = gameData.player
    if player is None:
        return None
    return GetNodeAbsoluteTransMatrix(player.mRootNode).pos


def method_a(manager, index: int, player_pos):
    handle = basic.TkHandle()
    manager.GetBaseRootNode(ctypes.byref(handle), index, False)
    if not handle.lookupInt:
        return None
    m = GetNodeAbsoluteTransMatrix(handle)
    return m, ot_common.world_to_matrix_local(player_pos, m.right, m.up, m.at, m.pos)


def method_b(buf, player_pos):
    m = buf.mBaseMatrix
    origin = m.pos.local
    return ot_common.world_to_matrix_local(player_pos, m.right, m.up, m.at, origin), m.pos.offset


def method_get_root_matrix(manager, index: int):
    """Direct call of the declared function with a correctly sized result. Only used as a cross-check."""
    result = basic.cTkPhysRelMat34()
    idx = ctypes.c_uint16(index)
    manager.GetBaseBuildingRootMatrix(ctypes.byref(result), ctypes.byref(idx), 0)
    return result


class OTSpike2(Mod):
    __author__ = "ethan-hann"
    __description__ = "Throwaway: world to base-local conversion"
    __version__ = "0.0"

    def __init__(self):
        super().__init__()
        self._pending = False
        self._checked = False
        self._ok = False

    @gui_button("Convert player position")
    def convert_button(self):
        self._pending = True

    @on_key_pressed("f9")
    def convert_key(self):
        self._pending = True

    @main_loop.after
    def on_frame(self):
        if not self._checked:
            self._checked = True
            self._ok = ot_common.build_supported()
            logger.info("NMS.exe build %s, supported: %s", ot_common.running_build() or "unknown", self._ok)
        if not self._pending:
            return
        self._pending = False
        if not self._ok:
            logger.warning("Ignored: unsupported game build.")
            return
        try:
            self.convert()
        except Exception:
            logger.exception("convert failed")

    def convert(self):
        player_pos = player_scene_position()
        game_state = gameData.game_state
        if player_pos is None or game_state is None:
            logger.warning("Load a save and spawn first.")
            return
        manager = nms.engine_modules.mBaseBuildingManager
        env = gameData.player_environment
        if env is not None:
            planet_rel = (
                player_pos.x - env.mNearestPlanetPos.x,
                player_pos.y - env.mNearestPlanetPos.y,
                player_pos.z - env.mNearestPlanetPos.z,
            )
            logger.info("player scene %s, planet-centred %s", ot_common.vec_str(player_pos), planet_rel)
        buffers = game_state.mSavedInteractionsManager.maPersistentBaseBuffers
        for i in range(len(buffers)):
            ptr = buffers[i]
            if not ptr:
                continue
            buf = ptr.contents
            if buf.muiValidObjectsCount == 0:
                continue
            name = buf.mName.value.decode(errors="replace")
            b_local, b_offset = method_b(buf, player_pos)
            logger.info("[%d] %r B (mBaseMatrix): %s  (pos.offset %s)", i, name, b_local, ot_common.vec_str(b_offset))
            a = method_a(manager, i, player_pos)
            if a is not None:
                logger.info("[%d] A (root node): %s  matrix %s", i, a[1], ot_common.mat34_str(a[0]))
            root = method_get_root_matrix(manager, i)
            logger.info("[%d] GetBaseBuildingRootMatrix: %s", i, ot_common.mat34_str(root))

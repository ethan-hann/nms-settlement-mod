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
# window_name_override = "OT spike 4: terrain flatten"
# ///
"""UNTESTED SKETCH. Capture how the game calls the terrain editor's flatten, then replay it.

Declared upstream (nmspy 180383.0 data/types.py lines 3508-3540): cGcTerrainEditorBeam.Fire,
.ApplyTerrainEditStroke and .ApplyTerrainEditFlatten(this, sTerrainEditData by value, cGcProjectileImpact*).
Not declared: cGcProjectileImpact (only a uint64 pointer), the beam's own fields (edit plane, current edit
position), and any global beam instance. So this sketch:
  1. captures the beam's `this` from the real Fire call (the player must use the terrain editor);
  2. snapshots the first 0x200 bytes behind the impact pointer on every real flatten call, because the
     impact is a const reference to something the caller owns and the pointer is stale after the call;
  3. on F11, replays the last flatten with the snapshot copy. Snapshots from two flattens at different
     places show, by diff, which bytes hold the position; patching those is the step after this one.

Two things are unverified and decide the outcome: whether the flatten still runs when the target is inside
a settlement (players report terrain edits are ignored there; ReNMS 4.13 headers show terrain edit blocks
carry mbIsBaseProtected and edits carry mbSetBaseProtected, which may be the reason), and whether a replay
outside the editor's own update has side effects. Test outside a settlement first, on the creative slot.

Capacity note from the decoded save copy (corvette-destroyer\\save3.hg.json, PlayerStateData.TerrainEditData):
terrain edits are one shared buffer of 256 blocks and 30000 edits, and that main save has 29578 used, so
terrain edits on a long-lived save are near the limit; the creative test slot starts empty.
"""

import ctypes
import logging
import sys
import time
from pathlib import Path

from pymhf import Mod
from pymhf.core.hooking import on_key_pressed
from pymhf.core.memutils import get_addressof, map_struct
from pymhf.gui.decorators import gui_button

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import ot_common  # noqa: E402
import nmspy.data.types as nms  # noqa: E402
from nmspy.decorators import main_loop  # noqa: E402

logger = logging.getLogger("OTSpike4")

SNAPSHOT_BYTES = 0x200


class OTSpike4(Mod):
    __author__ = "ethan-hann"
    __description__ = "Throwaway: capture and replay a terrain flatten"
    __version__ = "0.0"

    def __init__(self):
        super().__init__()
        self._checked = False
        self._ok = False
        self._beam_addr = 0
        self._last_edit = None
        self._snapshots = []
        self._replay_pending = False

    @nms.cGcTerrainEditorBeam.Fire.after
    def captured_fire(self, this, *args):
        self._beam_addr = get_addressof(this)

    @nms.cGcTerrainEditorBeam.ApplyTerrainEditFlatten.before
    def captured_flatten(self, this, lEditData, lImpact):
        self._beam_addr = get_addressof(this)
        self._last_edit = (lEditData.mVoxelType, lEditData.mShape, lEditData.mCustom1, lEditData.mCustom2)
        snapshot = ctypes.string_at(int(lImpact), SNAPSHOT_BYTES)
        self._snapshots.append(snapshot)
        (HERE / f"flatten-impact-{len(self._snapshots)}-{time.strftime('%H%M%S')}.bin").write_bytes(snapshot)
        logger.info("flatten called: edit=%s impact snapshot #%d saved", self._last_edit, len(self._snapshots))
        if len(self._snapshots) >= 2:
            a, b = self._snapshots[-2], self._snapshots[-1]
            diff = [i for i in range(SNAPSHOT_BYTES) if a[i] != b[i]]
            logger.info("bytes that differ from the previous call: %s", [hex(i) for i in diff[:64]])

    @gui_button("Replay last flatten")
    def replay_button(self):
        self._replay_pending = True

    @on_key_pressed("f11")
    def replay_key(self):
        self._replay_pending = True

    @main_loop.after
    def on_frame(self):
        if not self._checked:
            self._checked = True
            self._ok = ot_common.build_supported()
            logger.info("NMS.exe build %s, supported: %s", ot_common.running_build() or "unknown", self._ok)
        if not (self._replay_pending and self._ok):
            self._replay_pending = False
            return
        self._replay_pending = False
        if not (self._beam_addr and self._snapshots and self._last_edit):
            logger.warning("Use the terrain editor to flatten once first, so there is something to replay.")
            return
        beam = map_struct(self._beam_addr, nms.cGcTerrainEditorBeam)
        edit = nms.sTerrainEditData()
        edit.mVoxelType, edit.mShape, edit.mCustom1, edit.mCustom2 = self._last_edit
        impact = ctypes.create_string_buffer(self._snapshots[-1], SNAPSHOT_BYTES)
        result = beam.ApplyTerrainEditFlatten(edit, ctypes.addressof(impact))
        logger.info("replayed flatten, returned %s", result)

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
# window_name_override = "OT spike 1: log base objects"
# ///
"""UNTESTED SKETCH. Log every persistent base buffer the game has loaded, and its building objects.

Run (cmd or PowerShell, game closed, Python 3.9 to 3.13 venv with `nmspy==180383.0`):
    pymhf run spike1_log_base_objects.py
Then load the creative test slot, stand in or near a base, press F8 (or the GUI button).

Evidence this relies on (nmspy 180383.0 data/types.py, same as scratch\\nmspy_types.py):
- cGcApplication.Data.mGameState.mSavedInteractionsManager at 0x317B10 (line 1439), whose
  maPersistentBaseBuffers (0x2408, line 1270) is a tk_vector of pointers to cGcPlayerBasePersistentBuffer.
- cGcPlayerBasePersistentBuffer.maBaseBuildingObjects (0x30, line 1212): elements of 0xD0 bytes, each with
  mData (cGcPersistentBaseEntry: At, Position, Up, ObjectID, Timestamp, UserData, Message) and
  mpBuildingEntry (0xC0).
Known stub warnings: muCurrentAddress and muBaseUA are both declared at 0x40 (lines 1213 and 1216), and
the offsets were last verified on older builds. If the log shows nonsense counts, the first thing to
check is the 0x30 vector and the 0x2408 / 0x317B10 offsets.

The JSON written next to this file uses the save's own key names so it can be diffed against
tools/save_inspect.py output for the same slot after the game saves.
"""

import json
import logging
import sys
import time
from pathlib import Path

from pymhf import Mod
from pymhf.core.hooking import on_key_pressed
from pymhf.gui.decorators import gui_button

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import ot_common  # noqa: E402
import nmspy.data.types as nms  # noqa: E402
from nmspy.common import gameData  # noqa: E402
from nmspy.decorators import main_loop  # noqa: E402

logger = logging.getLogger("OTSpike1")


def dump_buffer(index: int, buf) -> dict:
    objects = buf.maBaseBuildingObjects
    out = {
        "index": index,
        "address": f"0x{buf.muCurrentAddress:X}",
        "name": buf.mName.value.decode(errors="replace"),
        "base_type": str(buf.meBaseType),
        "valid_objects": buf.muiValidObjectsCount,
        "vector_size": len(objects),
        "base_matrix": ot_common.mat34_str(buf.mBaseMatrix),
        "objects": [],
    }
    if buf.mpLayoutHandle:
        layout = buf.mpLayoutHandle.contents
        out["layout_base_position"] = ot_common.vec_str(layout.mBasePosition)
        out["layout_radius_sqr"] = layout.mfBaseRadiusSqr
    for i in range(len(objects)):
        entry = objects[i]
        data = entry.mData
        out["objects"].append(
            {
                "ObjectID": "^" + str(data.ObjectID),
                "Position": [data.Position.x, data.Position.y, data.Position.z],
                "Up": [data.Up.x, data.Up.y, data.Up.z],
                "At": [data.At.x, data.At.y, data.At.z],
                "Timestamp": data.Timestamp,
                "UserData": data.UserData,
                "entry_id": str(entry.mpBuildingEntry.contents.ID) if entry.mpBuildingEntry else None,
            }
        )
    return out


class OTSpike1(Mod):
    __author__ = "ethan-hann"
    __description__ = "Throwaway: log base buffers and their objects"
    __version__ = "0.0"

    def __init__(self):
        super().__init__()
        self._pending = False
        self._checked = False
        self._ok = False

    @gui_button("Log bases")
    def log_button(self):
        self._pending = True

    @on_key_pressed("f8")
    def log_key(self):
        self._pending = True

    @main_loop.after
    def on_frame(self):
        if not self._checked:
            self._checked = True
            build = ot_common.running_build()
            self._ok = ot_common.build_supported()
            logger.info("NMS.exe build %s, supported by this mod: %s", build or "unknown", self._ok)
        if not self._pending:
            return
        self._pending = False
        if not self._ok:
            logger.warning("Ignored: unsupported game build; edit SUPPORTED_BUILDS after checking hooks.")
            return
        try:
            self.log_bases()
        except Exception:
            logger.exception("log_bases failed")

    def log_bases(self):
        game_state = gameData.game_state
        if game_state is None:
            logger.warning("No game state yet; load a save first.")
            return
        buffers = game_state.mSavedInteractionsManager.maPersistentBaseBuffers
        logger.info("persistent base buffers: %d", len(buffers))
        dumped = []
        for i in range(len(buffers)):
            ptr = buffers[i]
            if not ptr:
                continue
            info = dump_buffer(i, ptr.contents)
            dumped.append(info)
            logger.info(
                "[%d] %s type=%s name=%r valid=%d vector=%d",
                i, info["address"], info["base_type"], info["name"], info["valid_objects"], info["vector_size"],
            )
            for o in info["objects"][:5]:
                logger.info("    %s at %s", o["ObjectID"], o["Position"])
        target = HERE / f"spike1-{time.strftime('%Y%m%d-%H%M%S')}.json"
        target.write_text(json.dumps(dumped, indent=1), encoding="utf-8")
        logger.info("wrote %s", target)

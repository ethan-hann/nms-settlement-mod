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
# log_level = "debug"
# window_name_override = "OT spike 3: place DECALPATH"
# ///
"""UNTESTED SKETCH. There is no placement function in NMS.py 180383.0, so this file is three experiments.

Facts (checked by grep over nmspy/data/types.py, tools/data.json and example_mods at master 52e2e554):
no declared function creates, places or adds a base part. The closest declared names are
cGcBaseBuildingManager.AddObjectMarker (types.py line 2643, a HUD marker for an object) and the raw
cGcPlayerBasePersistentBuffer.maBaseBuildingObjects vector.

Experiment 1 (safe): find the game's own placement code by tracing callers.
  Hook AddObjectMarker and log who calls it while you place a part by hand in the creative slot. The
  caller RVAs point into the function that creates a placed object; open NMS.exe in a disassembler at
  those RVAs, find the enclosing function, and its callers up to the build-menu "place" action.
  `get_caller` is documented for manual_hook; use with a function_hook detour is untested.
  Warning: scan_patterns.py (read-only byte scan of the installed NMS.exe, FileVersion 180836) finds
  NO match for the AddObjectMarker pattern, while the patterns of the other base-building hooks match
  exactly once. On 180836 this experiment needs a new pattern for AddObjectMarker, or another anchor.

Experiment 2 (needs reverse engineering first): declare the found function the way
  ShadowsKeep/nms-tracker-mod's nms_ext.py declares its own (class with `this` typed as a pointer, a
  byte pattern that matches once, RVA in a comment), then call it for ^DECALPATH. PLACE_PATTERN is None
  on purpose; the signature below is a guess shaped by the 4.13 headers in sonny-tel/renms
  (cGcBaseBuildingPlayerPlacement, cGcBaseBuildingBaseLayout::AddObject(TkID<128>, cTkVector3)).
  Nothing here is a real function until the pattern and arguments are confirmed.

Experiment 3 (last resort, creative slot only): append a raw entry to maBaseBuildingObjects. This does not
  create the scene node, link grids, network hash or object counts, so the part is not expected to appear
  until the slot is saved and reloaded, and a bad entry can corrupt the base. TkStd.tk_vector.append has
  a bug when the vector is full: it calls self.add, which does not exist (basic_types.py, expand path), so
  this sketch refuses when there is no spare capacity.
"""

import ctypes
import logging
import sys
import time
from ctypes import c_bool, c_uint16, c_uint64
from pathlib import Path
from typing import Annotated

from pymhf import Mod
from pymhf.core.hooking import Structure, function_hook, get_caller, on_key_pressed
from pymhf.core.memutils import get_addressof
from pymhf.gui.decorators import gui_button

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from ctypes import _Pointer  # noqa: E402,I001  after pymhf: it swaps in a subscriptable _Pointer on import

import ot_common  # noqa: E402
import nmspy.data.basic_types as basic  # noqa: E402
import nmspy.data.types as nms  # noqa: E402
from nmspy.common import gameData  # noqa: E402
from nmspy.decorators import main_loop  # noqa: E402

logger = logging.getLogger("OTSpike3")

PLACE_PATTERN = None  # fill in from reverse engineering; keep None until then
ALLOW_RAW_APPEND = False  # experiment 3 switch


class cGcBaseBuildingManagerExt(Structure):
    """Placeholder for the function found by experiment 1. Name and arguments are guesses."""

    if PLACE_PATTERN is not None:

        @function_hook(PLACE_PATTERN)
        def PlaceObject(
            self,
            this: "_Pointer[cGcBaseBuildingManagerExt]",
            lpID: _Pointer[basic.TkID0x10],
            lpMatrix: _Pointer[basic.cTkPhysRelMat34],
            luBaseIndex: Annotated[int, c_uint16],
            luUserData: Annotated[int, c_uint64],
        ) -> c_bool: ...


class OTSpike3(Mod):
    __author__ = "ethan-hann"
    __description__ = "Throwaway: find and call the base-part placement code"
    __version__ = "0.0"

    def __init__(self):
        super().__init__()
        self._checked = False
        self._ok = False
        self._place_pending = False
        self._append_pending = False

    # Experiment 1
    @get_caller
    @nms.cGcBaseBuildingManager.AddObjectMarker.after
    def traced_add_object_marker(self, this, lID, lObjectHandle):
        rva = self.traced_add_object_marker.caller_address()
        logger.info("AddObjectMarker id=%s handle=0x%X caller RVA=0x%X", lID.contents, int(lObjectHandle), rva)

    # Experiment 2
    @gui_button("Place DECALPATH at player")
    def place_button(self):
        self._place_pending = True

    # Experiment 3
    @on_key_pressed("f10")
    def append_key(self):
        self._append_pending = True

    @main_loop.after
    def on_frame(self):
        if not self._checked:
            self._checked = True
            self._ok = ot_common.build_supported()
            logger.info("NMS.exe build %s, supported: %s", ot_common.running_build() or "unknown", self._ok)
        if not self._ok:
            self._place_pending = self._append_pending = False
            return
        if self._place_pending:
            self._place_pending = False
            self.try_place()
        if self._append_pending:
            self._append_pending = False
            self.try_raw_append()

    def try_place(self):
        if PLACE_PATTERN is None:
            logger.warning("No placement function known yet; run experiment 1 first.")
            return
        # Needs: a base index, a matrix in whatever frame the real function expects (spike 2 settles the
        # frame), and an ID buffer. Left unwritten until the real signature is known.
        logger.warning("PLACE_PATTERN is set but the call is not written yet.")

    def try_raw_append(self):
        if not ALLOW_RAW_APPEND:
            logger.warning("ALLOW_RAW_APPEND is False; nothing done.")
            return
        game_state = gameData.game_state
        buffers = game_state.mSavedInteractionsManager.maPersistentBaseBuffers
        target = None
        for i in range(len(buffers)):
            ptr = buffers[i]
            if ptr and ptr.contents.muiValidObjectsCount:
                target = ptr.contents
                break
        if target is None:
            logger.warning("No populated base buffer.")
            return
        objects = target.maBaseBuildingObjects
        if objects.vector_size >= objects.allocated_size:
            logger.warning("Vector is full (%d); tk_vector.append would hit the self.add bug.", objects.vector_size)
            return
        # Copy the first existing entry and change only the ID and position, so every field the game
        # fills itself (vtable, region id, link indexes, entry pointer) stays plausible.
        element_type = nms.cGcPlayerBasePersistentBuffer.PlayerBasePersistentData
        size = ctypes.sizeof(element_type)
        src = get_addressof(objects._ptr)
        clone = (ctypes.c_ubyte * size).from_address(src)
        new = (ctypes.c_ubyte * size)()
        ctypes.memmove(new, clone, size)
        entry = element_type.from_buffer(new)
        entry.mData.ObjectID = basic.TkID0x10("DECALPATH")
        entry.mData.Timestamp = int(time.time())
        logger.info("Appending raw DECALPATH entry to base %r", target.mName.value.decode(errors="replace"))
        objects.append(entry)
        logger.info("vector size now %d; save, quit, reload the slot and look at the base", objects.vector_size)

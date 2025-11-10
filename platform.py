# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
from os.path import isdir, isfile, join

from platform import system

from platformio.managers.platform import PlatformBase
from platformio.util import get_systype

PLATFORM_DIR = os.path.dirname(__file__)

class EgmicroPlatform(PlatformBase):

    def configure_default_packages(self, variables, targets):
        board = variables.get("board")
        board_config = self.board_config(board)

        default_protocol = board_config.get("upload.protocol") or ""
        if variables.get("upload_protocol", default_protocol) == "dfu":
            self.packages["tool-dfuutil"]["optional"] = False

        return PlatformBase.configure_default_packages(self, variables, targets)

    def get_boards(self, id_=None):
        result = PlatformBase.get_boards(self, id_)
        if not result:
            return result
        if id_:
            return self._add_default_debug_tools(result)
        else:
            for key, value in result.items():
                result[key] = self._add_default_debug_tools(result[key])
        return result

    def _add_default_debug_tools(self, board):
        debug = board.manifest.get("debug", {})
        upload_protocols = board.manifest.get("upload", {}).get(
            "protocols", [])
        if "tools" not in debug:
            debug['tools'] = {}

        for link in ("cmsis-dap", "atlink", "atlink_dap_v2", "jlink", "stlink"):
            if link not in upload_protocols or link in debug['tools']:
                continue
            pyocd_target = debug.get("pyocd_target")
            assert pyocd_target

            debug["tools"][link] = {
                # "onboard": True,
                "server": {
                    "package": "tool-pyocd",
                    "executable": "$PYTHONEXE",
                    "arguments": [
                        "pyocd-gdbserver.py",
                        "--pack", os.path.join(PLATFORM_DIR, 'misc', 'EGmicro.EG32M0xx_DFP.1.0.1.pack'),
                        "--target",  pyocd_target,
                    ],
                    "ready_pattern": "GDB server started on port"
                }
            }

        board.manifest['debug'] = debug
        return board

    def configure_debug_session(self, debug_config):
        if debug_config.speed:
            if "jlink" in (debug_config.server or {}).get("executable", "").lower():
                debug_config.server["arguments"].extend(
                    ["-speed", debug_config.speed]
                )
            elif "pyocd" in debug_config.server["package"]:
                debug_config.server["arguments"].extend(
                    ["--frequency", debug_config.speed]
                )
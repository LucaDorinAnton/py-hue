import logging
from dataclasses import dataclass
from enum import Enum
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from bluepy.btle import ScanEntry, Peripheral, Characteristic

from py_hue.bluepy_utils import is_root, get_bluetooth_devices, filter_likely_smart_plugs, connect_to_smart_plug


logger = logging.getLogger(__name__)


class StateChange(str, Enum):
    activate = 'activate'
    deactivate = 'deactivate'
    toggle = 'toggle'

class NonRootException(Exception):
    pass


@dataclass(frozen=True, eq=True)
class PlugState:
    state: bool = False

    def to_bytes(self) -> bytes:
        if self.state:
            return b'\x01'
        return b'\x00'

    @classmethod
    def from_bytes(cls, value: bytes):
        if value not in {b'\x00', b'\x01'}:
            raise ValueError("Only bytes \x00 and \x01 are supported")
        return PlugState(state=value == b'\x01')

    def __invert__(self) -> "PlugState":
        return PlugState(state=not self.state)



def scan_for_plugs() -> List[ScanEntry]:
    scans: List[ScanEntry] = get_bluetooth_devices()
    return filter_likely_smart_plugs(scans)



@asynccontextmanager
async def lifespan(app: FastAPI):
    if not is_root():
        raise NonRootException("This app needs to run as root to handle bluetooth")
    logger.info("App is running as root - continuing")    
    yield

app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"service": "py-hue"}


@app.get("/devices")
def read_item():
    plugs: List[ScanEntry] = scan_for_plugs()
    return {"plugs": [plug.addr for plug in plugs]}


@app.get("/devices/{uuid}/{state}")
def change_state(uuid: str, state: StateChange):
    plug: Peripheral = connect_to_smart_plug(uuid)
    characteristic: Characteristic = plug.getCharacteristics(uuid="932c32bd-0002-47a2-835a-a8d455b859dd")[0]
    
    current_state: PlugState = PlugState.from_bytes(characteristic.read())
    if state == StateChange.activate:
        characteristic.write(PlugState(True).to_bytes())
    elif state == StateChange.deactivate:
        characteristic.write(PlugState(False).to_bytes())
    else:
        characteristic.write((~current_state).to_bytes())
    return 'Ok'


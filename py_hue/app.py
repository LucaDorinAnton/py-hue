import logging
from enum import Enum
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from bluepy.btle import ScanEntry, Peripheral, Characteristic

from bluepy_utils import is_root, get_bluetooth_devices, filter_likely_smart_plugs


logger = logging.getLogger(__name__)


class StateChange(str, Enum):
    activate = 'activate'
    deactivate = 'deactivate'
    toggle = 'toggle'

class NonRootException(Exception):
    pass


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
    plugs: List[ScanEntry] = scan_for_plugs()
    plugs = [plug for plug in plugs if plug.addr.lower() == uuid.lower()]
    if not plugs:
        return HTTPException(status_code=404, detail=f"Smart plug with UUID {uuid} not found")
    if len(plugs) != 1:
        return HTTPException(status_code=500, detail=f"Multiple Smart plugs found for UUID {uuid}")
    plug: Peripheral = Peripheral(deviceAddr=uuid, addrType="random")
    characteristic: Characteristic = plug.getCharacteristics("932c32bd-0002-47a2-835a-a8d455b859dd")[0]
    if state == StateChange.activate:
        characteristic.write(b'\x01')
    elif state == StateChange.deactivate:
        characteristic.write(b'\x00')
    else:
        current_state: bytes = characteristic.read()
        if current_state == b'\x00':
            characteristic.write(b'\x01')
        else:
            characteristic.write(b'\x00')
    return 'Ok'


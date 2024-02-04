import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from bluepy.btle import ScanEntry

from bluepy_utils import is_root, get_bluetooth_devices, filter_likely_smart_plugs


logger = logging.getLogger(__name__)


class NonRootException(Exception):
    pass


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
    scans: ScanEntry = get_bluetooth_devices()
    plugs: ScanEntry = filter_likely_smart_plugs(scans)
    return {"plugs": [plug.addr for plug in plugs]}


import os
import logging
from typing import List, Iterable

from bluepy.btle import Scanner, DefaultDelegate, ScanEntry, Peripheral, BTLEDisconnectError, ADDR_TYPE_RANDOM
from tenacity import retry, retry_if_exception_type, after_log, stop_after_attempt


logger = logging.getLogger(__name__)

def is_root() -> bool:
    return os.geteuid() == 0


@retry(
    retry=retry_if_exception_type(BTLEDisconnectError), 
    stop=stop_after_attempt(5),
    after=after_log(logger=logger, log_level=logging.WARNING),
    )
def get_bluetooth_devices() -> List[ScanEntry]:
    return list(Scanner().scan())



def filter_likely_smart_plugs(scans: Iterable[ScanEntry]) -> Iterable[ScanEntry]:
    return [scan for scan in scans if (
        scan.addrType is ADDR_TYPE_RANDOM and
        scan.scanData.get(ScanEntry.COMPLETE_LOCAL_NAME, b'') == b'Hue smart plug'
    )]


@retry(
    retry=retry_if_exception_type(BTLEDisconnectError), 
    stop=stop_after_attempt(5),
    after=after_log(logger=logger, log_level=logging.WARNING),
    )
def connect_to_smart_plug(address: str) -> Peripheral:
    return Peripheral(deviceAddr=address, addrType=ADDR_TYPE_RANDOM)

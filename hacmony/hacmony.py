from .device import Device
from .app import App
from .explorer import Explorer
from .hstg import HSTG
from loguru import logger
import time


class HACMony(object):
    def __init__(self):
        self.device_list = {}
        from .utils import get_available_devices
        for device_serial in get_available_devices():
            self.device_list[device_serial] = (Device(device_serial))
    
    def explore(self, device, depth, app_path='', service_list=[], timeout=30):
        assert isinstance(device, Device)
        app = App(device, app_path)
        explorer = Explorer(device, app)
        hstg = HSTG(device)
        explorer.explore_dfs(depth, hstg, service_list, timeout)
        return hstg
    
    def hop(self, source_device, target_device, app):
        return
    
    def detect_hac(self, test_device, test_app, test_hstg, cflc_device, cflc_app, cflc_hstg):
        test_seqs = test_hstg.get_PLAYs()
        cflc_seqs = cflc_hstg.get_PLAYs()
        statuses = []
        for test_seq in test_seqs:
            for clfc_seq in cflc_seqs:
                test_device.start_app(test_app)
                cflc_device.start_app(cflc_app)
                for event in test_seq:
                    test_device.u2.click(event)
                    time.sleep(1)
                for event in clfc_seq:
                    cflc_device.u2.click(event)
                    time.sleep(1)
                self.hop(test_device, cflc_device)
                time.sleep(1)
                status = cflc_device.adb.get_audio_status(test_app.get_package_name())
                statuses.append(status)
                test_device.stop_app(test_app)
                cflc_device.stop_app(cflc_app)
        return statuses


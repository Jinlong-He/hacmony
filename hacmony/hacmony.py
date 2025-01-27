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
        size = source_device.get_device_size()
        width = size[0]
        height = size[1]
        print(f'source_device width*height: {width}*{height}')
        if width < height:
            orientation = 'port'  # 竖屏
        else:
            orientation = 'land'  # 横屏

        source_device.press("recent")
        time.sleep(1)

        if orientation == 'port':
            source_device.swipe(width * 0.75, height * 0.5, width * 0.25, height * 0.5)
            time.sleep(1)

        drag_from_elem = None
        drag_from_elem_parent = source_device(resourceId="com.huawei.android.launcher:id/task_view")
        for drag_from_elem_p in drag_from_elem_parent:
            if app in drag_from_elem_p.info['contentDescription']:
                drag_from_elem = drag_from_elem_p.child(resourceId="com.huawei.android.launcher:id/snapshot")

        drag_to_elem = None
        drag_to_elem_parent = target_device(resourceId="com.huawei.android.launcher:id/device_background")
        for drag_to_elem_p in drag_to_elem_parent:
            device_name = drag_to_elem_p.sibling(resourceId="com.huawei.android.launcher:id/device_name")
            if target_device in device_name.info['text']:
                drag_to_elem = drag_to_elem_p.child(resourceId="com.huawei.android.launcher:id/device_animate")

        drag_from_elem_bounds = drag_from_elem.info['bounds']
        drag_to_elem_bounds = drag_to_elem.info['bounds']
        left_w = int((drag_from_elem_bounds['left'] + drag_from_elem_bounds['right']) / 2)
        left_h = int((drag_from_elem_bounds['top'] + drag_from_elem_bounds['bottom']) / 2)
        right_w = int((drag_to_elem_bounds['left'] + drag_to_elem_bounds['right']) / 2)
        right_h = int((drag_to_elem_bounds['top'] + drag_to_elem_bounds['bottom']) / 2)
        source_device.drag(left_w, left_h, right_w, right_h, 2)
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


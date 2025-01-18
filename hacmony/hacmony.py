from device import Device
from app import App
from explorer import Explorer
from hstg import HSTG


class HACMony(object):
    def __init__(self):
        self.device_list = []
        from utils import get_available_devices
        for device_serial in get_available_devices():
            self.device_list.append(Device(device_serial))
    
    def explore_for_hopping(self, device, app_path=''):
        assert isinstance(device, Device)
        app = App(device, app_path)
        print(app.package_name)
        explorer = Explorer(device, app)
        hstg = HSTG(device)
        # todo
        depth = 4
        # todo
        service_list = ['QQPlayerService']
        # return explorer.explore_for_audio(hstg, service_list)
        # return explorer.test_explore_for_audio(hstg, service_list)
        return explorer.explore_dfs(depth, hstg, service_list)
    
    def hop(self, source_device, target_device, app):
        return


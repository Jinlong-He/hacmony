import time
from times import Times


class Explorer(object):
    def __init__(self, device, app):
        self.device = device
        self.app = app
        self.adb = device.adb
        self.u2 = device.u2
        self.package_name = self.adb.get_current_package()
    
    def explore_dfs(self, depth, hstg, service_list=[]):
        if not service_list:
            return
        if not depth:
            return
        elements = self.u2(clickable='true')
        if not elements:
            return
        # todo elements order filter
        package_name = self.package_name
        for element in elements:
            if not service_list:
                return
            hstg.add_event(element)
            element.click()
            time.sleep(1)
            if hstg.add_state()[1]:
                audio_status = self.adb.get_audio_status(package_name)
                if audio_status:
                    # todo tocheck
                    keys = [key.split(":")[-1] for key, value in audio_status.items() if
                            key.split(":")[-1] in service_list and value in ['START', 'START*', 'DUCK']]
                    if keys:
                        print(f'keys={keys}')
                        service_list = list(set(service_list) - set(keys))
                        print(f'service_list={service_list}')
                hstg.add_edge()
                self.explore_dfs(depth - 1, hstg, service_list)
                # 回退至上个state
                hstg.back_state(hstg.visit_states[-2])
            else:
                self.explore_dfs(depth - 1, hstg, service_list)
                # 回退至本个state
                hstg.back_state(hstg.visit_states[-1])
        return

    def explore_bfs(self, hstg, service_list=[]):
        # todo 结点入队列
        if not service_list:
            return
        d = self.u2
        elements = d(clickable='true')
        if not elements:
            return
        for element in elements:
            element.click()
            time.sleep(1)
            for service in service_list:
                if self.adb.get_audio_status(self.package_name, service) in ['START', 'START*', 'DUCK']:
                    service_list.remove(service)
                    hstg.add_state(service)
                    print(hstg.states[0].act_name, hstg.states[0].audio_status)
            # todo 回退上一步
        return

    def explore_for_audio(self, hstg, service_list=[]):
        # strategy qqmusic
        # xml_hierarchy = self.u2.dump_hierarchy()
        # with open(f'xml_hierarchy.xml', 'w', encoding='utf-8') as f:
        #     f.write(xml_hierarchy)
        # elements = self.u2.xpath('//node[@clickable="true"]').all()
        services = service_list[:]
        d = self.u2
        elements = d(clickable='true')
        if not elements:
            return
        for element in elements:
            content_desc = element.info.get('contentDescription', '')
            if '播放' in content_desc:
                element.click()
                time.sleep(1)
                for service in services:
                    print(self.adb.get_audio_status(self.package_name))
                    return
                    # todo check start start* duck
                    # if self.adb.get_audio_status(self.package_name, service) in ['START', 'START*', 'DUCK']:
                        # services.remove(service)
                        # hstg.add_state(service)
                        # # todo hstg.add_edge()
                        # print(hstg.states[0].act_name, hstg.states[0].audio_status)
                        # if not services:
                        #     return
                # todo 回退上一步
        return

    def test_explore_dfs(self, depth, hstg, service_list, timeout=30):
        if self.is_return(depth, hstg, service_list):
            return

        views = hstg.states[hstg.visit_states[-1]].views
        for view in views:
            if self.is_return(depth, hstg, service_list):
                return

            if view.clickable in ['false', 'False']:
                continue
            if '返回' in view.description:
                continue

            print(f'service_list={service_list}')
            print(f'clickable={view.clickable}')
            print(f'description={view.description}')
            print(f'class_name={view.class_name}')

            hstg.add_event(view.bound)
            hstg.handle_event(hstg.events[-1])

            if hstg.add_state()[1]:
                audio_status = hstg.states[hstg.visit_states[-1]].audio_status
                if audio_status:
                    keys = [key for key, value in audio_status.items() if
                            key in service_list and value in ['START', 'START*', 'DUCK']]
                    if keys:
                        print(f'keys={keys}')
                        for key in keys:
                            service_list.remove(key)
                        print(f'service_list={service_list}')
                hstg.add_edge()
                if self.is_return(depth, hstg, service_list):
                    return
                self.test_explore_dfs(depth - 1, hstg, service_list)
                if self.is_return(depth, hstg, service_list):
                    return
                # 回退至上个state
                hstg.back_state(hstg.visit_states[-2])
            else:
                self.test_explore_dfs(depth - 1, hstg, service_list)
                if self.is_return(depth, hstg, service_list):
                    return
                # 回退至本个state
                hstg.back_state(hstg.visit_states[-1])
        return

    def is_return(self, depth, hstg, service_list):
        # 深度到达 返回
        if not depth:
            print(f'return: depth={depth}')
            return True

        # 超时 返回
        current_time = Times()
        if hstg.start_time.time_out(current_time):
            print(f'return: time is out.')
            return True

        # 全部搜索到
        if not service_list:
            print(f'return: service_list={service_list}')
            return True

        return False



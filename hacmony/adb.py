import subprocess
import re
from loguru import logger
try:
    from shlex import quote  # Python 3
except ImportError:
    from pipes import quote  # Python 2

class ADBException(Exception):
    """
    Exception in ADB connection
    """
    pass

class ADB(object):
    """
    this class describes a connector (ADB or HDC)
    """
    def __init__(self, device=None):
        self.device = device
        self.cmd_prefix = ['adb', "-s", device.serial]
        self.sdk = self.get_sdk_version()

    def run_cmd(self, extra_args):
        """
        run a command and return the output
        :return: output of command
        @param extra_args: arguments to run in adb or hdc
        """
        if isinstance(extra_args, str):
            extra_args = extra_args.split()
        if not isinstance(extra_args, list):
            msg = "invalid arguments: %s\nshould be str, %s given" % (extra_args, type(extra_args))
            logger.warning(msg)
            raise ADBException(msg)

        args = [] + self.cmd_prefix
        args += extra_args

        logger.debug('command:')
        logger.debug(args)
        r = subprocess.check_output(args).strip()
        if not isinstance(r, str):
            r = r.decode()
        logger.debug('return:')
        logger.debug(r)
        return r

    def shell(self, extra_args):
        """
        run an `adb shell` command
        @param extra_args:
        @return: output of adb shell command
        """
        if isinstance(extra_args, str):
            extra_args = extra_args.split()
        if not isinstance(extra_args, list):
            msg = "invalid arguments: %s\nshould be str, %s given" % (extra_args, type(extra_args))
            logger.warning(msg)
            raise ADBException(msg)

        shell_extra_args = ['shell'] + [ quote(arg) for arg in extra_args ]
        return self.run_cmd(shell_extra_args)

    def shell_grep(self, extra_args, grep_args):
        """
        run an `adb shell` command with `grep` command
        @param extra_args:
        @param grep_args:
        @return: output of adb shell command
        """
        if isinstance(extra_args, str):
            extra_args = extra_args.split()
        if isinstance(grep_args, str):
            grep_args = grep_args.split()
        if not isinstance(extra_args, list) or not isinstance(grep_args, list):
            msg = "invalid arguments: %s\nshould be str, %s given" % (extra_args, type(extra_args))
            logger.warning(msg)
            raise ADBException(msg)

        args = self.cmd_prefix +['shell'] + [ quote(arg) for arg in extra_args ]
        grep_args = ['grep'] + [ quote(arg) for arg in grep_args ]
        
        proc1 = subprocess.Popen(args, stdout=subprocess.PIPE)
        proc2 = subprocess.Popen(grep_args, stdin=proc1.stdout,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        proc1.stdout.close() # Allow proc1 to receive a SIGPIPE if proc2 exits.
        out, err = proc2.communicate()
        if not isinstance(out, str):
            out = out.decode()
        return out

    def check_connectivity(self):
        """
        check if adb is connected
        :return: True for connected
        """
        r = self.run_cmd("get-state")
        return r.startswith("device")
    
    def get_installed_apps(self):
        """
        Get the package names and apk paths of installed apps on the device
        :return: a dict, each key is a package name of an app and each value is the file path to the apk
        """
        app_lines = self.shell("pm list packages -f").splitlines()
        app_line_re = re.compile("package:(?P<apk_path>.+)=(?P<package>[^=]+)")
        package_to_path = {}
        for app_line in app_lines:
            m = app_line_re.match(app_line)
            if m:
                package_to_path[m.group('package')] = m.group('apk_path')
        return package_to_path
    
    def get_uid(self, package_name):
        process_lines = self.shell_grep("ps", package_name).splitlines()
        if len(process_lines) > 0 :
            usr_name = process_lines[0].split()[0]
            uid = str(int(usr_name.split('_a')[1]) + 10000)
            return uid
        else :
            return

    def get_pid(self, package_name, service_name):
        #wait for check whether service_name is form of pakage_name:service_name
        process_lines = self.shell_grep("ps", "%s:%s" % (package_name, service_name)).splitlines()
        if len(process_lines) > 0:
            pid = str(process_lines[0].split()[1])
            return pid
        else:
            return

    def get_service_name(self, package_name, pid):
        process_lines = self.shell_grep("ps", package_name).splitlines()
        if len(process_lines) > 0:
            for process_line in process_lines:
                if process_line.split()[1] == pid:
                    service_name = process_line.split()[8]
                    return service_name
        else:
            return

    def get_audio_status(self, package_name, orientation=0):
        """
        Get the audio status of given app on the device
        :return: a dict, each key is a package name of an app and each value is the file path to the apk
        """
        audio_lines = self.shell_grep("dumpsys audio", "AudioPlaybackConfiguration").splitlines()
        audio_line_re = re.compile(".*u/pid:(.*)/(.*) .*state:(.*) attr.*")
        audio_status_dict = {}
        started_count = 0
        if orientation:
            audio_lines = reversed(audio_lines)
        for audio_line in audio_lines:
            m = audio_line_re.match(audio_line)
            if m:
                uid = m.group(1)
                pid = m.group(2)
                status = m.group(3)
                audio_status_dict[(uid, pid)] = status
                if status == 'started':
                    started_count += 1
        req_focus_lines = self.shell_grep("dumpsys audio", "requestAudioFocus").splitlines()
        req_focus_line_re = re.compile(".*uid/pid (\d*)/(\d*) .*clientId=(.*) callingPack=.*")
        client_dict = {}
        started_count = 0
        for req_focus_line in req_focus_lines:
            m = req_focus_line_re.match(req_focus_line)
            if m:
                uid = str(m.group(1))
                pid = str(m.group(2))
                client_id = m.group(3)
                client_dict[client_id] = (uid, pid)
        focus_lines = self.shell_grep("dumpsys audio", "source:").splitlines()
        focus_line_re = re.compile(".* pack: (.*) -- client: (.*) -- gain: (.*) -- flags.* loss: (.*) -- notified.*")
        focus_dict = {}
        for focus_line in focus_lines:
            # print(focus_line)
            m = focus_line_re.match(focus_line)
            if m:
                (uid, pid) = client_dict[m.group(2)]
                focus_dict[(uid, pid)] = (m.group(3), m.group(4))
        audio_status = {}
        uid_ = self.get_uid(package_name)
        # print(focus_dict)
        for (uid, pid), status in audio_status_dict.items():
            if uid != uid_:
                continue
            service_name = self.get_service_name(package_name, pid)
            if status == 'paused':
                if (uid, pid) not in focus_dict:
                    audio_status[service_name] = 'PAUSE'
                    continue
                if focus_dict[(uid, pid)][1] == 'LOSS_TRANSIENT':
                    audio_status[service_name] = 'PAUSE*'
                else:
                    audio_status[service_name] = 'PAUSE'
            if status == 'stopped' or status == 'idle':
                audio_status[service_name] = 'STOP'
            if status == 'started':
                if (uid, pid) not in focus_dict:
                    if started_count > 1:
                        audio_status[service_name] = 'START*'
                    else:
                        audio_status[service_name] = 'START'
                    continue
                if focus_dict[(uid, pid)][1] == 'LOSS_TRANSIENT_CAN_DUCK':
                    audio_status[service_name] = 'DUCK'
                else:
                    audio_status[service_name] = 'START'
        return audio_status

        # audio_line_re = re.compile(".*u/pid:(.*)/.*state:(.*) attr.*")
        # if audio_status_dict[self.get_uid(package_name)] == 'started':
        # return status

    def get_current_package(self):
        focus_lines = self.shell_grep("dumpsys window", "mCurrentFocus").splitlines()
        package_re = re.compile(".*u0 (.*)/.*")
        if len(focus_lines) > 0:
            for focus_line in focus_lines:
                m = package_re.match(focus_line)
                if m:
                    return m.group(1)
        return

    def get_current_activity(self):
        focus_lines = self.shell_grep("dumpsys window", "mCurrentFocus").splitlines()
        package_re = re.compile(".*u0 .*/(.*)}")
        if len(focus_lines) > 0 :
            for focus_line in focus_lines:
                m = package_re.match(focus_line)
                if m:
                    return m.group(1)
        return

    def get_property(self, property_name):
        """
        get the value of property
        @param property_name:
        @return:
        """
        return self.shell(["getprop", property_name])

    def get_sdk_version(self):
        return int(self.get_property("ro.build.version.sdk"))
    
    def get_display_info(self):
        """
        Gets C{mDefaultViewport} and then C{deviceWidth} and C{deviceHeight} values from dumpsys.
        This is a method to obtain display dimensions and density
        """
        display_info = {}
        logical_display_re = re.compile(".*DisplayViewport{valid=true, .*orientation=(?P<orientation>\d+),"
                                        " .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+).*")
        dumpsys_display_result = self.shell("dumpsys display")
        if dumpsys_display_result is not None:
            for line in dumpsys_display_result.splitlines():
                m = logical_display_re.search(line, 0)
                if m:
                    for prop in ['width', 'height', 'orientation']:
                        display_info[prop] = int(m.group(prop))

        if 'width' not in display_info or 'height' not in display_info:
            physical_display_re = re.compile('Physical size: (?P<width>\d+)x(?P<height>\d+)')
            m = physical_display_re.search(self.shell('wm size'))
            if m:
                for prop in ['width', 'height']:
                    display_info[prop] = int(m.group(prop))

        if 'width' not in display_info or 'height' not in display_info:
            # This could also be mSystem or mOverscanScreen
            display_re = re.compile('\s*mUnrestrictedScreen=\((?P<x>\d+),(?P<y>\d+)\) (?P<width>\d+)x(?P<height>\d+)')
            # This is known to work on older versions (i.e. API 10) where mrestrictedScreen is not available
            display_width_height_re = re.compile('\s*DisplayWidth=(?P<width>\d+) *DisplayHeight=(?P<height>\d+)')
            for line in self.shell('dumpsys window').splitlines():
                m = display_re.search(line, 0)
                if not m:
                    m = display_width_height_re.search(line, 0)
                if m:
                    for prop in ['width', 'height']:
                        display_info[prop] = int(m.group(prop))

        if 'orientation' not in display_info:
            surface_orientation_re = re.compile("SurfaceOrientation:\s+(\d+)")
            output = self.shell("dumpsys input")
            m = surface_orientation_re.search(output)
            if m:
                display_info['orientation'] = int(m.group(1))

        display_info_keys = {'width', 'height', 'orientation'}
        if not display_info_keys.issuperset(display_info):
            logger.warning("getDisplayInfo failed to get: %s" % display_info_keys)
        return display_info
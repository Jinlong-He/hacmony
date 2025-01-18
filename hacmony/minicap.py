import socket
import sys
import time
import subprocess
from datetime import datetime
import os
from loguru import logger

MINICAP_REMOTE_ADDR = "localabstract:minicap"

class MinicapException(Exception):
    """
    Exception in minicap connection
    """
    pass

class Minicap(object):
    def __init__(self, device):
        self.host = "localhost"

        self.device = device
        # self.port = self.device.get_random_port()

        self.remote_minicap_path = "/data/local/tmp/minicap"
        self.port = self.device.get_random_port()

        self.sock = None
        self.connected = False
        self.minicap_process = None
        self.listen_thread = None
        self.banner = None
        self.width = -1
        self.height = -1
        self.orientation = -1

        self.last_screen = None
        self.last_screen_time = None
        self.last_views = []
        # self.last_rotation_check_time = datetime.now()

    def set_up(self):
        device = self.device

        try:
            minicap_files = device.adb.shell("ls %s 2>/dev/null" % self.remote_minicap_path).split()
            if "minicap.so" in minicap_files and ("minicap" in minicap_files or "minicap-nopie" in minicap_files):
                logger.debug("minicap was already installed.")
                return
        except:
            pass

        if device is not None:
            # install minicap
            import pkg_resources
            local_minicap_path = pkg_resources.resource_filename("h2mony", "resources/minicap")
            try:
                device.adb.shell("mkdir %s" % self.remote_minicap_path)
            except Exception:
                pass
            abi = device.adb.get_property('ro.product.cpu.abi')
            sdk = device.get_sdk_version()
            if sdk >= 16:
                minicap_bin = "minicap"
            else:
                minicap_bin = "minicap-nopie"
            minicap_bin_path = os.path.join(local_minicap_path, 'libs', abi, minicap_bin)
            device.push_file(local_file=minicap_bin_path, remote_dir=self.remote_minicap_path)
            minicap_so_path = os.path.join(local_minicap_path, 'jni', 'libs', f'android-{sdk}', abi, 'minicap.so')
            device.push_file(local_file=minicap_so_path, remote_dir=self.remote_minicap_path)
            logger.debug("minicap installed.")

    def connect(self):
        device = self.device
        display = device.get_display_info(refresh=True)
        if 'width' not in display or 'height' not in display or 'orientation' not in display:
            logger.warning("Cannot get the size of current device.")
            return
        w = display['width']
        h = display['height']
        if w > h:
            temp = w
            w = h
            h = temp
        o = display['orientation'] * 90
        self.width = w
        self.height = h
        self.orientation = o

        size_opt = "%dx%d@%dx%d/%d" % (w, h, w, h, o)
        grant_minicap_perm_cmd = "adb -s %s shell chmod -R a+x %s" % \
                                 (device.serial, self.remote_minicap_path)
        start_minicap_cmd = "adb -s %s shell LD_LIBRARY_PATH=%s %s/minicap -P %s" % \
                            (device.serial, self.remote_minicap_path, self.remote_minicap_path, size_opt)
        logger.debug("starting minicap: " + start_minicap_cmd)

        p = subprocess.Popen(grant_minicap_perm_cmd.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = p.communicate()

        self.minicap_process = subprocess.Popen(start_minicap_cmd.split(),
                                                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        # Wait 2 seconds for starting minicap
        time.sleep(2)
        logger.debug("minicap started.")
        try:
            forward_cmd = "adb -s %s forward tcp:%d %s" % (device.serial, self.port, MINICAP_REMOTE_ADDR)
            subprocess.check_call(forward_cmd.split())
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            import threading
            self.listen_thread = threading.Thread(target=self.listen)
            self.listen_thread.start()
            # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as e:
            self.connected = False
            logger.warning(e)
            raise MinicapException()

    def disconnect(self):
        """
        disconnect telnet
        """
        self.connected = False
        self.listen_thread.join()
        if self.sock is not None:
            try:
                self.sock.close()
            except Exception as e:
                print(e)
        if self.minicap_process is not None:
            try:
                self.minicap_process.terminate()
            except Exception as e:
                print(e)
        try:
            forward_remove_cmd = "adb -s %s forward --remove tcp:%d" % (self.device.serial, self.port)
            p = subprocess.Popen(forward_remove_cmd.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = p.communicate()
        except Exception as e:
            print(e)

    def listen(self):
        CHUNK_SIZE = 4096
        read_banner_bytes = 0
        banner_length = 24
        read_frame_bytes = 0
        frame_body_length = 0
        frame_body = bytearray()
        banner = {
            "version": 0,
            "length": 0,
            "pid": 0,
            "realWidth": 0,
            "realHeight": 0,
            "virtualWidth": 0,
            "virtualHeight": 0,
            "orientation": 0,
            "quirks": 0,
        }
        self.connected = True
        while self.connected:
            chunk = self.sock.recv(CHUNK_SIZE)
            if not chunk:
                continue
            cursor = 0
            buf_len = len(chunk)
            while cursor < buf_len:
                if read_banner_bytes < banner_length:
                    if read_banner_bytes == 0:
                        banner['version'] = chunk[cursor]
                    elif read_banner_bytes == 1:
                        banner['length'] = banner_length = chunk[cursor]
                    elif 2 <= read_banner_bytes <= 5:
                        banner['pid'] += (chunk[cursor] << ((read_banner_bytes - 2) * 8))
                    elif 6 <= read_banner_bytes <= 9:
                        banner['realWidth'] += (chunk[cursor] << ((read_banner_bytes - 6) * 8))
                    elif 10 <= read_banner_bytes <= 13:
                        banner['realHeight'] += (chunk[cursor] << ((read_banner_bytes - 10) * 8))
                    elif 14 <= read_banner_bytes <= 17:
                        banner['virtualWidth'] += (chunk[cursor] << ((read_banner_bytes - 14) * 8))
                    elif 18 <= read_banner_bytes <= 21:
                        banner['virtualHeight'] += (chunk[cursor] << ((read_banner_bytes - 18) * 8))
                    elif read_banner_bytes == 22:
                        banner['orientation'] += chunk[cursor] * 90
                    elif read_banner_bytes == 23:
                        banner['quirks'] = chunk[cursor]

                    cursor += 1
                    read_banner_bytes += 1
                    if read_banner_bytes == banner_length:
                        self.banner = banner
                        logger.debug("minicap initialized: %s" % banner)

                elif read_frame_bytes < 4:
                    frame_body_length += (chunk[cursor] << (read_frame_bytes * 8))
                    cursor += 1
                    read_frame_bytes += 1
                else:
                    if buf_len - cursor >= frame_body_length:
                        frame_body += chunk[cursor: cursor + frame_body_length]
                        self.handle_image(frame_body)
                        cursor += frame_body_length
                        frame_body_length = read_frame_bytes = 0
                        frame_body = bytearray()
                    else:
                        frame_body += chunk[cursor:]
                        frame_body_length -= buf_len - cursor
                        read_frame_bytes += buf_len - cursor
                        cursor = buf_len 


    def handle_image(self, frame_body):
        if frame_body[0] != 0xFF or frame_body[1] != 0xD8:
            logger.warning("Frame body does not start with JPG header")
        self.last_screen = frame_body
        self.last_screen_time = datetime.now()
        self.last_views = None
        # import cv
        # img = cv.load_image_from_buf(self.last_screen)
        # cv2.imwrite('xxx.jpg', img)
        logger.debug("Received an image at %s" % self.last_screen_time)
    
    def get_play_coordinates(self):
        if not self.last_screen:
            logger.warning("last_screen is None")
            return None
        if self.last_views:
            return self.last_views

        import cv
        coors = cv.get_play_coordinates(self.last_screen)
        return coors
    
    def get_view_imgs(self, bounds):
        if not self.last_screen:
            logger.warning("last_screen is None")
            return None
        if self.last_views:
            return self.last_views

        import cv
        img = cv.load_image_from_buf(self.last_screen)
        imgs = []
        for x,y,w,h in bounds:
            view = img[y:y+h, x:x+w]
            imgs.append(view)
        # self.last_views = views
        return imgs
    
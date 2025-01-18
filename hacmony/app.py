import os
import sys
from loguru import logger
from androguard.core.apk import APK

class App(object):
    """
    this class describes an app
    """

    def __init__(self, device, app_path=''):
        """
        create an App instance
        :param app_path: local file path of app
        :return:
        """
        assert app_path is not None
        logger.disable('androguard.core')

        self.app_path = app_path
        if app_path == '':
            self.package_name = device.adb.get_current_package()
            return

        self.apk = APK(self.app_path)
        self.package_name = self.apk.get_package()
        self.app_name = self.apk.get_app_name()
        self.main_activity = self.apk.get_main_activity()
        self.permissions = self.apk.get_permissions()
        self.activities = self.apk.get_activities()
        self.dumpsys_main_activity = None

    def get_package_name(self):
        """
        get package name of current app
        :return:
        """
        return self.package_name

    def get_main_activity(self):
        """
        get package name of current app
        :return:
        """
        if self.main_activity is not None:
            return self.main_activity
        else:
            logger.warning("Cannot get main activity from manifest. Using dumpsys result instead.")
            return self.dumpsys_main_activity

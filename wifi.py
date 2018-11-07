import subprocess

class Wifi:

    def is_wifi_active(self):

        iwconfig_out = subprocess.check_output(['iwconfig']).decode('utf-8')
        wifi_active = True
        if "Access Point: Not-Associated" in iwconfig_out:
            wifi_active = False
        return wifi_active

    def set_enter_apmode_flag():

        pass

    @property
    def EnterApModeFlag(self):
        flag = True
        return flag
    @EnterApModeFlag.setter
    def EnterApModeFlag(self, flag):
        return flag

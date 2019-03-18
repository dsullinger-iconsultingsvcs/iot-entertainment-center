#!/usr/bin/python
import json
import time
import cec

power_state = {
    0: "on",
    1: "standby",
    2: "transition_on",
    3: "transition_standby"
}

class EntertainmentCenter:
    def __init__(self):
        cec.init()
        device_list = cec.list_devices()
        for dev in device_list:
            print(device_list[dev].osd_string)
        self.television = None
        if 0 in device_list:
            self.television = { "address": "0",
                    "powerState": "standby"
                    }
        self.receiver = None
        if 5 in device_list:
            self.receiver = { "address": "5",
                     "powerState": "standby",
                     "mute": False,
                     "volume": None
                    }
        self.acquire_all_status()

    def get_volume_info(self, vol):
        mute = int(vol / 128)
        muted = (mute == 1)
        level = vol % 128
        return {"muted":muted,"volume":level}

    def broadcast_power_on(self):
        broadcast = cec.Device(cec.CECDEVICE_BROADCAST)
        broadcast.power_on()
        return

    def broadcast_power_off(self):
        broadcast = cec.Device(cec.CECDEVICE_BROADCAST)
        broadcast.standby()
        self.acquire_all_status()

    def acquire_all_status(self):
        self.acquire_television_status()
        self.acquire_receiver_status()
        return
    
    def acquire_television_status(self):
        if self.television is not None:
            power_info = power_state[cec.power_status(0)]

            self.television["powerState"] = power_info
        return
    
    def acquire_receiver_status(self):
        if self.receiver is not None:
            power_info = power_state[cec.power_status(5)]
            self.receiver["powerState"] = power_info
            if power_info == "on":
                volume_info = self.get_volume_info(cec.audio_status(True))
                self.receiver["mute"] = volume_info["muted"]
                self.receiver["volume"] = volume_info["volume"]
        return

    def set_receiver_status(self, power_state=None, mute=None, volume=None, receiver_state=None):
        if self.receiver is None:
            return
        if receiver_state != None:
            if "powerState" in receiver_state:
                power_state = receiver_state["powerState"]
            if "mute" in receiver_state:
                mute = receiver_state["mute"]
            if "volume" in receiver_state:
                volume = receiver_state["volume"]
        if power_state != None and power_state != "standby" and power_state != "on":
            raise Exception("Valid power_state values are 'standby' or 'on' (%s given)" % power_state)
        self.acquire_receiver_status()
        if power_state != None and power_state != self.receiver["powerState"]:
            receiver = cec.Device(cec.CECDEVICE_AUDIOSYSTEM)
            if power_state == "standby":
                receiver.standby()
            else:
                receiver.power_on()
            self.receiver["powerState"] = power_state
        if mute != None and mute != self.receiver["mute"]:
            if mute:
                cec.toggle_mute()
            else:
                cec.toggle_mute()
            self.receiver["mute"] = mute
        if volume != None and self.receiver["volume"] != None and \
          volume != self.receiver["volume"] and volume != -1:
            if volume < self.receiver["volume"]:
                while volume < self.receiver["volume"]:
                    self.receiver["volume"] = self.get_volume_info(cec.volume_down())["volume"]
            if volume > self.receiver["volume"]:
                while volume > self.receiver["volume"]:
                    self.receiver["volume"] = self.get_volume_info(cec.volume_up())["volume"]
        return
    
    def set_television_status(self, power_state=None, television_state=None):
        if self.television is None:
            return
        if television_state != None and "powerState" in television_state:
            power_state = television_state["powerState"]
        if power_state != None and power_state != "standby" and power_state != "on":
            raise Exception("Valid power_state values are 'standby' or 'on' (%s given)" % power_state)
        self.acquire_television_status()
        if power_state != None and power_state != self.television["powerState"]:
            tv = cec.Device(cec.CECDEVICE_TV)
            if power_state == "standby":
                print("TV Standby")
                tv.standby()
            else:
                print("TV Power On")
                tv.power_on()
            self.television["powerState"] = power_state
        return

    def get_status(self):
        self.acquire_all_status()
        status_doc = {}
        if self.television is not None:
            status_doc["television"] = self.television
        if self.receiver is not None:
            status_doc["receiver"] = self.receiver
        return json.dumps(status_doc)

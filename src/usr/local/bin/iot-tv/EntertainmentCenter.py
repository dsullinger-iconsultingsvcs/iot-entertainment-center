#!/usr/bin/python
import json
import time
import cec
import ssdp
import http.client
import RokuDevice

power_state = {
    0: "on",
    1: "standby",
    2: "transition_on",
    3: "transition_standby"
}

class EntertainmentCenter:
    def __init__(self, config=None):
        cec.init()
        device_list = cec.list_devices()
        self.roku_dev = None
        for dev in device_list:
            print(device_list[dev].osd_string)
            if device_list[dev].osd_string == 'Roku' and 'rokuName' in config:
                print("Finding address for Roku %s" % config['rokuName'])
                all_devices = RokuDevice.RokuDevices()
                try:
                    self.roku_dev = all_devices.get_device(config['rokuName'])
                except:
                    print("Did not find Roku Device %s" % config['rokuName'])
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
        if self.roku_dev is not None:
            self.roku_dev.keypress('Home')
        broadcast = cec.Device(cec.CECDEVICE_BROADCAST)
        broadcast.standby()
        self.acquire_all_status()

    def acquire_all_status(self):
        self.acquire_television_status()
        self.acquire_receiver_status()
        return
    
    def acquire_television_status(self):
        if self.television is not None:
            try:
                power_info = power_state[cec.power_status(0)]

                self.television["powerState"] = power_info
            except:
                self.television["powerState"] = 'exception'
        return
    
    def acquire_receiver_status(self):
        if self.receiver is not None:
            try:
                power_info = power_state[cec.power_status(5)]
                self.receiver["powerState"] = power_info
                if power_info == "on":
                    try:
                        volume_info = self.get_volume_info(cec.audio_status(True))
                        self.receiver["mute"] = volume_info["muted"]
                        self.receiver["volume"] = volume_info["volume"]
                    except:
                        self.receiver["mute"] = None
                        self.receiver["volume"] = None
            except:
                self.receiver["powerState"] = 'exception'
                self.receiver["mute"] = None
                self.receiver["volume"] = None
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
            retry_count = 0
            if power_state == "standby":
                while retry_count < 5:
                    try:
                        receiver.standby()
                        break
                    except:
                        print("Error setting audio system power state to standby")
                        retry_count += 1
                        print("retrying %d" % retry_count)
            else:
                while retry_count < 5:
                    try:
                        receiver.power_on()
                        break
                    except:
                        print("Error setting audio system power state to on")
                        retry_count += 1
                        print("retrying %d" % retry_count)
            self.receiver["powerState"] = power_state
        if mute != None and mute != self.receiver["mute"]:
            retry_count = 0
            if mute:
                while retry_count < 5:
                    try:
                        cec.toggle_mute()
                        break
                    except:
                        print("Error setting audio system mute")
                        retry_count += 1
                        print("retrying %d" % retry_count)
            else:
                while retry_count < 5:
                    try:
                        cec.toggle_mute()
                        break
                    except:
                        print("Error setting audio system mute (first)")
                        retry_count += 1
                        print("retrying %d" % retry_count)
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
                if self.roku_dev is not None:
                    self.roku_dev.keypress('Home')
                print("TV Standby")
                retry_count = 0
                while retry_count < 5:
                    try:
                        tv.standby()
                        break
                    except:
                        print("Exception with TV Standby")
                        retry_count += 1
                        print("Retrying %d" % retry_count)
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

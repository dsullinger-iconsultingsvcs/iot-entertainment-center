import json
from uuid import uuid4
import time
import boto3

iot_client = boto3.client('iot-data', region_name='us-east-1')


# Get a UUID
def unique_id():
    return str(uuid4())


# get the current timestamp in UTC
def utc_timestamp():
    return time.strftime("%Y-%m-%dT%H:%M:%S.00Z", time.gmtime())


class IoTEntertainmentCenter:
    def __init__(self, thing_name='Entertainment-Center'):
        self.thing_name = thing_name
        self.acquire_status()

    def get_tv_power(self):
        self.acquire_status()
        return self.current_status['television']['powerState']

    def set_tv_power(self, state):
        state = str(state).lower()
        if state != 'on':
            state = 'standby'
        self.current_status['television']['powerState'] = state
        self.update_device()

    def get_receiver_power(self):
        self.acquire_status()
        return self.current_status['receiver']['powerState']

    def set_receiver_power(self, state):
        state = str(state).lower()
        if state != 'on':
            state = 'standby'
        self.current_status['receiver']['powerState'] = state
        self.update_device()

    def get_receiver_mute(self):
        self.acquire_status()
        if 'mute' in self.current_status['receiver']:
            return self.current_status['receiver']['mute']
        else:
            return False

    def set_receiver_mute(self, mute):
        self.current_status['receiver']['mute'] = mute
        self.update_device()

    def get_receiver_volume(self):
        self.acquire_status()
        if 'volume' in self.current_status['receiver']:
            return self.current_status['receiver']['volume']
        else:
            return -1

    def set_receiver_volume(self, volume):
        self.current_status['receiver']['volume'] = volume
        self.update_device()

    def acquire_status(self):
        response = iot_client.get_thing_shadow(
            thingName=self.thing_name
        )
        streamingBody = response["payload"]
        jsonState = json.loads(streamingBody.read())
        if 'reported' in jsonState['state']:
            self.current_status = \
                jsonState['state']['reported']['EntertainmentCenter']
        else:
            self.current_status = \
                jsonState['state']['desired']['EntertainmentCenter']
        if 'mute' not in self.current_status['receiver']:
            self.current_status['receiver']['mute'] = False
        if 'volume' not in self.current_status['receiver']:
            self.current_status['receiver']['volume'] = -1

    def update_device(self):
        tv_state = self.current_status['television']
        receiver_state = self.current_status['receiver']
        shadow_data = {
            "state": {
                "desired": {
                    "EntertainmentCenter": {
                        "television": {
                            "powerState": tv_state['powerState'],
                            "address": tv_state['address']
                        },
                        "receiver": {
                            "mute": receiver_state['mute'],
                            "powerState": receiver_state['powerState'],
                            "address": receiver_state['address'],
                            "volume": receiver_state['volume']
                        }
                    },
                    "counter": int(time.time())
                }
            }
        }
        iot_client.update_thing_shadow(thingName=self.thing_name,
                                       payload=json.dumps(shadow_data))

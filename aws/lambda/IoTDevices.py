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

def get_all_things():
    iot = boto3.client('iot', region_name='us-east-1')
    return_things = []
    thing_list = iot.list_things(maxResults=50, 
                                thingTypeName='Entertainment-Center')
    while 'things' in thing_list:
        for thing in thing_list['things']:
            return_things.append(thing)
        if 'nextToken' in thing_list:
            thing_list = iot.list_things(nextToken=thing_list['nextToken'],
                                        maxResults=50,
                                        thingTypeName='Entertainment-Center')
        else:
            break
    return return_things


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
        
    def receiver_exists(self):
        return 'receiver' in self.current_status

    def get_receiver_power(self):
        self.acquire_status()
        if self.receiver_exists():
            return self.current_status['receiver']['powerState']
        else:
            return 'standby'

    def set_receiver_power(self, state):
        if self.receiver_exists():
            state = str(state).lower()
            if state != 'on':
                state = 'standby'
            self.current_status['receiver']['powerState'] = state
            self.update_device()

    def get_receiver_mute(self):
        self.acquire_status()
        if self.receiver_exists():
            if 'mute' in self.current_status['receiver']:
                return self.current_status['receiver']['mute']
            else:
                return False
        return False

    def set_receiver_mute(self, mute):
        if self.receiver_exists():
            self.current_status['receiver']['mute'] = mute
            self.update_device()

    def get_receiver_volume(self):
        self.acquire_status()
        if self.receiver_exists():
            if 'volume' in self.current_status['receiver']:
                return self.current_status['receiver']['volume']
            else:
                return -1
        else:
            return -1

    def set_receiver_volume(self, volume):
        if self.receiver_exists():
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
        if 'receiver' in self.current_status:
            if 'mute' not in self.current_status['receiver']:
                self.current_status['receiver']['mute'] = False
            if 'volume' not in self.current_status['receiver']:
                self.current_status['receiver']['volume'] = -1

    def update_device(self):
        tv_state = self.current_status['television']
        shadow_data = {
            "state": {
                "desired": {
                    "EntertainmentCenter": {
                        "television": {
                            "powerState": tv_state['powerState'],
                            "address": tv_state['address']
                        }
                    },
                    "counter": int(time.time())
                }
            }
        }
        if self.receiver_exists():
            receiver_state = self.current_status['receiver']
            shadow_data['state']['desired']['EntertainmentCenter']['receiver'] = \
                 {
                    "mute": receiver_state['mute'],
                    "powerState": receiver_state['powerState'],
                    "address": receiver_state['address'],
                    "volume": receiver_state['volume']
                 }
        iot_client.update_thing_shadow(thingName=self.thing_name,
                                       payload=json.dumps(shadow_data))

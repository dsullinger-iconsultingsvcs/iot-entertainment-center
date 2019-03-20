import json
import time
import copy


def utc_timestamp():
    return time.strftime("%Y-%m-%dT%H:%M:%S.00Z", time.gmtime())


def response_event(name, header, endpoint):
    event = {
                "header": {
                    "namespace": "Alexa",
                    "name": name,
                    "payloadVersion": "3",
                    "messageId": header["messageId"],
                    "correlationToken": header["correlationToken"]
                },
                "endpoint": {
                    "scope": {
                        "type": "BearerToken",
                        "token": endpoint["scope"]["token"]
                    },
                    "endpointId": endpoint["endpointId"]
                }
            }
    return event


def resolve_response_name(header):
    name = "Response"
    if header["namespace"] == "Alexa" and header["name"] == "ReportState":
        name = "StateReport"
    return name


class AlexaEntertainmentCenter:
    def __init__(self, capabilities=[], endpoint_id="Entertainment-Center",
                 manufacturer="Various", friendly_name="Entertainment Center",
                 description="Home Entertainment Center",
                 display_categories=["TV"]):
        self.capabilities = capabilities
        self.endpoint_id = endpoint_id
        self.manufacturer = manufacturer
        self.friendly_name = friendly_name
        self.description = description
        self.display_categories = display_categories

    def discovery(self, registered_things):
        endpoint_list = []
        endpoint = {
                "endpointId": self.endpoint_id,
                "manufacturerName": self.manufacturer,
                "friendlyName": self.friendly_name,
                "description": self.description,
                "displayCategories": self.display_categories,
                "capabilities": []
            }
        for capability in self.capabilities:
            endpoint["capabilities"].append(capability.discovery())
        for thing in registered_things:
            endpoint["endpointId"] = thing["thingName"]
            endpoint["friendlyName"] = thing["thingName"]
            endpoint_list.append(copy.deepcopy(endpoint))
        return endpoint_list

    def discovery_json(self):
        return json.dumps(self.discovery, indent=4, sort_keys=True)

    def response(self, header, endpoint):
        name = resolve_response_name(header)
        response_properties = []
        for capability in self.capabilities:
            response_properties.append(capability.response_properties())
        pass
        response_data = {
            "context": {
                "properties": response_properties
            },
            "event": response_event(name, header, endpoint),
            "payload": {}
        }
        return response_data


class AlexaPowerController:
    def __init__(self, power_state=None):
        self.set_power_state(power_state)

    def set_power_state(self, power_state):
        if str(power_state).upper != 'ON':
            power_state = 'OFF'
        self.power_state = str(power_state).upper()

    def get_power_state(self):
        return self.power_state

    def turn_on(self):
        self.set_power_state('ON')

    def turn_off(self):
        self.set_power_state('OFF')

    def discovery(self):
        capability = {
            "type": "AlexaInterface",
            "interface": "Alexa.PowerController",
            "version": "3",
            "properties": {
                "supported": [
                    {
                        "name": "powerState"
                    }
                ],
                "proactivelyReported": False,
                "retrievable": True
            }
            }
        return capability

    def take_action(self, header, payload):
        if header['name'] == "TurnOn":
            self.turn_on()
        elif header['name'] == "TurnOff":
            self.turn_off()

    def response(self, header, endpoint):
        name = resolve_response_name(header)
        response_data = {
            "context": {
                "properties": self.response_properties()
            },
            "event": response_event(name, header, endpoint),
            "payload": {}
        }
        return response_data

    def response_properties(self):
        if self.power_state is None:
            raise Exception('set power_state before responding')
        properties = [{
                    "namespace": "Alexa.PowerController",
                    "name": "powerState",
                    "value": self.power_state,
                    "timeOfSample": utc_timestamp(),
                    "uncertaintyInMilliseconds": 500
                }]
        return properties


class AlexaSpeaker:
    def __init__(self, muted=None, volume=None):
        self.set_muted(muted)
        self.set_volume(volume)

    def set_muted(self, muted):
        self.muted = muted

    def get_muted(self):
        return self.muted

    def mute_on(self):
        self.set_muted(True)

    def mute_off(self):
        self.set_muted(False)

    def set_volume(self, volume):
        self.volume = volume

    def get_volume(self):
        return self.volume

    def adjust_volume(self, amount):
        if self.volume is None:
            raise Exception('Set the volume before adjusting')
        if amount < 0:
            self.set_volume(self.get_volume() - amount)
        else:
            self.set_volume(self.get_volume() + amount)

    def discovery(self):
        capability = {
            "type": "AlexaInterface",
            "interface": "Alexa.Speaker",
            "version": "3",
            "properties": {
                "supported": [
                    {
                        "name": "muted"
                    },
                    {
                        "name": "volume"
                    }
                ],
                "proactivelyReported": False,
                "retrievable": True
            }
        }
        return capability

    def take_action(self, header, payload):
        if header['name'] == "SetVolume":
            self.set_volume(payload['volume'])
        elif header['name'] == "AdjustVolume":
            self.adjust_volume(payload['volume'])
        elif header['name'] == "SetMute":
            self.set_muted(payload['mute'])

    def response(self, header, endpoint):
        name = resolve_response_name(header)
        response = {
            "context": {
                "properties": self.response_properties()
            },
            "event": response_event(name, header, endpoint)
        }
        return response

    def response_properties(self):
        if self.muted is None:
            raise Exception('Set muted property before responding')
        if self.volume is None:
            raise Exception('set volume property before responding')
        properties = [{
                    "namespace": "Alexa.Speaker",
                    "name": "muted",
                    "value": self.muted,
                    "timeOfSample": utc_timestamp(),
                    "uncertaintyInMilliseconds": 500
                }, {
                    "namespace": "Alexa.Speaker",
                    "name": "volume",
                    "value": self.volume,
                    "timeOfSample": utc_timestamp(),
                    "uncertaintyInMilliseconds": 500
                }]
        return properties

# -*- coding: utf-8 -*-

import json
from uuid import uuid4
import time
import random
import boto3
import AlexaDevices
import IoTDevices

iot_client = boto3.client('iot-data', region_name='us-east-1')


# Get a UUID
def unique_id():
    return str(uuid4())


# get the current timestamp in UTC
def utc_timestamp():
    return time.strftime("%Y-%m-%dT%H:%M:%S.00Z", time.gmtime())


def lambda_handler(event, context):
    print(json.dumps(event))
    header = {}
    endpoint = {}
    payload = {}
    if 'header' in event['directive']:
        header = event["directive"]["header"]
    if 'endpoint' in event['directive']:
        endpoint = event["directive"]["endpoint"]
    if 'payload' in event['directive']:
        payload = event["directive"]["payload"]

    tv = AlexaDevices.AlexaPowerController(power_state='standby')
    receiver = AlexaDevices.AlexaSpeaker(
                    muted=False,
                    volume=-1)
    alexa_ent_center = AlexaDevices.AlexaEntertainmentCenter([tv, receiver])
    if "endpointId" in endpoint:
        iot_device = IoTDevices.IoTEntertainmentCenter(endpoint["endpointId"])
        tv.set_power_state(iot_device.get_tv_power())
        if iot_device.receiver_exists():
            receiver.set_muted(iot_device.get_receiver_mute())
            receiver.set_volume(iot_device.get_receiver_volume())
    if header["namespace"] == "Alexa.Discovery":
        if header["name"] == "Discover":
            endpoint_list = []
            all_things = IoTDevices.get_all_things()
            all_endpoints = alexa_ent_center.discovery(all_things)
            header["name"] = "Discover.Response"
            return_message = {
                "event": {
                    "header": header,
                    "payload": { "endpoints": all_endpoints }
                }
            }
            print(json.dumps(return_message))
            return return_message
    elif header["namespace"] == "Alexa.PowerController":
        return power_control(iot_device, tv, header, endpoint, payload)
    elif header["namespace"] == "Alexa.Speaker":
        return speaker_control(iot_device, receiver, header, endpoint, payload)
    elif header["namespace"] == "Alexa" and header["name"] == "ReportState":
        return alexa_ent_center.response(header, endpoint)

    # This request has not been implemented
    print('un supported request')
    return None


def power_control(iot_device, tv, header, endpoint, payload):
    if header['name'] == 'TurnOn':
        iot_device.set_tv_power('on')
    elif header['name'] == 'TurnOff':
        iot_device.set_tv_power('standby')
    tv.take_action(header, payload)
    return tv.response(header, endpoint)


def speaker_control(iot_device, receiver, header, endpoint, payload):
    if header['name'] == 'SetVolume':
        iot_device.set_receiver_volume(payload['volume'])
    elif header['name'] == 'AdjustVolume':
        start_vol = iot_device.get_receiver_volume()
        new_volume = start_vol + payload['volume']
        iot_device.set_receiver_volume(new_volume)
    elif header['name'] == 'SetMute':
        iot_device.set_receiver_mute(payload['mute'])
    receiver.take_action(header, payload)
    return receiver.response(header, endpoint)
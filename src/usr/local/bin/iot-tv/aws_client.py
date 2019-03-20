#!/usr/bin/env python3
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import json
import time
import subprocess
import EntertainmentCenter as EntCenter

def update_shadow(handler, state_data, counter_val=None):
    if counter_val is None:
        counter_val = int(time.time())
    base_state = '{"EntertainmentCenter": ' + state_data + ',"counter": %d}' % counter_val
    reported_state = '{"state":{"reported": %s,"desired": %s}}' % (base_state, base_state)
    print("%d: %s" % (counter_val, base_state))
    handler.shadowUpdate(reported_state, None, 5)

class callbackContainer:
    def __init__(self, shadow_instance):
        self.shadowInstance = shadow_instance

    def shadowCallback_Delta(self, payload, responseStatus, token):
        print("\n\n%s\n\n" % payload)
        print("Received a delta message:")
        payload_dict = json.loads(payload)
        request_counter = int(time.time())
        if "counter" in payload_dict["state"]:
            request_counter = payload_dict["state"]["counter"]
        if "EntertainmentCenter" in payload_dict["state"]:
            requested_state = payload_dict["state"]["EntertainmentCenter"]
            print("Requested State: " + json.dumps(requested_state))
            current_status = json.loads(ent_center.get_status())
            for device in requested_state:
                if device == "television":
                    ent_center.set_television_status(television_state=requested_state[device])
                elif device == "receiver":
                    ent_center.set_receiver_status(receiver_state=requested_state[device])
                else:
                    print("Unknown device %s in state" % device)
        update_shadow(self.shadowInstance, ent_center.get_status(), request_counter)

ent_center = EntCenter.EntertainmentCenter()
iot_tv_config = {}
with open('/etc/iot-tv/iot-tv.config') as conf:
    iot_tv_config = json.load(conf)
iot_client = AWSIoTMQTTShadowClient(iot_tv_config['shadowClient'])
iot_client.configureEndpoint(iot_tv_config['endpointHost'], iot_tv_config['endpointPort'])
cert_path = iot_tv_config['certPath']
root_cert = iot_tv_config['rootCACert']
cert_prefix = iot_tv_config['certPrefix']
iot_client.configureCredentials("%s/%s" % (cert_path, root_cert),
                                "%s/%s-private.pem.key" % (cert_path, cert_prefix),
                                "%s/%s-certificate.pem.crt" % (cert_path, cert_prefix))
iot_client.connect()

iot_handler = iot_client.createShadowHandlerWithName(iot_tv_config['shadowClient'], True)
iot_container_bot = callbackContainer(iot_handler)

last_status = ent_center.get_status()
update_shadow(iot_handler, last_status)

iot_handler.shadowRegisterDeltaCallback(iot_container_bot.shadowCallback_Delta)

counter = 0
while True:
    time.sleep(1)
    counter = counter + 1
    if counter % 5 == 0:
        current_status = ent_center.get_status()
        # print("current_status (%d): %s" % (int(time.time()),current_status))
        if last_status != current_status:
            update_shadow(iot_handler, current_status)
            last_status = current_status
        counter = 0

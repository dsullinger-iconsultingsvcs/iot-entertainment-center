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

iot_client = AWSIoTMQTTShadowClient("Entertainment-Center")
iot_client.configureEndpoint("a59arxnqr4t9k-ats.iot.us-east-1.amazonaws.com", 8883)
cert_path = "/home/pi/echo-certs"
iot_client.configureCredentials("%s/AmazonRootCA1.pem" % cert_path,
                                "%s/f6c3992e2b-private.pem.key" % cert_path,
                                "%s/f6c3992e2b-certificate.pem.crt" % cert_path)
iot_client.connect()

iot_handler = iot_client.createShadowHandlerWithName("Entertainment-Center", True)
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

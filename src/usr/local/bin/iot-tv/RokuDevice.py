import http.client
import ssdp
from xml.dom.minidom import parse
import xml.dom.minidom

class RokuDevice:
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.http_connection = http.client.HTTPConnection(address, port)
        self.get_device_info()

    def get_device_info(self):
        self.http_connection.request('GET', '/query/device-info')
        get_response = self.http_connection.getresponse()
        xml_data = get_response.read()
        DOMTree = xml.dom.minidom.parseString(xml_data)
        device_info = DOMTree.documentElement
        n = device_info.firstChild
        while n is not None:
            if not n.nodeName.startswith('#') and n.firstChild is not None:
                attr_name = n.nodeName.replace('-', '_')
                setattr(self, attr_name, n.firstChild.nodeValue)
            n = n.nextSibling

    def keypress(self, key):
        self.http_connection.request('POST', '/keypress/%s' % key)

class RokuDevices:
    # pylint: disable=no-member
    def __init__(self):
        devices = dict()
        ssdp_list = ssdp.discover("roku:ecp")
        for device in ssdp_list:
            addr_port = device.location.split('/')[2]
            [addr, port] = addr_port.split(':')
            roku_dev = RokuDevice(addr, port)
            print("adding %s to list" % roku_dev.friendly_device_name)
            devices[roku_dev.friendly_device_name] = \
                roku_dev.friendly_device_name
        self.devices = devices
    
    def get_device(self, name):
        if name in self.devices:
            return self.devices[name]
        else:
            raise Exception('Name %s not found in the current list of devices' % name)
        


            
# The MIT License (MIT)
#
# Copyright (c) 2019 Dan Halbert for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_ble.services.standard.hid`
====================================================

BLE Human Interface Device (HID)

* Author(s): Dan Halbert for Adafruit Industries

"""
import struct

from micropython import const

import _bleio
from adafruit_ble.characteristics import Attribute
from adafruit_ble.characteristics import Characteristic
from adafruit_ble.characteristics.int import Uint8Characteristic
from adafruit_ble.uuid import StandardUUID

from ..core import Service

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE.git"

_HID_SERVICE_UUID_NUM = const(0x1812)
_REPORT_UUID_NUM = const(0x2A4D)
_REPORT_MAP_UUID_NUM = const(0x2A4B)
_HID_INFORMATION_UUID_NUM = const(0x2A4A)
_HID_CONTROL_POINT_UUID_NUM = const(0x2A4C)
_REPORT_REF_DESCR_UUID_NUM = const(0x2908)
_REPORT_REF_DESCR_UUID = _bleio.UUID(_REPORT_REF_DESCR_UUID_NUM)
_PROTOCOL_MODE_UUID_NUM = const(0x2A4E)

_APPEARANCE_HID_KEYBOARD = const(961)
_APPEARANCE_HID_MOUSE = const(962)
_APPEARANCE_HID_JOYSTICK = const(963)
_APPEARANCE_HID_GAMEPAD = const(964)


# Boot keyboard and mouse not currently supported.
_BOOT_KEYBOARD_INPUT_REPORT_UUID_NUM = const(0x2A22)
_BOOT_KEYBOARD_OUTPUT_REPORT_UUID_NUM = const(0x2A32)
_BOOT_MOUSE_INPUT_REPORT_UUID_NUM = const(0x2A33)

# Output reports not currently implemented (e.g. LEDs on keyboard)
_REPORT_TYPE_INPUT = const(1)
_REPORT_TYPE_OUTPUT = const(2)

# Boot Protocol mode not currently implemented
_PROTOCOL_MODE_BOOT = b'\x00'
_PROTOCOL_MODE_REPORT = b'\x01'

class ReportIn:
    """A single HID report that transmits HID data into a client."""
    uuid = StandardUUID(0x24ad)
    def __init__(self, service, report_id, usage_page, usage, *, max_length):
        self._characteristic = _bleio.Characteristic.add_to_service(
            service.bleio_service,
            self.uuid.bleio_uuid,
            properties=Characteristic.READ | Characteristic.NOTIFY,
            read_perm=Attribute.ENCRYPT_NO_MITM, write_perm=Attribute.NO_ACCESS,
            max_length=max_length, fixed_length=True)
        self._report_id = report_id
        self.usage_page = usage_page
        self.usage = usage

        _bleio.Descriptor.add_to_characteristic(
            self._characteristic, _REPORT_REF_DESCR_UUID,
            read_perm=Attribute.ENCRYPT_NO_MITM, write_perm=Attribute.NO_ACCESS,
            initial_value=struct.pack('<BB', self._report_id, _REPORT_TYPE_INPUT))

    def send_report(self, report):
        """Send a report to the peers"""
        self._characteristic.value = report

class ReportOut:
    """A single HID report that receives HID data from a client."""
    uuid = StandardUUID(0x24ad)
    def __init__(self, service, report_id, usage_page, usage, *, max_length):
        self._characteristic = Characteristic.add_to_service(
            service.bleio_service,
            self.uuid.bleio_uuid,
            max_length=max_length,
            fixed_length=True,
            properties=(Characteristic.READ | Characteristic.WRITE |
                        Characteristic.WRITE_NO_RESPONSE),
            read_perm=Attribute.ENCRYPT_NO_MITM, write_perm=Attribute.ENCRYPT_NO_MITM
        )
        self._report_id = report_id
        self.usage_page = usage_page
        self.usage = usage

        _bleio.Descriptor.add_to_characteristic(
            self._characteristic, _REPORT_REF_DESCR_UUID,
            read_perm=Attribute.ENCRYPT_NO_MITM, write_perm=Attribute.NO_ACCESS,
            initial_value=struct.pack('<BB', self._report_id, _REPORT_TYPE_OUTPUT))

_ITEM_TYPE_MAIN = const(0)
_ITEM_TYPE_GLOBAL = const(1)
_ITEM_TYPE_LOCAL = const(2)

_MAIN_ITEM_TAG_START_COLLECTION = const(0b1010)
_MAIN_ITEM_TAG_END_COLLECTION = const(0b1100)
_MAIN_ITEM_TAG_INPUT = const(0b1000)
_MAIN_ITEM_TAG_OUTPUT = const(0b1001)
_MAIN_ITEM_TAG_FEATURE = const(0b1011)

class HIDService(Service):
    """
    Provide devices for HID over BLE.

    :param str hid_descriptor: USB HID descriptor that describes the structure of the reports. Known
        as the report map in BLE HID.

    Example::

        from adafruit_ble.hid_server import HIDServer

        hid = HIDServer()
    """
    uuid = StandardUUID(0x1812)
    default_field_name = "hid"

    boot_keyboard_in = Characteristic(uuid=StandardUUID(0x2A22),
                                      properties=(Characteristic.READ |
                                                  Characteristic.NOTIFY),
                                      read_perm=Attribute.ENCRYPT_NO_MITM,
                                      write_perm=Attribute.NO_ACCESS,
                                      max_length=8, fixed_length=True)

    boot_keyboard_out = Characteristic(uuid=StandardUUID(0x2A32),
                                       properties=(Characteristic.READ |
                                                   Characteristic.WRITE |
                                                   Characteristic.WRITE_NO_RESPONSE),
                                       read_perm=Attribute.ENCRYPT_NO_MITM,
                                       write_perm=Attribute.ENCRYPT_NO_MITM,
                                       max_length=1, fixed_length=True)

    protocol_mode = Uint8Characteristic(uuid=StandardUUID(0x2A4E),
                                        properties=(Characteristic.READ |
                                                    Characteristic.WRITE_NO_RESPONSE),
                                        read_perm=Attribute.OPEN,
                                        write_perm=Attribute.OPEN,
                                        initial_value=1, max_value=1)
    """Protocol mode: boot (0) or report (1)"""


    # bcdHID (version), bCountryCode (0 not localized), Flags: RemoteWake, NormallyConnectable
    # bcd1.1, country = 0, flag = normal connect
    # TODO: Make this a struct.
    hid_information = Characteristic(uuid=StandardUUID(0x2A4A),
                                     properties=Characteristic.READ,
                                     read_perm=Attribute.ENCRYPT_NO_MITM,
                                     write_perm=Attribute.NO_ACCESS,
                                     initial_value=b'\x01\x01\x00\x02')
    """Hid information including version, country code and flags."""

    report_map = Characteristic(uuid=StandardUUID(0x2A4B),
                                properties=Characteristic.READ,
                                read_perm=Attribute.ENCRYPT_NO_MITM,
                                write_perm=Attribute.NO_ACCESS,
                                fixed_length=True)
    """This is the USB HID descriptor (not to be confused with a BLE Descriptor). It describes
       which report characteristic are what."""

    suspended = Uint8Characteristic(uuid=StandardUUID(0x2A4C),
                                    properties=Characteristic.WRITE_NO_RESPONSE,
                                    read_perm=Attribute.NO_ACCESS,
                                    write_perm=Attribute.ENCRYPT_NO_MITM,
                                    max_value=1)
    """Controls whether the device should be suspended (0) or not (1)."""

    def __init__(self, hid_descriptor):
        super().__init__(report_map=hid_descriptor)
        self._init_devices()

    def _init_devices(self):
        # pylint: disable=too-many-branches,too-many-statements,too-many-locals
        self.devices = []
        hid_descriptor = self.report_map

        global_table = [None] * 10
        local_table = [None] * 3
        collections = []
        top_level_collections = []

        i = 0
        while i < len(hid_descriptor):
            b = hid_descriptor[i]
            tag = (b & 0xf0) >> 4
            _type = (b & 0b1100) >> 2
            size = b & 0b11
            size = 4 if size == 3 else size
            i += 1
            data = hid_descriptor[i:i+size]
            if _type == _ITEM_TYPE_GLOBAL:
                global_table[tag] = data
            elif _type == _ITEM_TYPE_MAIN:
                if tag == _MAIN_ITEM_TAG_START_COLLECTION:
                    collections.append({"type": data,
                                        "locals": list(local_table),
                                        "globals": list(global_table),
                                        "mains": []})
                elif tag == _MAIN_ITEM_TAG_END_COLLECTION:
                    collection = collections.pop()
                    # This is a top level collection if the collections list is now empty.
                    if not collections:
                        top_level_collections.append(collection)
                    else:
                        collections[-1]["mains"].append(collection)
                elif tag == _MAIN_ITEM_TAG_INPUT:
                    collections[-1]["mains"].append({"tag": "input",
                                                     "locals": list(local_table),
                                                     "globals": list(global_table)})
                elif tag == _MAIN_ITEM_TAG_OUTPUT:
                    collections[-1]["mains"].append({"tag": "output",
                                                     "locals": list(local_table),
                                                     "globals": list(global_table)})
                else:
                    raise RuntimeError("Unsupported main item in HID descriptor")
                local_table = [None] * 3
            else:
                local_table[tag] = data

            i += size

        def get_report_info(collection, reports):
            for main in collection["mains"]:
                if "type" in main:
                    get_report_info(main, reports)
                else:
                    report_size, report_id, report_count = [x[0] for x in main["globals"][7:10]]
                    if report_id not in reports:
                        reports[report_id] = {"input_size": 0, "output_size": 0}
                    if main["tag"] == "input":
                        reports[report_id]["input_size"] += report_size * report_count
                    elif main["tag"] == "output":
                        reports[report_id]["output_size"] += report_size * report_count


        for collection in top_level_collections:
            if collection["type"][0] != 1:
                raise NotImplementedError("Only Application top level collections supported.")
            usage_page = collection["globals"][0][0]
            usage = collection["locals"][0][0]
            reports = {}
            get_report_info(collection, reports)
            if len(reports) > 1:
                raise NotImplementedError("Only on report id per Application collection supported")

            report_id, report = list(reports.items())[0]
            output_size = report["output_size"]
            if output_size > 0:
                self.devices.append(ReportOut(self, report_id, usage_page, usage,
                                              max_length=output_size // 8))

            input_size = reports[report_id]["input_size"]
            if input_size > 0:
                self.devices.append(ReportIn(self, report_id, usage_page, usage,
                                             max_length=input_size // 8))


    @classmethod
    def from_remote_service(cls, remote_service):
        """Creates a HIDService from a remote service"""
        self = super(cls).from_remote_service(remote_service)
        self._init_devices() # pylint: disable=protected-access

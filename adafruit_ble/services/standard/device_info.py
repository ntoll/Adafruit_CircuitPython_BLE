# The MIT License (MIT)
#
# Copyright (c) 2019 Dan Halbert for Adafruit Industries
# Copyright (c) 2019 Scott Shawcroft for Adafruit Industries
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
`adafruit_ble`
====================================================

This module provides higher-level BLE (Bluetooth Low Energy) functionality,
building on the native `_bleio` module.

* Author(s): Dan Halbert for Adafruit Industries

Implementation Notes
--------------------

**Hardware:**

   Adafruit Feather nRF52840 Express <https://www.adafruit.com/product/4062>

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import binascii
import os
import sys
import microcontroller

from .. import Service
from ...uuid import StandardUUID
from ...characteristics.string import FixedStringCharacteristic

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE.git"

class DeviceInfoService(Service):
    """Device information"""
    uuid = StandardUUID(0x180a)
    default_field_name = "device_info"
    model_number = FixedStringCharacteristic(uuid=StandardUUID(0x2a24))
    serial_number = FixedStringCharacteristic(uuid=StandardUUID(0x2a25))
    firmware_revision = FixedStringCharacteristic(uuid=StandardUUID(0x2a26))
    hardware_revision = FixedStringCharacteristic(uuid=StandardUUID(0x2a27))
    software_revision = FixedStringCharacteristic(uuid=StandardUUID(0x2a28))
    manufacturer = FixedStringCharacteristic(uuid=StandardUUID(0x2a29))

    def __init__(self, *, manufacturer,
                 software_revision,
                 model_number=None,
                 serial_number=None,
                 firmware_revision=None):
        if model_number is None:
            model_number = sys.platform
        if serial_number is None:
            serial_number = binascii.hexlify(microcontroller.cpu.uid).decode('utf-8') # pylint: disable=no-member

        if firmware_revision is None:
            firmware_revision = os.uname().version
        super().__init__(manufacturer=manufacturer,
                         software_revision=software_revision,
                         model_number=model_number,
                         serial_number=serial_number,
                         firmware_revision=firmware_revision)

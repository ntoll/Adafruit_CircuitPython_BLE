# The MIT License (MIT)
#
# Copyright (c) 2018 Dan Halbert for Adafruit Industries
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
Advertising is the first phase of BLE where devices can broadcast
"""

import struct

def to_hex(seq):
    """Pretty prints a byte sequence as hex values."""
    return " ".join("{:02x}".format(v) for v in seq)

def to_bytes_literal(seq):
    """Prints a byte sequence as a Python bytes literal that only uses hex encoding."""
    return "b\"" + "".join("\\x{:02x}".format(v) for v in seq) + "\""

def decode_data(data, *, key_encoding="B"):
    """Helper which decodes length encoded structures into a dictionary with the given key
       encoding."""
    i = 0
    data_dict = {}
    key_size = struct.calcsize(key_encoding)
    while i < len(data):
        item_length = data[i]
        i += 1
        if item_length == 0:
            break
        key = struct.unpack_from(key_encoding, data, i)[0]
        value = data[i + key_size:i + item_length]
        if key in data_dict:
            if not isinstance(data_dict[key], list):
                data_dict[key] = [data_dict[key]]
            data_dict[key].append(value)
        else:
            data_dict[key] = value
        i += item_length
    return data_dict

def compute_length(data_dict, *, key_encoding="B"):
    """Computes the length of the encoded data dictionary."""
    value_size = 0
    for value in data_dict.values():
        if isinstance(value, list):
            for subv in value:
                value_size += len(subv)
        else:
            value_size += len(value)
    return len(data_dict) + len(data_dict) * struct.calcsize(key_encoding) + value_size

def encode_data(data_dict, *, key_encoding="B"):
    """Helper which encodes dictionaries into length encoded structures with the given key
       encoding."""
    length = compute_length(data_dict, key_encoding=key_encoding)
    data = bytearray(length)
    key_size = struct.calcsize(key_encoding)
    i = 0
    for key, value in data_dict.items():
        if isinstance(value, list):
            value = b"".join(value)
        item_length = key_size + len(value)
        struct.pack_into("B", data, i, item_length)
        struct.pack_into(key_encoding, data, i + 1, key)
        data[i + 1 + key_size: i + 1 + item_length] = bytes(value)
        i += 1 + item_length
    return data

class AdvertisingDataField:
    """Top level class for any descriptor classes that live in Advertisement or its subclasses."""

class AdvertisingFlag:
    """A single bit flag within an AdvertisingFlags object."""
    def __init__(self, bit_position):
        self._bitmask = 1 << bit_position

    def __get__(self, obj, cls):
        return (obj.flags & self._bitmask) != 0

    def __set__(self, obj, value):
        if value:
            obj.flags |= self._bitmask
        else:
            obj.flags &= ~self._bitmask

class AdvertisingFlags(AdvertisingDataField):
    """Standard advertising flags"""

    limited_discovery = AdvertisingFlag(0)
    """Discoverable only for a limited time period."""
    general_discovery = AdvertisingFlag(1)
    """Will advertise until discovered."""
    le_only = AdvertisingFlag(2)
    """BR/EDR not supported."""
    # BR/EDR flags not included here, since we don't support BR/EDR.

    def __init__(self, advertisement, advertising_data_type):
        self._advertisement = advertisement
        self._adt = advertising_data_type
        self.flags = None
        if self._adt in self._advertisement.data_dict:
            self.flags = self._advertisement.data_dict[self._adt][0]
        elif self._advertisement.mutable:
            self.flags = 0b110 # Default to General discovery and LE Only
        else:
            self.flags = 0

    def __len__(self):
        return 1

    def __bytes__(self):
        encoded = bytearray(1)
        encoded[0] = self.flags
        return encoded

    def __str__(self):
        parts = ["<AdvertisingFlags"]
        for attr in dir(self.__class__):
            attribute_instance = getattr(self.__class__, attr)
            if issubclass(attribute_instance.__class__, AdvertisingFlag):
                if getattr(self, attr):
                    parts.append(attr)
        parts.append(">")
        return " ".join(parts)

class String(AdvertisingDataField):
    """UTF-8 encoded string in an Advertisement.

       Not null terminated once encoded because length is always transmitted."""
    def __init__(self, *, advertising_data_type):
        self._adt = advertising_data_type

    def __get__(self, obj, cls):
        if self._adt not in obj.data_dict:
            return None
        return str(obj.data_dict[self._adt], "utf-8")

    def __set__(self, obj, value):
        obj.data_dict[self._adt] = value.encode("utf-8")

class Struct(AdvertisingDataField):
    """`struct` encoded data in an Advertisement."""
    def __init__(self, struct_format, *, advertising_data_type):
        self._format = struct_format
        self._adt = advertising_data_type

    def __get__(self, obj, cls):
        if self._adt not in obj.data_dict:
            return None
        return struct.unpack(self._format, obj.data_dict[self._adt])[0]

    def __set__(self, obj, value):
        obj.data_dict[self._adt] = struct.pack(self._format, value)


class LazyField(AdvertisingDataField):
    """Non-data descriptor useful for lazily binding a complex object to an advertisement object."""
    def __init__(self, cls, attribute_name, *, advertising_data_type, **kwargs):
        self._cls = cls
        self._attribute_name = attribute_name
        self._adt = advertising_data_type
        self._kwargs = kwargs

    def __get__(self, obj, cls):
        # Return None if our object is immutable and the data is not present.
        if not obj.mutable and self._adt not in obj.data_dict:
            return None
        bound_class = self._cls(obj, advertising_data_type=self._adt, **self._kwargs)
        setattr(obj, self._attribute_name, bound_class)
        obj.data_dict[self._adt] = bound_class
        return bound_class

    # TODO: Add __set_name__ support to CircuitPython so that we automatically tell the descriptor
    # instance the attribute name it has and the class it is on.

class Advertisement:
    """Core Advertisement type"""
    prefix = b"\x00" # This is an empty prefix and will match everything.
    flags = LazyField(AdvertisingFlags, "flags", advertising_data_type=0x01)
    short_name = String(advertising_data_type=0x08)
    """Short local device name (shortened to fit)."""
    complete_name = String(advertising_data_type=0x09)
    """Complete local device name."""
    tx_power = Struct("<b", advertising_data_type=0x0a)
    """Transmit power level"""
    # DEVICE_ID = 0x10
    # """Device identifier."""
    # SLAVE_CONN_INTERVAL_RANGE = 0x12
    # """Slave connection interval range."""
    # PUBLIC_TARGET_ADDRESS = 0x17
    # """Public target address."""
    # RANDOM_TARGET_ADDRESS = 0x18
    # """Random target address (chosen randomly)."""
    # APPEARANCE = 0x19
    # # self.add_field(AdvertisingPacket.APPEARANCE, struct.pack("<H", appearance))
    # """Appearance."""
    # DEVICE_ADDRESS = 0x1B
    # """LE Bluetooth device address."""
    # ROLE = 0x1C
    # """LE Role."""
    #
    # MAX_LEGACY_DATA_SIZE = 31
    # """Data size in a regular BLE packet."""

    def __init__(self):
        """Create an advertising packet.

        :param buf data: if not supplied (None), create an empty packet
          if supplied, create a packet with supplied data. This is usually used
          to parse an existing packet.
        """
        self.data_dict = {}
        self.address = None
        self._rssi = None
        self.connectable = False
        self.mutable = True
        self.scan_response = False

    @classmethod
    def from_entry(cls, entry):
        """Create an Advertisement based on the given ScanEntry. This is done automatically by
           `BLERadio` for all scan results."""
        self = cls()
        self.data_dict = decode_data(entry.advertisement_bytes)
        self.address = entry.address
        self._rssi = entry.rssi # pylint: disable=protected-access
        self.connectable = entry.connectable
        self.scan_response = entry.scan_response
        self.mutable = False
        return self

    @property
    def rssi(self):
        """Signal strength of the scanned advertisement. Only available on Advertisement's created
           from ScanEntrys. (read-only)"""
        return self._rssi

    @classmethod
    def matches(cls, entry):
        """Returns true if the given `_bleio.ScanEntry` matches all portions of the Advertisement
           type's prefix."""
        if not hasattr(cls, "prefix"):
            return True

        return entry.matches(cls.prefix)

    def __bytes__(self):
        """The raw packet bytes."""
        return encode_data(self.data_dict)

    def __str__(self):
        parts = ["<" + self.__class__.__name__]
        for attr in dir(self.__class__):
            attribute_instance = getattr(self.__class__, attr)
            if issubclass(attribute_instance.__class__, AdvertisingDataField):
                value = getattr(self, attr)
                if value is not None:
                    parts.append(attr + "=" + str(value))
        parts.append(">")
        return " ".join(parts)

    def __len__(self):
        return compute_length(self.data_dict)

    def __repr__(self):
        return "Advertisement(data={})".format(to_bytes_literal(encode_data(self.data_dict)))

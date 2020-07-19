"""Shark IQ Wrapper"""

import enum
import requests
from collections import abc
from typing import Dict, Iterable, List, Optional, Set, Union
from .ayla_api import AylaApi
from .const import DEVICE_URL, SHARK_APP_ID, SHARK_APP_SECRET

PropertyName = Union[str, enum.Enum]
PropertyValue = Union[str, int, enum.Enum]


def get_ayla_api(username, password):
    """Get an AylaApi object"""
    return AylaApi(username, password, SHARK_APP_ID, SHARK_APP_SECRET)


@enum.unique
class PowerModes(enum.IntEnum):
    ECO = 0
    NORMAL = 1
    MAX = 2


@enum.unique
class OperatingModes(enum.IntEnum):
    STOP = 0
    PAUSE = 1
    START = 2
    RETURN = 3


@enum.unique
class Properties(enum.Enum):
    BATTERY_CAPACITY = 'Battery_Capacity'
    FIND_DEVICE = 'Find_Device'
    OPERATING_MODE = 'Operating_Mode'
    POWER_MODE = 'Power_Mode'


def _clean_property_name(raw_property_name: str) -> str:
    """Clean up property names"""
    if raw_property_name[:4].upper() in ['SET_', 'GET_']:
        return raw_property_name[4:]
    else:
        return raw_property_name


class SharkIqVacuum:
    """Shark IQ vacuum entity"""

    def __init__(self, sapi: AylaApi, device_dct: Dict):
        self.sapi = sapi
        self._dsn = device_dct['dsn']
        self._key = device_dct['key']
        self._model_number = device_dct['oem_model']  # type: str
        self.properties_full = {}
        self.property_values = SharkPropertiesView(self)
        self._settable_properties = None  # type: Optional[Set]

        # Properties
        self._name = device_dct['product_name']
        self._error = None

    @property
    def model_number(self) -> str:
        return self._model_number

    @property
    def name(self):
        return self._name

    @property
    def serial_number(self) -> str:
        return self._dsn

    def get_property_value(self, property_name: PropertyName) -> str:
        """Get the value of a property from the properties dictionary"""
        if isinstance(property_name, enum.Enum):
            property_name = property_name.value
        return self.property_values[property_name]

    def _post_property(self, property_name: PropertyName, value: PropertyValue) -> requests.Response:
        """Send data to the device via the Ayla API"""
        if isinstance(property_name, enum.Enum):
            property_name = property_name.value

        end_point = f'{DEVICE_URL:s}/apiv1/dsns/{self._dsn:s}/properties/{property_name:s}/datapoints.json'
        data = {'datapoint': {'value': value}}
        r = self.sapi.post(end_point, json=data)
        return r

    def set_property_value(self, property_name: PropertyName, value: PropertyValue):
        """Update a property"""
        if isinstance(property_name, enum.Enum):
            property_name = property_name.value
        if isinstance(value, enum.Enum):
            value = value.value

        resp = self._post_property(f'SET_{property_name:s}', value)
        self.properties_full[property_name].update(resp.json())

    @property
    def update_url(self) -> str:
        """API endpoint to fetch updated device information"""
        return f'{DEVICE_URL}/apiv1/dsns/{self.serial_number}/properties.json'

    def update(self, property_list: Optional[Iterable[str]] = None):
        """Update the known device state"""
        if property_list is not None:
            params = {'names[]': property_list}
        else:
            params = None

        resp = self.sapi.get(self.update_url, params)
        properties = resp.json()
        self._do_update(property_list, properties)

    async def update_async(self, property_list: Optional[Iterable[str]] = None):
        if property_list is not None:
            params = {'names[]': property_list}
        else:
            params = None
        resp = await self.sapi.get_async(self.update_url, params)
        properties = await resp.json()
        resp.close()
        self._do_update(property_list, properties)

    def _do_update(self, property_list: Optional[Iterable[str]], properties: List[Dict]):
        """Update the internal state from fetched properties"""
        property_names = {p['property']['name'] for p in properties}
        settable_properties = {_clean_property_name(p) for p in property_names if p[:3].upper() == 'SET'}
        readable_properties = {
            _clean_property_name(p['property']['name']): p['property']
            for p in properties if p['property']['name'].upper() != 'SET'
        }

        if property_list is None or self._settable_properties is None:
            self._settable_properties = settable_properties
        else:
            self._settable_properties = self._settable_properties.union(settable_properties)

        # Update the property map so we can update by name instead of by fickle number
        if property_list is not None:
            self.properties_full.update(readable_properties)
        else:
            self.properties_full = readable_properties

    def start(self):
        self.set_property_value(Properties.OPERATING_MODE, OperatingModes.START)

    def stop(self):
        self.set_property_value(Properties.OPERATING_MODE, OperatingModes.STOP)

    def pause(self):
        self.set_property_value(Properties.OPERATING_MODE, OperatingModes.STOP)

    def return_to_base(self):
        self.set_property_value(Properties.OPERATING_MODE, OperatingModes.RETURN)

    def find_device(self):
        self.set_property_value(Properties.FIND_DEVICE, 1)


class SharkPropertiesView(abc.Mapping):
    """Convenience API for shark iq properties"""
    def __init__(self, shark: SharkIqVacuum):
        self._shark = shark

    def __getitem__(self, key):
        return self._shark.properties_full[key].get('value')

    def __iter__(self):
        for k in self._shark.properties_full.keys():
            yield k

    def __len__(self):
        return self._shark.properties_full.__len__()

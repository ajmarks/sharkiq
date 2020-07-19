"""Shark IQ Wrapper"""

import enum
from collections import abc, defaultdict
from typing import Dict, Iterable, List, Optional, Set, Union, TYPE_CHECKING
from .const import DEVICE_URL

if TYPE_CHECKING:
    from .ayla_api import AylaApi

PropertyName = Union[str, enum.Enum]
PropertyValue = Union[str, int, enum.Enum]


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

    def __init__(self, ayla_api: "AylaApi", device_dct: Dict):
        self.ayla_api = ayla_api
        self._dsn = device_dct['dsn']
        self._key = device_dct['key']
        self._model_number = device_dct['oem_model']  # type: str
        self.properties_full = defaultdict(dict)  # Using a defaultdict prevents errors before calling `update()`
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

    def get_property_endpoint(self, property_name) -> str:
        """Get the API endpoint for a given property"""
        return f'{DEVICE_URL:s}/apiv1/dsns/{self._dsn:s}/properties/{property_name:s}/datapoints.json'

    def get_property_value(self, property_name: PropertyName) -> str:
        """Get the value of a property from the properties dictionary"""
        if isinstance(property_name, enum.Enum):
            property_name = property_name.value
        return self.property_values[property_name]

    def set_property_value(self, property_name: PropertyName, value: PropertyValue):
        """Update a property"""
        if isinstance(property_name, enum.Enum):
            property_name = property_name.value
        if isinstance(value, enum.Enum):
            value = value.value

        end_point = self.get_property_endpoint(f'SET_{property_name}')
        data = {'datapoint': {'value': value}}
        resp = self.ayla_api.request('post', end_point, json=data)
        self.properties_full[property_name].update(resp.json())

    async def set_property_value_async(self, property_name: PropertyName, value: PropertyValue):
        """Update a property async"""
        if isinstance(property_name, enum.Enum):
            property_name = property_name.value
        if isinstance(value, enum.Enum):
            value = value.value

        end_point = self.get_property_endpoint(f'SET_{property_name}')
        data = {'datapoint': {'value': value}}
        resp = await self.ayla_api.async_request('post', end_point, json=data)
        resp_data = await resp.json()
        self.properties_full[property_name].update(resp_data)
        resp.close()

    @property
    def update_url(self) -> str:
        """API endpoint to fetch updated device information"""
        return f'{DEVICE_URL}/apiv1/dsns/{self.serial_number}/properties.json'

    def update(self, property_list: Optional[Iterable[str]] = None):
        """Update the known device state"""
        full_update = property_list is None
        if full_update:
            params = None
        else:
            params = {'names[]': property_list}

        resp = self.ayla_api.request('get', self.update_url, params=params)
        properties = resp.json()
        self._do_update(full_update, properties)

    async def async_update(self, property_list: Optional[Iterable[str]] = None):
        """Update the known device state async"""
        full_update = property_list is None
        if full_update:
            params = None
        else:
            params = {'names[]': property_list}

        resp = await self.ayla_api.async_request('get', self.update_url, params=params)
        properties = await resp.json()
        resp.close()

        self._do_update(full_update, properties)

    def _do_update(self, full_update: bool, properties: List[Dict]):
        """Update the internal state from fetched properties"""
        property_names = {p['property']['name'] for p in properties}
        settable_properties = {_clean_property_name(p) for p in property_names if p[:3].upper() == 'SET'}
        readable_properties = {
            _clean_property_name(p['property']['name']): p['property']
            for p in properties if p['property']['name'].upper() != 'SET'
        }

        if full_update or self._settable_properties is None:
            self._settable_properties = settable_properties
        else:
            self._settable_properties = self._settable_properties.union(settable_properties)

        # Update the property map so we can update by name instead of by fickle number
        if full_update:
            # Did a full update, so let's wipe everything
            self.properties_full = defaultdict(dict)
        self.properties_full.update(readable_properties)

    def set_operating_mode(self, mode: OperatingModes):
        self.set_property_value(Properties.OPERATING_MODE, mode)

    async def async_set_operating_mode(self, mode: OperatingModes):
        await self.set_property_value_async(Properties.OPERATING_MODE, mode)

    def find_device(self):
        self.set_property_value(Properties.FIND_DEVICE, 1)

    async def async_find_device(self):
        await self.set_property_value_async(Properties.FIND_DEVICE, 1)


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

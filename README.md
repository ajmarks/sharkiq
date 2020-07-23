# sharkiqpy
Unofficialy SDK for Shark IQ robot vacuums, designed primarily to support an integration for [Home Assistant](https://www.home-assistant.io/).

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install foobar.

```bash
pip install sharkiqpy
```

## Usage
### Simple Operation
```python
from sharkiqpy import get_ayla_api, OperatingModes, Properties, PowerModes

USERNAME = 'me@email.com'
PASSWORD = '$7r0nkP@s$w0rD'

ayla_api = get_ayla_api(USERNAME, PASSWORD)
ayla_api.sign_in()

shark_vacs = ayla_api.get_devices()
shark = shark_vacs[0]

shark.update()
shark.set_operating_mode(OperatingModes.START)
shark.return_to_base()
```

### Async operation
```python
import asyncio
from sharkiqpy import get_ayla_api, OperatingModes, SharkIqVacuum

USERNAME = 'me@email.com'
PASSWORD = '$7r0nkP@s$w0rD'

async def main(ayla_api) -> SharkIqVacuum:
    await ayla_api.async_sign_in()
        
    shark_vacs = await ayla_api.async_get_devices()
    shark = shark_vacs[0]
    await shark.async_update()
    await shark.async_find_device()
    await shark.async_set_operating_mode(OperatingModes.START)

    return shark


ayla_api = get_ayla_api(USERNAME, PASSWORD)
shark = asyncio.run(main(ayla_api))
```

## Documentation
### `get_ayla_api(username, password, websession=None)`
Returns and `AylaApi` object to interact with the Ayla Networks Device API conrolling the Shark IQ robot, with the `app_id` and `app_secret` parameters set for the Shark IQ robot.

### `class AylaAPI`
Class for interacting with the Ayla Networks Device API underlying the Shark IQ controls.

#### Parameters:
 * `username: str`
 * `password: str`
 * `app_id: str` 
 * `app_secret: str`
 * `websession: Optional[aiohttp.ClientSession] = None` Optional `aiohttp.ClientSession` to use for async calls.  If
  one is not provided, a new `aiohttp.ClientSession` will be created at the first async call.
#### Methods
 * `sign_in()`/`async_sign_in()` Authenticate
 * `refesh_auth()`/`async_refesh_auth()` Refresh the authentication token
 * `sign_out()`/`async_sign_out()` Sign out
 * `request(method, url, headers = None, auto_refresh = True, **kwargs)`/`async_request(...)` Submit an HTTP request to
  the Ayla networks API with the auth header
   * `method: str` An HTTP method, usually `'get'` or `'post'`
   * `url: str`
   * `headers: Optional[Dict] = None` Optional `dict` of HTTP headers besides the auth header, which is included 
   automatically
   * `auto_refresh: bool = True` If `True`, automatically call `refesh_auth()`/`async_refesh_auth()` if the auth token
   is near expiration
   * `**kwargs` Passed on to `requests.request` or `aiohttp.ClientSession.request`
  * `list_devices()`/`async_list_devices()` Get a list of known device description `dict`s
  * `get_devices()`/`async_get_devices()` Get a list of `SharkIqVacuum`s for every device found in `list_devices()`


### `class SharkIqRobot`
Primary API for interacting with Shark IQ vacuums

#### Parameters
 * `ayla_api: AylaApi` An `AylaApi` with an authenticated connection
 * `device_dct: Dict` A `dict` describing the device, usually obtained from `AylaApi.list_devices()`

#### Methods
 * `get_property_value(property_name)/async_get_property_value(property_name)`
   Returns the value of `property_name`, cast to the appropriate type
   * `property_name: Union[str, PropertyName]` Either a `str` or `PropertyNames` value for the desired property
 * `set_property_value(property_name, property_value)/async_set_property_value(property_name, property_value)`
 Set the value of `property_name`
   * `property_name: Union[str, PropertyName]` Either a `str` or `PropertyName` value for the desired property
   * `property_value: Any` New value.  Type checking is currently left to the remote API.
 * `update()`/`async_update(property_list=None)` Fetch the updated robot state from the remote api
   * `property_list: Optional[Interable[str]]` An optional iterable of property names.  If specified, only those 
   properties will be updated.
 * `set_operating_mode(mode)`/`async_set_operating_mode(mode)` Set the operating mode.  This is just a thin wrapper 
 around `set_property_value`/`async_set_property_value` provided for convenience.
   * mode: OperatingModes Mode to set, e.g., `OperatingModes.START` to start the vacuum
 * `find_device()`/`async_find_device()` Cause the device to emit an annoying chirp 
 * `get_metadata()`/`async_get_metadata()` Update some device metadata (`vac_model_number` and `vac_serial_number`)
 * `get_file_property_url`/`async_get_file_property_url` Get the URL for the latest version of a `'file'`-type property
 * `get_file_property`/`async_get_file_property` Get the contents of the latest version of a `'file'`-type property
 
#### Properties
 * `ayla_api` The underlying `AylaApi` object
 * `properties_full` A dictionary representing all known device properties and their metadata (type 
 `Dict[str, Dict]`)
 * `property_values` A convenience accessor into `properties_full` mapping property names to values
 * `oem_model_number` A "rough" model number that does not distinguish, for example, between robots with and without
 a self-emptying base
 * `vac_model_number` The precise model number
 * `vac_serial_number` The serial number printed on the device
 * `name` The device name as it appears in the SharkClean app
 * `serial_number` The unique device serial number used with the Ayla Networks API (NB: this name may change)
 * `error_code` Error code, if any.  *NB: these can be very stale as they are not immediately reset in the API when the 
 error is cleared*.
 * `error_text` English description of the `error_code`.  The same caveat applies.


### Enums
 * `Properties` Properties to use with `get_property_value`/`set_property_value`
 * `OperatingModes` Operation modes to control the vacuum (`START`, `STOP`, `PAUSE`, `RETURN`)
 * `PowerModes` Vacuum power mode (`ECO`, `NORMAL`, `MAX`)

 


## License
[MIT](https://choosealicense.com/licenses/mit/)

# pyshark
Python API for Shark IQ robot vacuums


### Examples
##### Simple Operation
```python
from sharkiq import get_ayla_api, OperatingModes

USERNAME = 'me@email.com'
PASSWORD = '$7r0nkP@s$w0rD'

ayla_api = get_ayla_api(USERNAME, PASSWORD)
ayla_api.auth()

shark_vacs = ayla_api.get_devices()
shark = shark_vacs[0]

shark.update()
shark.set_operating_mode(OperatingModes.START)
shark.return_to_base()
```

##### Async operation
```python
import asyncio
from sharkiq import get_ayla_api, OperatingModes, SharkIqVacuum

USERNAME = 'me@email.com'
PASSWORD = '$7r0nkP@s$w0rD'

async def main(ayla_api) -> SharkIqVacuum:
    await ayla_api.async_auth()
        
    shark_vacs = await ayla_api.async_get_devices()
    shark = shark_vacs[0]
    await shark.async_update()
    await shark.async_find_device()
    await shark.async_set_operating_mode(OperatingModes.START)

    return shark


ayla_api = get_ayla_api(USERNAME, PASSWORD)
shark = asyncio.run(main(ayla_api))
```
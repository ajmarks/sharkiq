# pyshark
Python API for Shark IQ robot vacuums


### Examples
##### Simple Operation
```python
from sharkiq import get_ayla_api, SharkIqVacuum

USERNAME = 'me@email.com'
PASSWORD = '$7r0nkP@s$w0rD'

ayla_api = get_ayla_api(USERNAME, PASSWORD)
ayla_api.auth()

devices = ayla_api.list_devices()

shark_vacs = [SharkIqVacuum(ayla_api, d) for d in devices]
shark = shark_vacs[0]
shark.update()
shark.start()
shark.return_to_base()
```

##### Async operation
```python
import asyncio
from sharkiq import get_ayla_api, SharkIqVacuum

USERNAME = 'me@email.com'
PASSWORD = '$7r0nkP@s$w0rD'

async def main(ayla_api) -> SharkIqVacuum:
    await ayla_api.auth_async()
    print(ayla_api.auth_header)
    devices = await ayla_api.list_devices_async()
    shark_vacs = [SharkIqVacuum(ayla_api, d) for d in devices]

    shark = shark_vacs[0]
    await shark.update_async()
    await shark.find_device_async()

    return shark


ayla_api = get_ayla_api(USERNAME, PASSWORD)
shark = asyncio.run(main(ayla_api))
```
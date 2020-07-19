# pyshark
Python API for Shark IQ robot vacuums


## Usage
```python
from sharkiq import get_ayla_api, SharkIqVacuum


USERNAME = 'me@email.com'
PASSWORD = '$7r0nkP@s$w0rD'

sapi = get_ayla_api(USERNAME, PASSWORD)
sapi.auth()

devices = sapi.list_devices()

shark_vacs = [SharkIqVacuum(sapi, d) for d in devices]
shark = shark_vacs[0]
shark.start()
shark.return_to_base()
```


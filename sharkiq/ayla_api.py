"""Simple implementation of the Ayla networks API"""

import aiohttp
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .sharkiq import SharkIqVacuum
from .const import DEVICE_URL, LOGIN_URL, SHARK_APP_ID, SHARK_APP_SECRET

_session = None


def get_ayla_api(username: str, password: str, websession: Optional[aiohttp.ClientSession] = None):
    """Get an AylaApi object"""
    return AylaApi(username, password, SHARK_APP_ID, SHARK_APP_SECRET, websession=websession)


async def _get_session():
    """Get a new ClientSession"""
    global _session
    if _session is None:
        _session = aiohttp.ClientSession()
    return _session


class AylaApi:
    """Simple Ayla Networks API wrapper"""

    def __init__(
            self,
            email: str,
            password: str,
            app_id: str,
            app_secret: str,
            websession: Optional[aiohttp.ClientSession] = None):
        self._email = email
        self._password = password
        self._access_token = None  # type: Optional[str]
        self._refresh_token = None  # type: Optional[str]
        self._auth_expiration = None  # type: Optional[datetime]
        self._is_authed = False  # type: bool
        self._app_id = app_id
        self._app_secret = app_secret
        self._websession = websession

    @property
    def _login_data(self) -> Dict[str, Dict]:
        return {
            "user": {
                "email": self._email,
                "password": self._password,
                "application": {"app_id": self._app_id, "app_secret": self._app_secret},
            }
        }

    def _set_credentials(self, login_result: Dict):
        """Update the internal credentials store"""
        self._access_token = login_result["access_token"]
        self._refresh_token = login_result["refresh_token"]
        self._auth_expiration = datetime.now() + timedelta(seconds=login_result["expires_in"])
        self._is_authed = True

    def auth(self):
        login_data = self._login_data
        resp = requests.post(f"{LOGIN_URL:s}/users/sign_in.json", json=login_data)
        self._set_credentials(resp.json())

    def refresh_auth(self):
        refresh_data = {"user": {"refresh_token": self._refresh_token}}
        resp = requests.post(f"{LOGIN_URL:s}/users/refresh_token.json", json=refresh_data)
        self._set_credentials(resp.json())

    async def auth_async(self):
        session = await _get_session()
        login_data = self._login_data
        async with session.post(f"{LOGIN_URL:s}/users/sign_in.json", json=login_data) as resp:
            self._set_credentials(await resp.json())

    async def async_refresh_auth(self):
        session = await _get_session()
        refresh_data = {"user": {"refresh_token": self._refresh_token}}
        async with session.post(f"{LOGIN_URL:s}/users/refresh_token.json", json=refresh_data) as resp:
            self._set_credentials(await resp.json())

    @property
    def token_expired(self) -> bool:
        return datetime.now() > self._auth_expiration - timedelta(seconds=600)

    @property
    def auth_header(self) -> Dict[str, str]:
        if self._access_token is None:
            raise RuntimeError('Auth Error')
        return {"Authorization": f"auth_token {self._access_token:s}"}

    def request(self, method: str, url: str, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        if self.token_expired:
            self.refresh_auth()

        if headers is None:
            headers = self.auth_header
        else:
            headers = {**headers, **self.auth_header}
        return requests.request(method, url, headers=headers, **kwargs)

    async def async_request(
            self, http_method: str, url: str, headers: Optional[Dict] = None, **kwargs) -> aiohttp.ClientResponse:
        if self._websession is None:
            self._websession = await _get_session()
        if self.token_expired:
            await self.async_refresh_auth()

        session = self._websession
        if headers is None:
            headers = self.auth_header
        else:
            headers = {**headers, **self.auth_header}
        return await session.request(http_method, url, headers=headers, **kwargs)

    def list_devices(self) -> List[Dict]:
        resp = self.request("get", f"{DEVICE_URL:s}/apiv1/devices.json")
        devices = resp.json()
        return [d["device"] for d in devices]

    async def list_devices_async(self) -> List[Dict]:
        resp = await self.async_request("get", f"{DEVICE_URL:s}/apiv1/devices.json")
        devices = await resp.json()
        resp.close()
        return [d["device"] for d in devices]

    def get_devices(self, update: bool = True) -> List[SharkIqVacuum]:
        devices = [SharkIqVacuum(self, d) for d in self.list_devices()]
        if update:
            for device in devices:
                device.update()
        return devices

    async def async_get_devices(self, update: bool = True) -> List[SharkIqVacuum]:
        devices = [SharkIqVacuum(self, d) for d in await self.list_devices_async()]
        if update:
            for device in devices:
                await device.async_update()
        return devices
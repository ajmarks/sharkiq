"""Simple implementation of the Ayla networks API"""

import aiohttp
import requests
from datetime import datetime
from functools import partial
from typing import Callable, Dict, List, Optional
from .const import DEVICE_URL, LOGIN_URL

_session = None


async def _get_session():
    global _session
    if _session is None:
        _session = aiohttp.ClientSession()
    return _session


class AylaApi:
    """Simple Ayla Networks API wrapper"""

    def __init__(self, email: str, password: str, app_id: str, app_secret: str):
        self._email = email
        self._password = password
        self._access_token = None  # type: Optional[str]
        self._refresh_token = None  # type: Optional[str]
        self._auth_expiration = None # type: Optional[datetime]
        self._is_authed = False  # type: bool
        self._app_id = app_id
        self._app_secret = app_secret

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
        self._access_token = login_result["access_token"]
        self._refresh_token = login_result["refresh_token"]
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

    async def refresh_auth_async(self):
        session = await _get_session()
        refresh_data = {"user": {"refresh_token": self._refresh_token}}
        async with session.post(f"{LOGIN_URL:s}/users/refresh_token.json", json=refresh_data) as resp:
            self._set_credentials(await resp.json())

    def list_devices(self) -> List[Dict]:
        r = self.get(f"{DEVICE_URL:s}/apiv1/devices.json")
        devices = r.json()
        return [d["device"] for d in devices]

    @property
    def auth_header(self) -> Dict[str, str]:
        if self._access_token is None:
            raise RuntimeError('Auth Error')
        return {"Authorization": f"auth_token {self._access_token:s}"}

    def http(self, url: str, method: Callable[..., requests.Response], **kwargs) -> requests.Response:
        return method(url, headers=self.auth_header, **kwargs)

    def get(self, url: str, params=None, **kwargs) -> requests.Response:
        return self.http(url, requests.get, params=params, **kwargs)

    def post(self, url: str, data=None, json=None, **kwargs) -> requests.Response:
        return self.http(url, requests.post, data=data, json=json, **kwargs)

    def put(self,  url, data=None, **kwargs) -> requests.Response:
        return self.http(url, requests.put, data=data, **kwargs)

    async def http_async(self, url: str, http_method: str, **kwargs) -> aiohttp.ClientResponse:
        session = await _get_session()
        method = partial(getattr(session, http_method), headers=self.auth_header)
        return await method(url, **kwargs)

    async def get_async(self, url: str, params=None, **kwargs) -> aiohttp.ClientResponse:
        return await self.http_async(url, 'get', params=params, **kwargs)

    async def post_async(self, url: str, data=None, json=None, **kwargs) -> aiohttp.ClientResponse:
        return await self.http_async(url, 'post', data=data, json=json, **kwargs)

    async def put_async(self,  url, data=None, **kwargs) -> aiohttp.ClientResponse:
        return await self.http_async(url, 'put', data=data, **kwargs)

    async def list_devices_async(self) -> List[Dict]:
        resp = await self.get_async(f"{DEVICE_URL:s}/apiv1/devices.json")
        print(resp)
        devices = await resp.json()
        resp.close()
        return [d["device"] for d in devices]
"""Simple implementation of the Ayla networks API"""

import aiohttp
import requests
from functools import partial
from typing import Dict, List
from .const import DEVICE_URL, LOGIN_URL


class AylaApi:
    """Simple Ayla Networks API wrapper"""

    def __init__(self, email: str, password: str, app_id: str, app_secret: str):
        self._email = email
        self._password = password
        self._access_token = None
        self._refresh_token = None
        self._auth_expiration = None
        self._is_authed = False
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
        r = requests.post(f"{LOGIN_URL:s}/users/sign_in.json", json=login_data)
        self._set_credentials(r.json())

    def refresh_auth(self):
        refresh_data = {"user": {"refresh_token": self._refresh_token}}
        r = requests.post(f"{LOGIN_URL:s}/users/refresh_token.json", json=refresh_data)
        self._set_credentials(r.json())

    def list_devices(self) -> List[Dict]:
        r = self.get(f"{DEVICE_URL:s}/apiv1/devices.json")
        devices = r.json()
        return [d["device"] for d in devices]

    async def async_list_devices(self) -> List[Dict]:
        r = self.async_get(f"{DEVICE_URL:s}/apiv1/devices.json")
        devices = r.json()
        return [d["device"] for d in devices]

    @property
    def auth_header(self) -> Dict[str, str]:
        if self._access_token is None:
            raise RuntimeError('Auth Error')
        return {"Authorization": f"auth_token {self._access_token: s}"}

    def __getattr__(self, name):
        if name[:6] == "async_":
            return partial(getattr(aiohttp, name[6:]), headers=self.auth_header)
        else:
            return partial(getattr(requests, name), headers=self.auth_header)


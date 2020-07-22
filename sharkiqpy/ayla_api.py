"""Simple implementation of the Ayla networks API"""

import aiohttp
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .const import (
    DEVICE_URL,
    LOGIN_URL,
    SHARK_APP_ID,
    SHARK_APP_SECRET,
)
from .exc import SharkIqAuthError, SharkIqAuthExpiredError, SharkIqNotAuthedError
from .sharkiq import SharkIqVacuum

_session = None


def get_ayla_api(username: str, password: str, websession: Optional[aiohttp.ClientSession] = None):
    """Get an AylaApi object"""
    return AylaApi(username, password, SHARK_APP_ID, SHARK_APP_SECRET, websession=websession)


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

    def ensure_session(self) -> aiohttp.ClientSession:
        """Ensure that we have an aiohttp ClientSession"""
        if self._websession is None:
            self._websession = aiohttp.ClientSession()
        return self._websession

    @property
    def _login_data(self) -> Dict[str, Dict]:
        """Prettily formatted data for the login flow"""
        return {
            "user": {
                "email": self._email,
                "password": self._password,
                "application": {"app_id": self._app_id, "app_secret": self._app_secret},
            }
        }

    def _set_credentials(self, status_code: int, login_result: Dict):
        """Update the internal credentials store"""
        if status_code == 404:
            raise SharkIqAuthError(login_result["error"] + " (Confirm app_id and app_secret are correct)")
        elif status_code == 401:
            raise SharkIqAuthError(login_result["error"])

        self._access_token = login_result["access_token"]
        self._refresh_token = login_result["refresh_token"]
        self._auth_expiration = datetime.now() + timedelta(seconds=login_result["expires_in"])
        self._is_authed = True

    def sign_in(self):
        """Authenticate to Ayla API synchronously"""
        login_data = self._login_data
        resp = requests.post(f"{LOGIN_URL:s}/users/sign_in.json", json=login_data)
        self._set_credentials(resp.status_code, resp.json())

    def refresh_auth(self):
        """Refresh the authentication synchronously"""
        refresh_data = {"user": {"refresh_token": self._refresh_token}}
        resp = requests.post(f"{LOGIN_URL:s}/users/refresh_token.json", json=refresh_data)
        self._set_credentials(resp.status_code, resp.json())

    async def async_sign_in(self):
        session = self.ensure_session()
        login_data = self._login_data
        async with session.post(f"{LOGIN_URL:s}/users/sign_in.json", json=login_data) as resp:
            self._set_credentials(resp.status, await resp.json())

    async def async_refresh_auth(self):
        session = self.ensure_session()
        refresh_data = {"user": {"refresh_token": self._refresh_token}}
        async with session.post(f"{LOGIN_URL:s}/users/refresh_token.json", json=refresh_data) as resp:
            self._set_credentials(resp.status, await resp.json())

    @property
    def sign_out_data(self) -> Dict:
        """Payload for the sign_out call"""
        return {"user": {"access_token": self._access_token}}

    def _clear_auth(self):
        """Clear authentication state"""
        self._is_authed = False
        self._access_token = None
        self._refresh_token = None
        self._auth_expiration = None

    def sign_out(self):
        """Sign out and invalidate the access token"""
        requests.post(f"{LOGIN_URL:s}/users/sign_out.json", json=self.sign_out_data)
        self._clear_auth()

    async def async_sign_out(self):
        """Sign out and invalidate the access token"""
        session = self.ensure_session()
        async with session.post(f"{LOGIN_URL:s}/users/sign_out.json", json=self.sign_out_data) as _:
            pass
        self._clear_auth()

    @property
    def auth_expiration(self) -> Optional[datetime]:
        """When does the auth expire"""
        if not self._is_authed:
            return None
        elif self._auth_expiration is None:  # This should not happen, but let's be ready if it does...
            raise SharkIqNotAuthedError("Invalid state.  Please reauthorize.")
        else:
            return self._auth_expiration

    @property
    def token_expired(self) -> bool:
        if self.auth_expiration is None:
            return True
        return datetime.now() > self.auth_expiration + timedelta(seconds=60)  # Prevent timeout immediately following

    def check_auth(self, confirm_still_valid=False):
        """Confirm authentication status"""
        authed = self._access_token is not None and self._is_authed
        if not authed:
            raise SharkIqNotAuthedError()
        elif confirm_still_valid and not self.token_expired:
            raise SharkIqAuthExpiredError()

    @property
    def auth_header(self) -> Dict[str, str]:
        self.check_auth()
        return {"Authorization": f"auth_token {self._access_token:s}"}

    def request(
            self, method: str, url: str,
            headers: Optional[Dict] = None, auto_refresh: bool = True, **kwargs) -> requests.Response:
        try:
            self.check_auth()
        except SharkIqAuthExpiredError:
            if auto_refresh:
                self.refresh_auth()
            else:
                raise

        if headers is None:
            headers = self.auth_header
        else:
            headers = {**headers, **self.auth_header}
        return requests.request(method, url, headers=headers, **kwargs)

    async def async_request(
            self, http_method: str, url: str,
            headers: Optional[Dict] = None, auto_refresh: bool = True, **kwargs):
        session = self.ensure_session()

        try:
            self.check_auth()
        except SharkIqAuthExpiredError:
            if auto_refresh:
                await self.async_refresh_auth()
            else:
                raise

        if headers is None:
            headers = self.auth_header
        else:
            headers = {**headers, **self.auth_header}
        return session.request(http_method, url, headers=headers, **kwargs)

    def list_devices(self) -> List[Dict]:
        resp = self.request("get", f"{DEVICE_URL:s}/apiv1/devices.json")
        devices = resp.json()
        return [d["device"] for d in devices]

    async def list_devices_async(self) -> List[Dict]:
        async with await self.async_request("get", f"{DEVICE_URL:s}/apiv1/devices.json") as resp:
            devices = await resp.json()
        return [d["device"] for d in devices]

    def get_devices(self, update: bool = True) -> List[SharkIqVacuum]:
        devices = [SharkIqVacuum(self, d) for d in self.list_devices()]
        if update:
            for device in devices:
                device.get_metadata()
                device.update()
        return devices

    async def async_get_devices(self, update: bool = True) -> List[SharkIqVacuum]:
        devices = [SharkIqVacuum(self, d) for d in await self.list_devices_async()]
        if update:
            for device in devices:
                await device.async_get_metadata()
                await device.async_update()
        return devices

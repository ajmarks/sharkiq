"""Python API for Shark IQ vacuum robots"""

from .ayla_api import get_ayla_api, AylaApi
from .exc import SharkIqError, SharkIqAuthExpiredError, SharkIqNotAuthedError, SharkIqAuthError
from .sharkiq import SharkIqVacuum, PowerModes, OperatingModes, Properties

__version__ = '0.3.2'

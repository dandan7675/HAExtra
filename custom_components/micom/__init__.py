from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .micloud.miauth import MiAuth
from .micloud.miio import MiIO
from homeassistant.helpers.storage import STORAGE_DIR

import logging
_LOGGER = logging.getLogger(__name__)

DOMAIN = 'micom'

_miauth = None
_miio = None


async def async_setup(hass, config):
    conf = config.get(DOMAIN)
    global _miauth, _miio
    # TODO: new aiohttp session?
    # TODO: Use session context?
    _miauth = MiAuth(async_get_clientsession(hass), conf['username'], conf['password'], hass.config.path(STORAGE_DIR, DOMAIN))
    _miio = MiIO(_miauth, conf.get('region'))
    return True


def miio():
    return _miio

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .micloud.miauth import MiAuth
from .micloud.miiocloud import MiIOCloud
from homeassistant.helpers.storage import STORAGE_DIR

import logging
_LOGGER = logging.getLogger(__name__)

DOMAIN = 'micom'

_miaccount = None
_miiocloud = None


async def async_setup(hass, config):
    conf = config.get(DOMAIN)
    global _miaccount, _miiocloud
    # TODO: new aiohttp session?
    # TODO: Use session context?
    _miaccount = MiAuth(async_get_clientsession(hass), conf['username'], conf['password'], hass.config.path(STORAGE_DIR, DOMAIN))
    _miiocloud = MiIOCloud(_miaccount, conf.get('region'))
    return True


def miiocloud():
    return _miiocloud

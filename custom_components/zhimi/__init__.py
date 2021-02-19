from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .micloud.miauth import MiAuth
from .micloud.miiocloud import MiIOCloud
from homeassistant.helpers.storage import STORAGE_DIR

import logging
_LOGGER = logging.getLogger(__name__)

DOMAIN = 'micom'

_mi_auth = None
_miio_cloud = None


async def async_setup(hass, config):
    conf = config.get(DOMAIN)
    global _mi_auth, _miio_cloud
    # TODO: new aiohttp session?
    # TODO: Use session context?
    _mi_auth = MiAuth(async_get_clientsession(hass), conf['username'], conf['password'], hass.config.path(STORAGE_DIR, DOMAIN))
    _miio_cloud = MiIOCloud(_mi_auth, conf.get('region'))
    return True


def miio_cloud():
    return _miio_cloud

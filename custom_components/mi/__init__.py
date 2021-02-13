from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .micloud.miaccount import MiAccount
from .micloud.miiocloud import MiIOCloud

import logging
_LOGGER = logging.getLogger(__name__)

DOMAIN = 'mi'

_miaccount = None
_miiocloud = None

async def async_setup(hass, config):
    conf = config.get(DOMAIN)
    global _miaccount, _miiocloud
    # TODO: new aiohttp session?
    # TODO: Use session context?
    _miaccount = MiAccount(async_get_clientsession(hass), str(conf['username']), str(conf['password']), hass.config.path('.micloud'))
    _miiocloud = MiIOCloud(_miaccount, conf.get('region'))
    return True

def miiocloud():
    return _miiocloud

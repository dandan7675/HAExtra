from custom_components.micloud.miaccount import MiAccount
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .micloud import MiCloud

import logging
_LOGGER = logging.getLogger(__name__)

DOMAIN = 'micloud'

miiocloud = None

async def async_setup(hass, config):
    conf = config.get(DOMAIN)
    global miiocloud
    account = MiAccount(async_get_clientsession(hass), str(conf['username']), str(conf['password']), hass.config.path('.micloud'))
    
    return True

miiocloud
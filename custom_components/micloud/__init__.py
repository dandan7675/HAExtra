from custom_components.micloud.miaccount import MiAccount
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from miaccount import MiAccount
from miiocloud import MiIOCloud

import logging
_LOGGER = logging.getLogger(__name__)

DOMAIN = 'micloud'

miaccount = None
miiocloud = None

async def async_setup(hass, config):
    conf = config.get(DOMAIN)
    global miaccount, miiocloud
    # TODO: new aiohttp session?
    # TODO: Use session context?
    miaccount = MiAccount(async_get_clientsession(hass), str(conf['username']), str(conf['password']), hass.config.path('.micloud'))
    miiocloud = MiIOCloud(miaccount, conf.get('region'))
    return True

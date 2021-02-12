from .micloud import MiAuth, MiCloud
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers import aiohttp_client

import logging
_LOGGER = logging.getLogger(__name__)

# Config validation
SERVICE_SCHEMA = vol.All(
    vol.Schema({
        vol.Optional('message'): cv.string,
        vol.Optional('volume'): vol.Range(min=0, max=100),
        vol.Optional('devno'): vol.Range(min=-1, max=9),
        # vol.Optional('region'): cv.string,
    }),
    cv.has_at_least_one_key("message", "volume"),
)


class miotmsg(MiCloud):

    def __init__(self, hass, conf):
        session = aiohttp_client.async_get_clientsession(hass)
        # from aiohttp import ClientSession
        # session = ClientSession()
        auth = MiAuth(session, conf['username'], conf['password'], hass.config.config_dir)
        super().__init__(auth, conf.get('region'))
        self.did = str(conf['did'])

    async def async_send(self, message, data):
        # volume = data.get('volume')
        params = {
            'did': self.did,
            'siid': 5,
            'aiid': 1,
            'in': [message],
        }
        await self.miot_action(params)

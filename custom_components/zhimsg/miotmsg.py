from .micloud import MiAuth, MiCloud
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import aiohttp_client
import voluptuous as vol

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
        username = conf['username']
        session = aiohttp_client.async_get_clientsession(hass)
        account = MiAuth(session, username, conf['password'], hass.config.config_dir)
        super().__init__(account, conf.get('region'))
        self.did = str(conf.get('did'))
        self.devices = None

    async def async_send_message(self, message, data):
        volume = data.get('volume')
        params = {
            'did': self.did,
            'siid': 5,
            'aiid': 1,
            'in': [message],
        }
        await self.miot_action(params)

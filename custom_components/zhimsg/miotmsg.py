from .micloud import MiAuth, MiCloud
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers.aiohttp_client import async_get_clientsession

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
        auth = MiAuth(async_get_clientsession(hass), str(conf['username']), str(conf['password']), hass.config.config_dir)
        super().__init__(auth, conf.get('region'))
        self.did = str(conf['did'])
        self.siid = conf.get('siid', 5)
        self.aiid = conf.get('aiid', 1)

    async def async_send(self, message, data):
        result = await self.miot_action({'did': self.did, 'siid': self.siid, 'aiid': self.aiid,'in': [message]})
        return f"{result}" if type(result) == Exception else None

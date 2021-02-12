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
        self.did = conf['did']
        self.siid = conf.get('siid', 5)
        self.aiid = conf.get('aiid', 1)  # 4
        self.template = conf.get('template', '["%s"]')
        self.execute_siid = conf.get('execute_siid', self.siid)
        self.execute_aiid = conf.get('execute_aiid', 4)
        self.execute_template = conf.get('execute_template', '["%s",1]')
        self.volume_siid = conf.get('volume_siid', 2)
        self.volume_piid = conf.get('volume_piid', 1)

    async def async_send(self, message, data):
        if message.startswith('音量'):
            pos = message.find('%')
            volume = message[2:None if pos == -1 else pos]
            result = await self.miot_prop(self.did, [(self.volume_siid, self.volume_piid, volume, False)])
            message = None if pos == -1 else message[pos+1:]
        if message:
            if message.startswith('执行') or message.startswith('询问'):
                result = await self.miot_action(self.execute_siid, self.execute_aiid, self.execute_template % message[2:], self.did)
            else:
                result = await self.miot_action(self.siid, self.aiid, self.template % message, self.did)
        return f"{result}" if type(result) == Exception else None

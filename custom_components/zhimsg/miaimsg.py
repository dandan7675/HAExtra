from ..micloud import miiocloud
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers.aiohttp_client import async_get_clientsession

import logging
_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA = vol.All(
    vol.Schema({
        vol.Optional('message'): cv.string,
        vol.Optional('volume'): vol.Range(min=0, max=100),
        vol.Optional('devno'): vol.Range(min=-1, max=9),
        # vol.Optional('region'): cv.string,
    }),
    cv.has_at_least_one_key("message", "volume"),
)

MODEL_SPECS = {
    'lx01': {},
    'lx04': {'execute_aiid': 4},
    'lx08c': {'siid': 3, 'volume_siid': 4},
}


class miaimsg:

    def __init__(self, hass, conf):
        self.did = conf['did']
        self.spec = MODEL_SPECS[conf.get('model', 'lx01')]

    async def async_send(self, message, data):
        if message.startswith('音量'):
            pos = message.find('%')
            volume = message[2:None if pos == -1 else pos]
            result = await miiocloud.miot_prop(self.did, [(self.spec.get('volume_siid', 2), self.spec.get('volume_piid', 2), volume, False)])
            message = None if pos == -1 else message[pos+1:]
        else:
            result = Exception("空谈误国，实干兴邦！")
        if message:
            if message[0] == '$' or message.startswith('执行') or message.startswith('询问'):
                siid = self.spec.get('execute_siid', 5)
                aiid = self.spec.get('execute_aiid', 5)
                pos = 1 if message[0] == '$' else 2
                message = f'["{message[pos:]}",1]'
            else:
                siid = self.spec.get('siid', 5)
                aiid = self.spec.get('aiid', 1)
            result = await miiocloud.miot_action(self.did, siid, aiid, message)
        return f"{result}" if type(result) == Exception else None

from ..micom import miiocloud

import logging
_LOGGER = logging.getLogger(__name__)


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
        if message[0] == '%' or message.startswith('音量'):
            pos = message.find('%')
            start = 1 if message[0] == '%' else 2
            volume = message[start:None if pos == -1 else pos]
            result = await miiocloud().miot_set_props(self.did, [(self.spec.get('volume_siid', 2), self.spec.get('volume_piid', 1), int(volume))])
            message = None if pos == -1 else message[pos+1:]
        else:
            result = Exception("空谈误国，实干兴邦！")
        if message:
            if message[0] == '$' or message.startswith('查询') or message.startswith('执行') or message.startswith('静默'):
                siid = self.spec.get('execute_siid', 5)
                aiid = self.spec.get('execute_aiid', 5)
                start = 1 if message[0] == '$' else 2
                echo = 0 if message.startswith('静默') else 1
                message = f'["{message[start:]}",{echo}]'
            else:
                siid = self.spec.get('siid', 5)
                aiid = self.spec.get('aiid', 1)
            result = await miiocloud().miot_action_text(self.did, siid, aiid, message)
        return f"{result}" if isinstance(result, Exception) else None

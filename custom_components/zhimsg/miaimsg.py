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
        self.did = str(conf['did'])
        self.spec = MODEL_SPECS[conf.get('model', 'lx01')]

    async def async_send(self, message, data):

        if message.startswith('音量'):
            pos = message.find('%')
            volume = int(message[2:None if pos == -1 else pos])
            siid = self.spec.get('volume_siid', 2)
            piid = self.spec.get('volume_piid', 1)
            code = await miiocloud().miot_set_prop(self.did, siid, piid, volume)
            if pos == -1:
                return f"错误代码：{code}" if code else None
            message = message[pos+1:]

        if not message:
            return "空谈误国，实干兴邦！"

        if message.startswith('查询') or message.startswith('执行') or message.startswith('静默'):
            siid = self.spec.get('execute_siid', 5)
            aiid = self.spec.get('execute_aiid', 5)
            echo = 0 if message.startswith('静默') else 1
            message = f'["{message[2:]}",{echo}]'
        else:
            siid = self.spec.get('siid', 5)
            aiid = self.spec.get('aiid', 1)
        code = await miiocloud().miot_action_text(self.did, siid, aiid, message)
        return f"错误代码：{code}" if code else None

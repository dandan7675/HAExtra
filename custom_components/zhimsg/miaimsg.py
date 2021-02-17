from ..micom import miiocloud

import logging
_LOGGER = logging.getLogger(__name__)


MODEL_SPECS = {
    # 'default': {'siid': 5, 'aiid': 1, 'execute_siid': 5, 'execute_aiid': 5, 'volume_siid': 2, 'volume_piid': 1},
    'lx01': {},
    'lx04': {'execute_aiid': 4},
    'lx08c': {'siid': 3, 'volume_siid': 4},
}


class miaimsg:

    def __init__(self, hass, conf):
        self.did = str(conf['did'])
        self.spec = MODEL_SPECS[conf.get('model', 'lx01')]

    async def async_send(self, message, data):

        if message.startswith('/'):
            pos = message.find('{')
            if pos != -1:
                return await miiocloud().miio(message[0:pos+1], message[pos:])

        elif message.startswith('{') or message.startswith('['):
            pos = message.rfind('}' if message.startswith('{') else ']')
            if pos != -1:
                api = message[pos+1:] or ('action' if message.startswith('{') else 'prop/get')
                return await miiocloud().miot_spec(api, message[0:pos+1])

        elif message.startswith('音量'):
            pos = message.find('%')
            if pos == -1:
                volume = message[2:]
                message = None
            else:
                volume = message[2:pos]
                message = message[pos+1:].strip()
            siid = self.spec.get('volume_siid', 2)
            piid = self.spec.get('volume_piid', 1)
            try:
                volume = int(volume)
            except:
                return f"当前音量：{await miiocloud().miot_get_prop(self.did, siid, piid)}"
            code = await miiocloud().miot_set_prop(self.did, siid, piid, volume)
            if not message:
                return f"设置音量出错：{code}" if code else None

        if message.startswith('查询') or message.startswith('执行') or message.startswith('静默'):
            siid = self.spec.get('execute_siid', 5)
            aiid = self.spec.get('execute_aiid', 5)
            echo = 0 if message.startswith('静默') else 1
            message = message[2:].strip()
            args = f'["{message}", {echo}]'
        else:
            siid = self.spec.get('siid', 5)
            aiid = self.spec.get('aiid', 1)
            args = f'["{message}"]'

        if not message:
            return "空谈误国，实干兴邦！"

        result = await miiocloud().miot_action(self.did, siid, aiid, args)
        return None if result.get('code') == 0 else result

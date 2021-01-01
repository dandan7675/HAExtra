
#
from .dingbot import dingbotView
from ..zhimsg import async_send_message

# Logging
import logging
_LOGGER = logging.getLogger(__name__)


#
class ding2miaibotView(dingbotView):

    async def handle(self, data):
        content = data['text']['content']
        if content.startswith('音量'):
            pos = content.find('%')
            if pos == -1:
                volume = content[2:]
                message = None
            else:
                volume = content[2:pos]
                message = content[pos+1:]
            await async_send_message('miai', message, {'volume': volume})
            return '已设置音量：' + volume + (('，并喊话：' + message) if message else '')
        await async_send_message('miai', content)
        return '已喊话：' + content
 
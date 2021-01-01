
#
from .dingbot import dingbotView
from ..zhimsg import async_send_message

# Logging
import logging
_LOGGER = logging.getLogger(__name__)


#
class ding2miaibotView(dingbotView):

    async def handleQuery(self, query):
        if query.startswith('音量'):
            pos = query.find('%')
            if pos == -1:
                volume = query[2:]
                message = None
            else:
                volume = query[2:pos]
                message = query[pos+1:]
            await async_send_message('miai', message, {'volume': volume})
            return '已设置音量：' + volume + (('，并喊话：' + message) if message else '')
        await async_send_message('miai', query)
        return '已喊话：' + query
 
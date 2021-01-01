
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
            volume = query[2:None if pos == -1 else pos]
            message = None if pos == -1 else query[pos+1:]
            answer = '已设置音量：' + volume + (('，并喊话：' + message) if message else '') 
        else:
            volume = None
            message = query
            answer = '已喊话：' + query
        await async_send_message('miai', query, {'volume': volume} if volume else {})
        return answer

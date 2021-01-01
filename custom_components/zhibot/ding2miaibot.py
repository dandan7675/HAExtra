
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
            message = None if pos == -1 else query[pos+1:]
            data = {'volume': query[2:None if if pos == -1 else pos]}
            answer = '已设置音量：' + volume + (('，并喊话：' + message) if message else '') 
        else:
            message = query
            data = {}
            answer = '已喊话：' + query
        await async_send_message('miai', query, data)
        return answer

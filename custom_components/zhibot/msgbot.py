from .dingbot import dingbotView
from ..zhimsg import async_send

# Logging
import logging
_LOGGER = logging.getLogger(__name__)


#
class msgbotView(dingbotView):

    def __init__(self, hass, conf):
        super().__init__(hass, conf)
        self.service = conf.get('service', 'ding')

    async def handleChat(self, query):
        return await async_send(self.service, message, data)

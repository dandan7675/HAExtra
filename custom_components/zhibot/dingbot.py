
#
from .zhichat import zhiChat
from .basebot import basebot
from ..zhimsg import async_send

import logging
_LOGGER = logging.getLogger(__name__)


class dingbot(basebot):

    def get_auth_user(self, data):
        return data['chatbotUserId']

    def get_auth_desc(self, data):
        return "钉钉群“%s”的“%s”正在试图访问“%s”。\n\nchatbotUserId: %s" % (data['conversationTitle'], data['senderNick'], data['text']['content'], data['chatbotUserId'])

    async def async_handle(self, data):
        query = data['text']['content'].strip()
        if self.name:
            return await async_send(self.name, query)
        else:
            return await zhiChat(self.hass, query)

    def response(self, result):
        return {'msgtype': 'text', 'text': {'content': str(result)}}

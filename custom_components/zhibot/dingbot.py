
#
from .zhichat import zhiChat
from .basebot import basebot
from ..zhimsg import async_send

import logging
_LOGGER = logging.getLogger(__name__)


class dingbot(basebot):

    def check(self, request, data):
        if data['chatbotUserId'] in self.conf:
            return True
        return super().check(request, data)

    def config_done(self, data):
        self.conf.append(data['chatbotUserId'])

    def config_desc(self, data):
        return "钉钉群“%s”的“%s”正在试图访问“%s”。\n\nchatbotUserId: %s" % (data['conversationTitle'], data['senderNick'], data['text']['content'], data['chatbotUserId'])

    async def async_handle(self, data):
        query = data['text']['content'].strip()
        if self.name:
            return await async_send(self.name, query)
        else:
            return await zhiChat(self.hass, query)

    def response(self, answer):
        return self.json({'msgtype': 'text', 'text': {'content': answer}})

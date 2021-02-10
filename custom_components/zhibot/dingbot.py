
#
from .zhichat import zhiChat
from .chatbot import chatbotView

# Logging
import logging
_LOGGER = logging.getLogger(__name__)


#
class dingbotView(chatbotView):

    def config(self, data):
        if data['chatbotUserId'] in self.conf:
            return True
        return super().config(data)

    def config_done(self, data):
        self.conf.append(data['chatbotUserId'])

    def config_desc(self, data):
        return "钉钉群“%s”的“%s”正在试图访问“%s”。\n\nchatbotUserId: %s" % (data['conversationTitle'], data['senderNick'], data['text']['content'], data['chatbotUserId'])

    async def handle(self, data):
        return await self.handleChat(data['text']['content'].strip())

    async def handleChat(self, query):
        return await zhiChat(self.hass, query)

    def response(self, answer):
        return {'msgtype': 'text', 'text': {'content': answer}}

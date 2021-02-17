
#
from .zhichat import zhiChat
from .basebot import basebot
from ..zhimsg import async_send

import json
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
            result = await async_send(self.name, query)
            if result is None or isinstance(result, str):
                return result
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            return await zhiChat(self.hass, query)

    def response(self, result):
        return {'msgtype': 'text', 'text': {'content': result}}

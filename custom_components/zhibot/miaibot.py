# curl -k -H "Authorization: Bearer $HA_TOKEN" -d '{"conversationId": "conversationId", "atUsers": [{"dingtalkId": "dingtalkId"}], "chatbotUserId": "chatbotUserId", "msgId": "msgId", "senderNick": "Yonsm", "isAdmin": false, "sessionWebhookExpiredTime": 1613505952713, "createAt": 1613500552475, "conversationType": "2", "senderId": "senderId", "conversationTitle": "智能家庭", "isInAtList": true, "sessionWebhook": "sessionWebhook", "text": {"content": "您好"}, "msgtype": "text"}' "https://localhost:8123/er_tong_fang_yin_xiang?password=$ZHIBOT_PASS"
from .zhichat import zhiChat
from .basebot import basebot

import logging
_LOGGER = logging.getLogger(__name__)


class miaibot(basebot):

    def get_auth_user(self, data):
        return data['session']['application']['app_id']

    def get_auth_desc(self, data):
        return "小爱同学正在试图访问“%s”。\n\napp_id: %s”\nuser_id: %s" % (data['query'], data['session']['application']['app_id'], data['session']['user']['user_id'])

    async def post(self, request):
        self._open_mic = False
        return await super().post(request)

    async def async_handle(self, data):

        request = data['request']

        #
        if 'no_response' in request:
            self._open_mic = True
            return "主人，您还在吗？"

        #
        request_type = request['type']
        if request_type == 2:
            return "再见主人，我在这里等你哦！"

        #
        slot_info = data['request'].get('slot_info')
        intent_name = slot_info.get(
            'intent_name') if slot_info is not None else None
        if intent_name == 'Mi_Welcome':
            self._open_mic = True
            return "您好主人，我能为你做什么呢？"

        answer = await zhiChat(self.hass, data['query'])
        self._open_mic = answer == "未找到设备"
        return answer

    def response(self, result):
        return {
            'version': '1.0',
            'is_session_end': not self._open_mic,
            'response': {
                'open_mic': self._open_mic,
                'to_speak': {'type': 0, 'text': result},
                # 'to_display': {'type': 0,'text': text}
            }
        }

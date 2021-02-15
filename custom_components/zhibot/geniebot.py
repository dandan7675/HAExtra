from .genie import handleRequest
from .basebot import basebot

import logging
_LOGGER = logging.getLogger(__name__)


class geniebot(basebot):

    def access_token(self, data):
        return data['payload']['accessToken']

    async def async_handle(self, data):
        return await handleRequest(data)

    def response(self, answer):
        return self.json(answer)

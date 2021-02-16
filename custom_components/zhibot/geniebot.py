from custom_components.zhibot.oauthbot import oauthbot
from .genie import handleRequest, makeResponse
from .oauthbot import oauthbot

import logging
_LOGGER = logging.getLogger(__name__)


class geniebot(oauthbot):

    async def async_check_auth(self, data):
        return await self.async_check_token(data['payload']['accessToken'])

    async def async_handle(self, data):
        return await handleRequest(self.hass, data)

    def error(self, err):
        return makeResponse('ACCESS_TOKEN_INVALIDATE' if type(err) == PermissionError else 'SERVICE_ERROR')

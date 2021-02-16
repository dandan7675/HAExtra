from .genie import handleRequest, errorResult, makeResponse
from .basebot import basebot

import logging
_LOGGER = logging.getLogger(__name__)


class geniebot(basebot):

    async def async_check(self, request, data):
        self.data = data
        token = data['payload']['accessToken']
        return await self.hass.auth.async_validate_access_token(token) is not None

    async def async_handle(self, data):
        return await handleRequest(self.hass, data)

    def error(self, err):
        if type(err) == PermissionError:
            return errorResult('ACCESS_TOKEN_INVALIDATE')
        self.data = {}
        return errorResult('SERVICE_ERROR')

    def response(self, result):
        return makeResponse(self.data, result)

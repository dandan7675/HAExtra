from datetime import timedelta
from typing import Optional
#from homeassistant.helpers.state import AsyncTrackStates
import homeassistant.auth.models as models
from homeassistant.auth.const import ACCESS_TOKEN_EXPIRATION
from .genie import handleRequest
from .basebot import basebot

import logging
_LOGGER = logging.getLogger(__name__)

EXPIRE_HOURS = 8760  # 365天过期


class geniebot(basebot):

    def __init__(self, platform, hass, conf):
        super().__init__(platform, hass, conf)
        hass.auth._store.async_create_refresh_token = self.async_create_refresh_token

    async def async_config(self, data):
        payload = data['payload']
        accessToken = payload['accessToken']
        return await self.hass.auth.async_validate_access_token(accessToken) is not None

    async def async_handle(self, data):
        return 'TODO'

    def response(self, answer):
        return self.json(answer)

    async def async_create_refresh_token(self,
            user: models.User, client_id: Optional[str] = None,
            client_name: Optional[str] = None,
            client_icon: Optional[str] = None,
            token_type: str = models.TOKEN_TYPE_NORMAL,
            access_token_expiration: timedelta = ACCESS_TOKEN_EXPIRATION) -> models.RefreshToken:
        if access_token_expiration == ACCESS_TOKEN_EXPIRATION:
            access_token_expiration = timedelta(hours=EXPIRE_HOURS)
        _LOGGER.info('Access token expiration: %d hours', EXPIRE_HOURS)
        """Create a new token for a user."""
        kwargs = {
            'user': user,
            'client_id': client_id,
            'token_type': token_type,
            'access_token_expiration': access_token_expiration
        }  # type: Dict[str, Any]
        if client_name:
            kwargs['client_name'] = client_name
        if client_icon:
            kwargs['client_icon'] = client_icon

        refresh_token = models.RefreshToken(**kwargs)
        user.refresh_tokens[refresh_token.id] = refresh_token

        self.hass.auth._store._async_schedule_save()
        return refresh_token

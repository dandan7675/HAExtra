from typing import Optional
from datetime import timedelta
import homeassistant.auth.models as models
from homeassistant.auth.const import ACCESS_TOKEN_EXPIRATION
from .basebot import basebot

import logging
_LOGGER = logging.getLogger(__name__)

EXPIRE_HOURS = 8760  # 365*24


class oauthbot(basebot):

    def __init__(self, platform, hass, conf):
        super().__init__(platform, hass, conf)
        hass.auth._store.async_create_refresh_token = self.async_create_refresh_token

    async def async_config(self, data):
        access_token = self.get_access_token(data)
        return access_token and await self.hass.auth.async_validate_access_token(access_token) is not None

    def get_access_token(data):
        return None

    async def async_create_refresh_token(self, user, client_id=None, client_name=None, client_icon=None, token_type=models.TOKEN_TYPE_NORMAL, access_token_expiration=ACCESS_TOKEN_EXPIRATION):
        if access_token_expiration == ACCESS_TOKEN_EXPIRATION:
            access_token_expiration = timedelta(hours=EXPIRE_HOURS)
        kwargs = {
            'user': user,
            'client_id': client_id,
            'token_type': token_type,
            'access_token_expiration': access_token_expiration
        }
        if client_name:
            kwargs['client_name'] = client_name
        if client_icon:
            kwargs['client_icon'] = client_icon

        refresh_token = models.RefreshToken(**kwargs)
        user.refresh_tokens[refresh_token.id] = refresh_token

        self.hass.auth._store._async_schedule_save()
        return refresh_token

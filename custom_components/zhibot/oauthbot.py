from typing import Optional
from datetime import timedelta
import homeassistant.auth.models as models
from homeassistant.auth.const import ACCESS_TOKEN_EXPIRATION
from .basebot import basebot

import logging
_LOGGER = logging.getLogger(__name__)


class oauthbot(basebot):

    def init_auth(self, platform):
        # TODO: 这TMD到底是不是 OAuth 的最佳姿势？严重怀疑，我也不知道哪里抄来的姿势
        store = self.hass.auth._store
        self._async_create_refresh_token = store.async_create_refresh_token
        store.async_create_refresh_token = self.async_create_refresh_token

    async def async_create_refresh_token(
        self,
        user: models.User,
        client_id: Optional[str] = None,
        client_name: Optional[str] = None,
        client_icon: Optional[str] = None,
        token_type: str = models.TOKEN_TYPE_NORMAL,
        access_token_expiration: timedelta = ACCESS_TOKEN_EXPIRATION,
    ) -> models.RefreshToken:
        if access_token_expiration == ACCESS_TOKEN_EXPIRATION:
            access_token_expiration = timedelta(days=365)
        return await self._async_create_refresh_token(user, client_id, client_name, client_icon, token_type, access_token_expiration)

    async def async_check_token(self, token):
        return await self.hass.auth.async_validate_access_token(token) is not None

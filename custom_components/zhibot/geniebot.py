# TODO:
from .genie import handleRequest
from homeassistant.components.http import HomeAssistantView
from homeassistant.auth.const import ACCESS_TOKEN_EXPIRATION
import homeassistant.auth.models as models
from homeassistant.helpers.state import AsyncTrackStates
from typing import Optional
from datetime import timedelta

import logging
_LOGGER = logging.getLogger(__name__)


MAIN = 'genie'
DOMAIN = 'genie'
EXPIRE_HOURS = 8760  # 365天过期


async def async_setup(hass, config):
    global _hass
    _hass = hass
    hass.auth._store.async_create_refresh_token = async_create_refresh_token
    hass.http.register_view(AliGenieView)
    return True


class AliGenieView(HomeAssistantView):
    """View to handle Configuration requests."""

    url = '/genie'
    name = 'genie'
    requires_auth = False

    async def post(self, request):
        """Update state of entity."""
        data = await request.json()
        response = await handleRequest(data)
        return self.json(response)


async def async_create_refresh_token(
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

    _hass.auth._store._async_schedule_save()
    return refresh_token

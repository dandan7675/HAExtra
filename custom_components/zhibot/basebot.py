from homeassistant.util import slugify
from homeassistant.util.json import load_json, save_json
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.components.http import HomeAssistantView

import logging
_LOGGER = logging.getLogger(__package__)


class basebot(HomeAssistantView):
    """View to handle Configuration requests."""

    def __init__(self, platform, hass, conf):
        self.hass = hass
        self.name = slugify(conf['name']) if 'name' in conf else None

        self.url = '/' + (self.name or platform)
        self.requires_auth = False

        self.password = conf.get('password')
        info = "Serving on " + self.url
        if self.password:
            info += '?password=' + self.password
        else:
            self.init_auth(platform)
        _LOGGER.info(info)

    async def post(self, request):
        try:
            data = await request.json()
            _LOGGER.debug(f"REQUEST: %s", data)
            if await self.async_check(request, data):
                result = await self.async_handle(data)
            else:
                result = self.error(PermissionError("没有访问授权！"))
        except Exception as e:
            import traceback
            _LOGGER.error(traceback.format_exc())
            result = self.error(e)
        resp = self.response(result)
        _LOGGER.debug("RESPONSE: %s", resp)
        return self.json(resp)

    def response(self, result):
        return result

    def error(self, err):
        return str(err)

    async def async_handle(self, data):
        return self.error(NotImplementedError(f"未能处理：{data}"))

    async def async_check(self, request, data):
        if self.password:
            return self.password == request.query.get('password') or self.password == '*'
        return await self.async_check_auth(data)

    def init_auth(self, platform):
        self._auth_ui = None
        self._auth_path = self.hass.config.path(STORAGE_DIR, platform)
        self._auth_users = load_json(self._auth_path) or []

    async def async_check_auth(self, data):
        return self.check_auth(data)

    def check_auth(self, data):
        user = self.get_auth_user(data)
        if not user:
            return False
        if user in self._auth_users:
            return True

        configurator = self.hass.components.configurator
        if self._auth_ui:
            configurator.async_request_done(self._auth_ui)

        def config_callback(fields):
            configurator.request_done(self._auth_ui)
            self._auth_ui = None

            _LOGGER.debug(fields)
            if fields.get('agree') == 'ok':
                self.auth_users.append(user)
                save_json(self._auth_path, self.auth_users)

        self._auth_ui = configurator.async_request_config(
            '智加加', config_callback,
            description=self.get_auth_desc(data),
            submit_caption='完成',
            fields=[{'id': 'agree', 'name': '如果允许访问，请输入“ok”'}],
        )
        return False

    def get_auth_desc(self, data):
        return f"授权访问：{data}"

    def get_auth_user(self, data):
        return None

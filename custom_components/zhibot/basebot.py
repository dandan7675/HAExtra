from homeassistant.util import slugify
from homeassistant.util.json import load_json, save_json
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.components.http import HomeAssistantView
# from homeassistant.components.http import KEY_HASS

import logging
_LOGGER = logging.getLogger(__package__)


class basebot(HomeAssistantView):
    """View to handle Configuration requests."""

    def __init__(self, platform, hass, conf):
        self.platform = platform
        self.hass = hass
        self.name = slugify(conf['name']) if 'name' in conf else None
        self.password = conf.get('password')

        if self.password is None:  # Auth: config UI confirmation, intead of pre shared password
            self._configuring = None
            self.conf = load_json(hass.config.path(STORAGE_DIR, platform))
            if not self.conf:
                self.conf = []

        self.url = '/' + (self.name or platform)
        self.requires_auth = False
        _LOGGER.debug(f"Serving on {self.url}")

    async def post(self, request):
        try:
            # request[KEY_REAL_IP]
            # request.app[KEY_HASS]
            data = await request.json()
            _LOGGER.debug("REQUEST: %s", data)
            answer = await self.async_handle(data) if await self.async_check(request, data) else "没有访问授权！"
        except:
            import traceback
            _LOGGER.error(traceback.format_exc())
            answer = "程序出错啦！"
        _LOGGER.debug("RESPONSE: %s", answer)
        return self.response(answer)

    def response(self, answer):
        return answer

    async def async_handle(self, data):
        return "未能处理"

    async def async_check(self, request, data):
        access_token = self.access_token(data)
        if access_token is not None:
            return await self.hass.auth.async_validate_access_token(access_token) is not None
        return await self.hass.async_add_executor_job(self.check, request, data)

    def access_token(data):
        return None

    def check(self, request, data):
        if self.password is not None:
            return self.password == request.query.get('password') or self.password == ''
        return self.config(data)

    def config(self, data):
        configurator = self.hass.components.configurator
        if self._configuring:
            configurator.async_request_done(self._configuring)

        def config_callback(fields):
            configurator.request_done(self._configuring)
            self._configuring = None

            _LOGGER.debug(fields)
            if fields.get('agree') == 'ok':
                self.config_done(data)
                save_json(self.hass.config.path('.' + self.platform), self.conf)

        self._configuring = configurator.async_request_config(
            '智加加', config_callback,
            description=self.config_desc(data),
            submit_caption='完成',
            fields=[{'id': 'agree', 'name': '如果允许访问，请输入“ok”'}],
        )
        return False

    def config_done(self, data):
        pass

    def config_desc(self, data):
        return "授权访问"

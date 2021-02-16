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
        _LOGGER.debug(f"Serving on {self.url}")

        self.password = conf.get('password')
        if self.password is None:  # Auth: config UI confirmation, intead of pre shared password
            self.config_id = None
            self.config_path = hass.config.path(STORAGE_DIR, platform)
            self.config_users = load_json(self.config_path) or []

    async def post(self, request):
        try:
            # from homeassistant.components.http import KEY_HASS
            # request[KEY_REAL_IP]
            # request.app[KEY_HASS]
            data = await request.json()
            _LOGGER.debug("REQUEST: %s", data)
            result = await self.async_handle(data) if await self.async_check(request, data) else self.error(PermissionError("没有访问授权！"))
        except Exception as e:
            import traceback
            _LOGGER.error(traceback.format_exc())
            result = self.error(e)
        resp = self.response(result)
        _LOGGER.debug("RESPONSE: %s", resp)
        return self.json(resp)

    def response(self, result):
        return [result]

    def error(self, err):
        return str(err)

    async def async_handle(self, data):
        return self.error(NotImplementedError('未能处理'))

    async def async_check(self, request, data):
        return self.check_password(request) if self.password is not None else self.check_config(data)

    def check_password(self, request):
        return self.password == request.query.get('password') or self.password == '*'

    def check_config(self, data, desc="授权访问"):
        configurator = self.hass.components.configurator
        if self.config_id:
            configurator.async_request_done(self.config_id)

        def config_callback(fields):
            configurator.request_done(self.config_id)
            self.config_id = None

            _LOGGER.debug(fields)
            if fields.get('agree') == 'ok':
                self.config_ok(data)
                save_json(self.config_path, self.config_users)

        self.config_id = configurator.async_request_config(
            '智加加', config_callback,
            description=desc,
            submit_caption='完成',
            fields=[{'id': 'agree', 'name': '如果允许访问，请输入“ok”'}],
        )
        return False

    def config_ok(self, data):
        pass

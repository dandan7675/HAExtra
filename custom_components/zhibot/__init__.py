import importlib

DOMAIN = 'zhibot'

async def async_setup(hass, config):
    for conf in config.get(DOMAIN):
        platform = conf['platform'] + 'bot'
        mod = importlib.import_module('.' + platform, __package__)
        view = getattr(mod, platform + 'View')
        hass.http.register_view(view(platform, hass, conf))
    return True

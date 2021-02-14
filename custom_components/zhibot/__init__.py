from importlib import import_module

DOMAIN = 'zhibot'

async def async_setup(hass, config):
    for conf in config.get(DOMAIN):
        platform = conf['platform'] + 'bot'
        module = import_module('.' + platform, __package__)
        Class = getattr(module, platform + 'View')
        hass.http.register_view(Class(platform, hass, conf))
    return True

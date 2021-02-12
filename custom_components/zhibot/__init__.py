import importlib

DOMAIN = 'zhibot'

async def async_setup(hass, config):
    confs = config.get(DOMAIN)
    if confs:
        for conf in confs:
            platform = conf['platform'] + 'bot'
            mod = importlib.import_module('.' + platform, __package__)
            view = getattr(mod, platform + 'View')
            hass.http.register_view(view(platform, hass, conf))
    return True

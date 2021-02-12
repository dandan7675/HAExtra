import importlib
import logging
_LOGGER = logging.getLogger(__name__)

DOMAIN = 'zhibot'


async def async_setup(hass, config):
    confs = config.get(DOMAIN)
    if confs:
        http = config.get('http')
        base_url = http.get('base_url', '') if http else ''
        for conf in confs:
            platform = conf['platform'] + 'bot'
            mod = importlib.import_module('.' + platform, __package__)
            view = getattr(mod, platform + 'View')
            hass.http.register_view(view(hass, conf))
            _LOGGER.debug("Listing on: %s/%s", base_url, platform)
    return True

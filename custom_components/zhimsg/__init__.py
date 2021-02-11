import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.util import slugify
from homeassistant.components.input_text import (InputText, CONF_MIN, CONF_MIN_VALUE, CONF_MAX, CONF_MAX_VALUE, CONF_INITIAL, MODE_TEXT, SERVICE_SET_VALUE, ATTR_VALUE)
from homeassistant.const import (CONF_ID, CONF_NAME, CONF_ICON, CONF_MODE)


# Logging
import logging
_LOGGER = logging.getLogger(__name__)

DOMAIN = 'zhimsg'
_handlers = {}
_hass = None

async def async_setup(hass, config):
    global _hass
    _hass = hass
    _confs = config.get(DOMAIN)
    if _confs:
        import importlib
        global _handlers
        entities = []
        for conf in _confs:
            if 'name' in conf:
                name = conf['name']
                uniquey_id = slugify(name)
                config = {
                    CONF_ID: uniquey_id,
                    CONF_NAME: name,
                    CONF_MIN: CONF_MIN_VALUE,
                    CONF_MAX: CONF_MAX_VALUE,
                    # CONF_INITIAL: name,
                    CONF_ICON: 'mdi:account-tie-voice',
                    CONF_MODE: MODE_TEXT
                }
                input_text = InputText(config)
                input_text.entity_id = f"input_text.{uniquey_id}"
                input_text.editable = False
                entities.append(input_text)
                hass.helpers.event.async_track_state_change_event([input_text.entity_id], async_text_changed)

            platform = conf['platform']
            parts = platform.split('_')
            handler = parts[0] + 'msg'
            service = uniquey_id if name else platform
            mod = importlib.import_module('.' + handler, __package__)
            _handlers[service] = getattr(mod, handler)(hass, conf)
            SERVICE_SCHEMA = getattr(mod, 'SERVICE_SCHEMA')
            hass.services.async_register(DOMAIN, service, async_send, schema=SERVICE_SCHEMA)
            _LOGGER.debug("Register service: %s.%s", DOMAIN, service)

        if len(entities):
            from homeassistant.helpers.entity_component import EntityComponent
            component = EntityComponent(_LOGGER, 'input_text', hass)
            await component.async_add_entities(entities)
            component.async_register_entity_service(SERVICE_SET_VALUE, {vol.Required(ATTR_VALUE): cv.string}, 'async_set_value')

    return True


def async_text_changed(event):
    data = event.data
    old_state = data.get('old_state')
    new_state = data.get('new_state')
    if old_state and new_state:
        text = new_state.state
        if text != old_state.state:
            entity_id = data['entity_id']
            service = entity_id[entity_id.find('.') + 1:]
            _hass.add_job(async_send_message(service, text))


async def async_send(call):
    handler = _handlers[call.service]
    data = call.data
    message = data.get('message')
    await handler.async_send_message(message, data)


async def async_send_message(service, message, data={}):
    await _handlers[service].async_send_message(message, data)

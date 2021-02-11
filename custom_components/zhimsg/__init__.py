import importlib
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


async def async_setup(hass, config):
    _confs = config.get(DOMAIN)
    if not _confs:
        return True

    entities = []
    global _handlers
    for conf in _confs:
        name = conf.get('name')
        platform = conf['platform']
        if name:
            service = slugify(name)
            entities.append(create_input_entity(hass, name, service))
        else:
            service = platform
        parts = platform.split('_')
        handler = parts[0] + 'msg'
        mod = importlib.import_module('.' + handler, __package__)
        _handlers[service] = getattr(mod, handler)(hass, conf)
        SERVICE_SCHEMA = getattr(mod, 'SERVICE_SCHEMA')
        hass.services.async_register(DOMAIN, service, async_send, schema=SERVICE_SCHEMA)
        _LOGGER.debug("Register service: %s.%s", DOMAIN, service)

    if len(entities):
        await async_add_input_entities(hass, entities)
    return True


async def async_send(call):
    handler = _handlers[call.service]
    data = call.data
    message = data.get('message')
    await handler.async_send_message(message, data)


async def async_send_message(service, message, data={}):
    await _handlers[service].async_send_message(message, data)


def create_input_entity(hass, name, uniquey_id):
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
    hass.helpers.event.async_track_state_change_event([input_text.entity_id], async_input_changed)
    return input_text


async def async_input_changed(event):
    data = event.data
    old_state = data.get('old_state')
    new_state = data.get('new_state')
    if old_state and new_state:
        text = new_state.state
        if text != old_state.state:
            entity_id = data['entity_id']
            service = entity_id[entity_id.find('.') + 1:]
            await async_send_message(service, text)


async def async_add_input_entities(hass, entities):
    from homeassistant.helpers.entity_component import EntityComponent
    component = EntityComponent(_LOGGER, 'input_text', hass)
    await component.async_add_entities(entities)
    component.async_register_entity_service(SERVICE_SET_VALUE, {vol.Required(ATTR_VALUE): cv.string}, 'async_set_value')

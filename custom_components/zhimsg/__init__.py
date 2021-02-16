from homeassistant.core import HomeAssistant
import voluptuous as vol
from random import randint
from importlib import import_module
import homeassistant.helpers.config_validation as cv
from homeassistant.util import slugify
from homeassistant.util.yaml import load_yaml
from homeassistant.components.input_text import (InputText, CONF_MIN, CONF_MIN_VALUE, CONF_MAX, CONF_MAX_VALUE, CONF_INITIAL, MODE_TEXT, SERVICE_SET_VALUE, ATTR_VALUE)
from homeassistant.const import (CONF_ID, CONF_NAME, CONF_ICON, CONF_MODE)

import logging
_LOGGER = logging.getLogger(__name__)

DOMAIN = 'zhimsg'
SERVICES = {}

SERVICE_SCHEMA = vol.Schema({
    vol.Required('message'): cv.string,
})


async def async_setup(hass: HomeAssistant, config):
    global SERVICES
    entities = []
    Classes = {}
    descriptions = load_yaml(hass.config.path('custom_components/zhimsg/services.yaml'))
    for conf in config.get(DOMAIN):
        service = conf['platform']
        platform = service.split('_')[0]
        Class = Classes.get(platform)
        if Class is None:
            attr = platform + 'msg'
            module = import_module('.' + attr, __package__)
            Class = getattr(module, attr)
            Classes[platform] = Class
            SERVICES[platform] = []
            hass.services.async_register(DOMAIN, platform, async_call, schema=SERVICE_SCHEMA)
            _LOGGER.debug("Platform Service as %s.%s", DOMAIN, platform)
        instance = Class(hass, conf)
        SERVICES[platform].append(instance)

        name = conf.get('name')
        if name:
            service = slugify(name)
            examples = descriptions.get(platform, {}).get('fields', {}).get('message', {}).get('example', '您好').split('|')
            initial_text = examples[randint(0, len(examples) - 1)]
            entities.append(create_input_entity(hass, name, service, initial_text))
        if service not in SERVICES:
            SERVICES[service] = instance
            _LOGGER.debug("Service as %s.%s", DOMAIN, platform)
            hass.services.async_register(DOMAIN, service, async_call, schema=SERVICE_SCHEMA)

    if len(entities):
        await async_add_input_entities(hass, config, entities)
    return True


async def async_call(call):
    data = call.data
    message = data.get('message')
    await async_send(call.service, message, data)


async def async_send(service, message, data={}):
    try:
        instance = SERVICES[service]
        if type(instance) == list:
            error = None
            for inst in instance:
                err = await inst.async_send(message, data)
                if err:
                    error = err
        else:
            error = await instance.async_send(message, data)
    except Exception as e:
        error = e
    if error:
        _LOGGER.error(error)
    return error


def create_input_entity(hass, name, service, initial_text):
    config = {
        CONF_ID: service,
        CONF_NAME: name,
        CONF_MIN: CONF_MIN_VALUE,
        CONF_MAX: CONF_MAX_VALUE,
        CONF_INITIAL: initial_text,
        CONF_ICON: 'mdi:account-tie-voice',
        CONF_MODE: MODE_TEXT
    }
    entity = InputText(config)
    entity.entity_id = f"input_text.{service}"
    #entity.editable = False
    return entity


async def async_input_changed(event):
    data = event.data
    old_state = data.get('old_state')
    new_state = data.get('new_state')
    if old_state and new_state:
        message = new_state.state
        if message != old_state.state:
            entity_id = data['entity_id']
            service = entity_id[entity_id.find('.') + 1:]
            await async_send(service, message)


async def async_add_input_entities(hass, config, entities):
    if 'input_text' not in config:
        return await _async_add_input_entities(hass, entities)

    # 如果配置了文本输入，则必须延迟等待，并复用现有的组件来添加
    async def _delay_add_input_entities(timestamp=None):
        await _async_add_input_entities(hass, entities)
    hass.helpers.event.async_call_later(5, _delay_add_input_entities)


async def _async_add_input_entities(hass, entities):
    from homeassistant.helpers.entity_component import EntityComponent
    component = hass.data.get('entity_components', {}).get('input_text')
    if component is None:
        component = EntityComponent(_LOGGER, 'input_text', hass)
        component.async_register_entity_service(SERVICE_SET_VALUE, {vol.Required(ATTR_VALUE): cv.string}, 'async_set_value')
    await component.async_add_entities(entities)
    hass.helpers.event.async_track_state_change_event([entity.entity_id for entity in entities], async_input_changed)

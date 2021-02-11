#!/usr/bin/env python3
# encoding: utf-8

from .micloud import MIoTCloud
from custom_components.zhimsg.micloud import MIoTCloud
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import aiohttp_client
import voluptuous as vol

import logging
_LOGGER = logging.getLogger(__name__)

# Config validation
SERVICE_SCHEMA = vol.All(
    vol.Schema({
        vol.Optional('message'): cv.string,
        vol.Optional('volume'): vol.Range(min=0, max=100),
        vol.Optional('devno'): vol.Range(min=-1, max=9),
    }),
    cv.has_at_least_one_key("message", "volume"),
)


class miaimsg(MIoTCloud):

    def __init__(self, hass, conf):
        super().__init__(aiohttp_client.async_get_clientsession(hass), conf['username'], conf['password'])
        self.devices = None

    async def async_send_message(self, message, data):
        if self._devices is None:
            self._devices = await miai_login(self._miid, self._password)
            # _LOGGER.debug("miai_login: %s", self._devices)
        if self._devices is None:
            return False

        devno = data.get('devno', 0)
        volume = data.get('volume')
        if message or volume:
            await miai_send_message3(self._devices, devno, message, volume)


params = {
            'did':  did or self._cloud.get("did") or f'action-{siid}-{aiid}',
            'siid': siid,
            'aiid': aiid,
            'in':   params2 or [],
        }

        try:
            if not self._cloud_write:
                result = await self._try_command(
                    f"Calling action for {self._name} failed.",
                    self._device.send,
                    "action",
                    params,
                )
                if result:
                    return True
            else:
                result = await self._cloud_instance.call_action(
                    json.dumps({
                        'params': params or []
                    })

# class MiNASession:
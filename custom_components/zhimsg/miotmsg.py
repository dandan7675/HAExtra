#!/usr/bin/env python3
# encoding: utf-8

from .micloud import MiAccount, MiCloud
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
        # vol.Optional('region'): cv.string,
    }),
    cv.has_at_least_one_key("message", "volume"),
)


class miotmsg(MiCloud):

    def __init__(self, hass, conf):
        account = MiAccount(aiohttp_client.async_get_clientsession(hass), conf['username'], conf['password'])
        super().__init__(account, conf.get('region'))
        self.did = str(conf.get('did'))
        self.devices = None

    async def async_send_message(self, message, data):
        devno = data.get('devno', 0)
        volume = data.get('volume')
        params = {
            'did': self.did,
            'siid': 5,
            'aiid': 1,
            'in': [message],
        }
        await self.miot_action(params)

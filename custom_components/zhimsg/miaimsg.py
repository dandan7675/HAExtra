#!/usr/bin/env python3
# encoding: utf-8

import json
import aiohttp
import os
import re
import random
import string
import hashlib
import time
import base64
from urllib import parse

import logging
_LOGGER = logging.getLogger(__name__)
_session = None


async def miai_request(url, data=None):
    try:
        requestId = ''.join(random.sample(string.ascii_letters + string.digits, 30))
        url += "&requestId=" + requestId
        async with _session.post(url, data=data) if data is not None else _session.get(url) as response:
            return await response.json()
    except BaseException:
        import traceback
        _LOGGER.error(traceback.format_exc())
    return False


async def miai_ubus(deviceId, method, path, message):
    url = "https://api.mina.mi.com/remote/ubus?deviceId=%s&message=%s&method=%s&path=%s" % (
        deviceId, parse.quote(json.dumps(message, ensure_ascii=False)), method, path)
    result = await miai_request(url, '')
    if result:
        code = result.get('code')
        if code == 0:  # Success
            return True
        # elif code == 100: # ubus error
        #     pass
        # elif code == 1000: # Unauthorized
        #     _LOGGER.error('Unauthorized')
        else:
            _LOGGER.error(result)
    return False


async def miai_text_to_speech(deviceId, text):
    return await miai_ubus(deviceId, 'text_to_speech', 'mibrain', {'text': text})


async def miai_player_set_volume(deviceId, volume):
    return await miai_ubus(deviceId, 'player_set_volume', 'mediaplayer', {'volume': volume, 'media': 'app_ios'})


async def miai_login(miid, password):
    global _session
    _session = aiohttp.ClientSession()

    sign = await miai_serviceLogin()
    if sign is None:
        return None

    auth_result = await miai_serviceLoginAuth2(miid, password, sign)
    if auth_result is None:
        return None

    login_success = await miai_login_miai(auth_result.get('location'), auth_result.get('nonce'), auth_result.get('ssecurity'))
    if not login_success:
        return None

    return await miai_device_list()


async def miai_serviceLogin():
    url = 'https://account.xiaomi.com/pass/serviceLogin?sid=micoapi'
    pattern = re.compile(r'_sign=(.*?)&')
    try:
        async with _session.get(url, allow_redirects=False) as response:
            text = await response.text()
            sign = pattern.findall(text)[0]
            return parse.unquote(sign)
    except BaseException:
        import traceback
        _LOGGER.error(traceback.format_exc())
        return None


async def miai_serviceLoginAuth2(miid, password, sign, captCode=None, ick=None):
    url = 'https://account.xiaomi.com/pass/serviceLoginAuth2'
    data = {
        '_json': 'true',
        '_sign': sign,
        'callback': 'https://api.mina.mi.com/sts',
        'hash': hashlib.md5(password.encode('utf-8')).hexdigest().upper(),
        'qs': '%3Fsid%3Dmicoapi',
        'serviceParam': '{"checkSafePhone":false}',
        'sid': 'micoapi',
        'user': miid
    }
    if captCode:
        url += '?_dc=' + str(int(round(time.time() * 1000)))
        data['captCode'] = captCode
        #_headers['Cookie'] += '; ick=' + ick

    try:
        async with _session.post(url, data=data) as response:
            text = await response.text()
            result = json.loads(text[11:])
            code = result['code']
            if code == 0:
                return result
            elif code == 87001:
                _LOGGER.error('Need capt code')
            elif code == 70016:
                _LOGGER.error('Incorrect password')
            else:
                _LOGGER.error(result)
    except BaseException as e:
        import traceback
        _LOGGER.error(traceback.format_exc())
    return None


async def miai_login_miai(url, nonce, ssecurity):
    token = 'nonce=' + str(nonce) + '&' + ssecurity
    sha1 = hashlib.sha1(token.encode('utf-8')).digest()
    clientSign = base64.b64encode(sha1)
    url += '&clientSign=' + parse.quote(clientSign.decode())
    try:
        async with _session.get(url) as response:
            return response.status == 200
    except BaseException:
        import traceback
        _LOGGER.error(traceback.format_exc())
        return False


async def miai_device_list():
    url = 'https://api.mina.mi.com/admin/v2/device_list?master=1'
    result = await miai_request(url)
    return result.get('data') if result else None


async def miai_send_message(deviceId, message, volume=None):
    result = True if volume is None else await miai_player_set_volume(deviceId, volume)
    if result and message:
        result = await miai_text_to_speech(deviceId, message)
    if not result:
        _LOGGER.error("Send failed: %s %s", message, volume)
    return result


async def miai_send_message2(devices, index, message, volume=None):
    deviceId = devices[index]['deviceID']
    result = await miai_send_message(deviceId, message, volume)
    if not result:
        result = await miai_send_message(deviceId, message, volume)
    return result


async def miai_send_message3(devices, devno, message, volume=None):
    if devno is not None and devno != -1:
        return await miai_send_message2(devices, devno, message, volume) 
    result = False
    for i in range(0, len(devices)):
        if devno is None and not devices[i]['capabilities'].get('yunduantts'):
            continue
        result = await miai_send_message2(devices, i, message, volume)
        if not result or devno is None:
            break
    return result


async def test():
    PY_DIR = os.path.split(os.path.realpath(__file__))[0]
    with open(PY_DIR + '/../../secrets.yaml') as f:
        lines = f.readlines()
    miid = None
    password = None
    for line in lines:
        if line.startswith('miai_miid:'):
            miid = line[10:-1].strip()
        elif line.startswith('miai_password:'):
            password = line[14:-1].strip()
    devices = await miai_login(miid, password)
    if devices:
        import sys
        await miai_send_message3(devices, None, sys.argv[1] if len(sys.argv) > 1 else "测试")
    await _session.close()


if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
    loop.close()
    exit(0)

# Config validation
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

SERVICE_SCHEMA = vol.All(
    vol.Schema({
        vol.Optional('message'): cv.string,
        vol.Optional('volume'): vol.Range(min=0, max=100),
        vol.Optional('devno'): vol.Range(min=0, max=9),
    }),
    cv.has_at_least_one_key("message", "volume"),
)


class miaimsg(object):

    def __init__(self, hass, conf):
        self._miid = str(conf['miid'])
        self._password = conf.get('password')
        self._devices = None

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

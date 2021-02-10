# The base logic was taken from project https://github.com/squachen/micloud

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import random
import string
import time

from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)

REGIONS = ['cn', 'de', 'i2', 'ru', 'sg', 'us']
UA = "Android-7.1.1-1.0.0-ONEPLUS A3010-136-%s APP/xiaomi.smarthome APPV/62830"


def get_random_string(length):
    seq = string.ascii_uppercase + string.digits
    return ''.join((random.choice(seq) for _ in range(length)))


def gen_nonce():
    """Time based nonce."""
    nonce = os.urandom(8) + int(time.time() / 60).to_bytes(4, 'big')
    return base64.b64encode(nonce).decode()


def gen_signed_nonce(ssecret, nonce=gen_nonce()):
    """Nonce signed with ssecret."""
    m = hashlib.sha256()
    m.update(base64.b64decode(ssecret))
    m.update(base64.b64decode(nonce))
    return base64.b64encode(m.digest()).decode()


def gen_signature(url, signed_nonce, nonce, data):
    """Request signature based on url, signed_nonce, nonce and data."""
    sign = '&'.join([url, signed_nonce, nonce, 'data=' + data])
    signature = hmac.new(key=base64.b64decode(signed_nonce),
                         msg=sign.encode(),
                         digestmod=hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

def server_url(region):
    assert region in REGIONS, "Wrong region: " + region
    return 'https://' + ('' if region is None or region == 'cn' else region + '.') + 'api.io.mi.com/app'

class MiCloud:

    def __init__(self, session, username, password, user_id=None, ssecurity=None, service_token=None):
        self.device_id = get_random_string(16)
        self.session = session
        self.username = username
        self.password = password
        self.user_id = user_id
        self.ssecurity = ssecurity
        self.service_token = service_token

    def ensure_login(self):
        if self.service_token is None:
            return self.login()
        return True

    async def login(self):
        try:
            payload = await self.login1()
            data = await self.login2(payload)
            if not data['location']:
                return False
            self.service_token = await self.login3(data['location'])
            self.user_id = data['userId']
            self.ssecurity = data['ssecurity']
            return True

        except Exception as e:
            _LOGGER.exception(f"Can't login to Mi Cloud: {e}")
            return False

    async def login1(self):
        r = await self.session.get('https://account.xiaomi.com/pass/serviceLogin',
                                   cookies={'sdkVersion': '3.8.6', 'deviceId': self.device_id},
                                   headers={'User-Agent': UA % self.device_id},
                                   params={'sid': 'xiaomiio', '_json': 'true'})
        raw = await r.read()
        resp = json.loads(raw[11:])
        _LOGGER.debug(f"MiCloud step1: %s", resp)
        return {k: v for k, v in resp.items() if k in ('sid', 'qs', 'callback', '_sign')}

    async def login2(self, payload):
        payload['user'] = self.username
        payload['hash'] = hashlib.md5(self.password.encode()).hexdigest().upper()
        r = await self.session.post('https://account.xiaomi.com/pass/serviceLoginAuth2',
                                    cookies={'sdkVersion': '3.8.6', 'deviceId': self.device_id},
                                    data=payload,
                                    headers={'User-Agent': UA % self.device_id},
                                    params={'_json': 'true'})
        raw = await r.read()
        resp = json.loads(raw[11:])
        _LOGGER.debug(f"MiCloud step2: %s", resp)
        return resp

    async def login3(self, location):
        r = await self.session.get(location, headers={'User-Agent': UA})
        service_token = r.cookies['serviceToken'].value
        _LOGGER.debug(f"MiCloud step3: %s", service_token)
        return service_token

    def sign(self, uri, data):
        nonce = gen_nonce()
        signed_nonce = gen_signed_nonce(self.ssecurity, nonce)
        signature = gen_signature(uri, signed_nonce, nonce, data)
        return {'signature': signature, '_nonce': nonce, 'data': data}

    async def get_devices(self, region=None):
        if not self.ensure_login():
            return None

        uri = '/home/device_list'
        data = '{"getVirtualModel":false, "getHuamiDevices":0}'

        try:
            r = await self.session.post(server_url(region) + uri, cookies={
                'userId': self.auth['user_id'],
                'serviceToken': self.auth['service_token'],
                'locale': 'en_US'
            }, headers={
                'User-Agent': UA,
                'x-xiaomi-protocal-flag-cli': 'PROTOCAL-HTTP2'
            }, data=self.sign(uri, data), timeout=10)
            resp = await r.json(content_type=None)
            assert resp['code'] == 0, resp
            return resp['result']['list']

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout while loading MiCloud device list")
        except Exception as e:
            _LOGGER.exception(f"Can't load devices list {e}")

        return None

    async def get_total_devices(self, regions):
        total = []
        for region in regions:
            devices = await self.get_devices(region)
            if devices is None:
                return None
            total += devices
        return total


class MIoTCloud:

    async def request(self, api, params=None, region=None):
        uri = "/miotspec/" + api
        try:
            r = await self.session.post(server_url(region) + url, cookies={
                'userId': self.auth['user_id'],
                'serviceToken': self.auth['service_token'],
            }, headers={
                'User-Agent': UA,
                'x-xiaomi-protocal-flag-cli': 'PROTOCAL-HTTP2'
            }, data=self.sign(uri, params), timeout=10)

            resp = await r.json(content_type=None)
            if resp.get('message') == 'auth err':
                _LOGGER.error("Auth error")
                return None
            elif resp.get('code') != 0:
                _LOGGER.error(f"Response of {api} from cloud: {resp}")
                return resp
            else:
                _LOGGER.info(f"Response of {api} from cloud: {resp}")
                return resp

        except asyncio.TimeoutError:
            _LOGGER.error(f"Timeout while requesting MIoT api: {api}")
        except Exception as e:
            _LOGGER.exception(f"Can't load devices list: {e}")

    async def get_prop(self, params=''):
        return await self.request('prop/get', params)

    async def set_prop(self, params=''):
        return await self.request('prop/set', params)

    async def action(self, params=''):
        return await self.request('action', params)

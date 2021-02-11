#!/usr/bin/env python3
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

#REGIONS = ['cn', 'de', 'i2', 'ru', 'sg', 'us']
UA = "Android-7.1.1-1.0.0-ONEPLUS A3010-136-%s APP/xiaomi.smarthome APPV/62830"


def get_random(length):
    seq = string.ascii_uppercase + string.digits
    return ''.join((random.choice(seq) for _ in range(length)))


def gen_nonce():
    """Time based nonce."""
    nonce = os.urandom(8) + int(time.time() / 60).to_bytes(4, 'big')
    return base64.b64encode(nonce).decode()


def gen_signed_nonce(ssecret, nonce):
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


class MiAccount:

    def __init__(self, session: ClientSession, username, password, user_id=None, ssecurity=None, service_token=None):
        self.device_id = get_random(16)
        self.session = session
        self.username = username
        self.password = password
        self.user_id = user_id
        self.ssecurity = ssecurity
        self.service_token = service_token

    async def ensure_login(self):
        if self.service_token is None:
            return await self.login()
        return True

    async def re_login(self):
        self.user_id = None
        self.ssecurity = None
        self.service_token = None
        return await self.login()

    async def login(self):
        try:
            payload = await self._login1()
            data = await self._login2(payload)
            location = data['location']
            if not location:
                return False
            self.service_token = await self._login3(location)
            self.user_id = data['userId']
            self.ssecurity = data['ssecurity']
            return True

        except Exception as e:
            _LOGGER.exception(f"Exception on login {self.username}: {e}")
            return False

    async def _login1(self):
        r = await self.session.get('https://account.xiaomi.com/pass/serviceLogin',
                                   cookies={'sdkVersion': '3.8.6', 'deviceId': self.device_id},
                                   headers={'User-Agent': UA % self.device_id},
                                   params={'sid': 'xiaomiio', '_json': 'true'})
        raw = await r.read()
        resp = json.loads(raw[11:])
        _LOGGER.debug(f"MiCloud step1: %s", resp)
        return {k: v for k, v in resp.items() if k in ('sid', 'qs', 'callback', '_sign')}

    async def _login2(self, payload):
        payload['user'] = str(self.username)
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

    async def _login3(self, location):
        r = await self.session.get(location, headers={'User-Agent': UA})
        service_token = r.cookies['serviceToken'].value
        _LOGGER.debug(f"MiCloud step3: %s", service_token)
        return service_token


class MiCloud:

    def __init__(self, account, region=None):
        self.account = account
        self.server = 'https://' + ('' if region is None or region == 'cn' else region + '.') + 'api.io.mi.com/app'

    def sign(self, uri, params):
        data = params if type(params) == str else json.dumps(params)
        nonce = gen_nonce()
        signed_nonce = gen_signed_nonce(self.account.ssecurity, nonce)
        signature = gen_signature(uri, signed_nonce, nonce, data)
        return {'signature': signature, '_nonce': nonce, 'data': data}

    # class ResultError(Exception): ...
        
    async def _request(self, uri, params=''):
        try:
            r = await self.account.session.post(self.server + uri, cookies={
                'userId': self.account.user_id,
                'serviceToken': self.account.service_token,
                # 'locale': 'en_US'
            }, headers={
                'User-Agent': UA,
                'x-xiaomi-protocal-flag-cli': 'PROTOCAL-HTTP2'
            }, data=self.sign(uri, params), timeout=10)
            return await r.json(content_type=None)
        except asyncio.TimeoutError:
            _LOGGER.error(f"Timeout on request {uri}")
        except Exception as e:
            _LOGGER.exception(f"Exception on request {uri}: {e}")

        return None

    async def request(self, uri, params=''):
        if not await self.account.ensure_login():
            return None
        resp = await self._request(uri, params)
        code = resp.get('code')
        if code == 0:
            return resp.get('result')
        _LOGGER.error(f"Error on request {uri}: {resp}")
        if code == 2 and await self.account.re_login():
            resp = await self._request(uri, params)
            if resp.get('code') == 0:
                return resp.get('result')
        return None

    async def device_list(self):
        uri = '/home/device_list'
        params = {"getVirtualModel": False, "getHuamiDevices": 0}
        result = await self.request(uri, params)
        return result.get('list') if result else None

    async def miotspec(self, api, params=''):
        return await self.request('/miotspec/' + api, params)

    async def miot_prop_get(self, params=''):
        return await self.miotspec('prop/get', params)

    async def miot_prop_set(self, params=''):
        return await self.miotspec('prop/set', params)

    async def miot_action(self, params=''):
        return await self.miotspec('action', params)


async def test():
    PY_DIR = os.path.split(os.path.realpath(__file__))[0]
    with open(PY_DIR + '/../../secrets.yaml') as f:
        lines = f.readlines()
    username = None
    password = None
    for line in lines:
        if line.startswith('mi_username:'):
            username = line[12:-1].strip()
        elif line.startswith('mi_password:'):
            password = line[12:-1].strip()
            if username:
                break
    async with ClientSession() as session:
        cloud = MiCloud(MiAccount(session, username, password))
        print(json.dumps(await cloud.device_list(), indent=2, ensure_ascii=False))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
    loop.close()
    exit(0)

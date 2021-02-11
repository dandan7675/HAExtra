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


class MiAuth:

    def __init__(self, session: ClientSession, username, password, token_path=None):
        self.session = session
        self.username = username
        self.password = password
        self.token_path = token_path
        self.token = self.load_token()
        self.device_id = get_random(16)

    def load_token(self):
        if self.token_path and os.path.isfile(self.token_path):
            try:
                with open(self.token_path) as f:
                    return json.load(f)
            except Exception:
                _LOGGER.exception(f"Exception on load token from {self.token_path}")
        return None

    def save_token(self):
        if self.token_path:
            if self.token:
                try:
                    with open(self.token_path, 'w') as f:
                        json.dump(self.token, f)
                except Exception:
                    _LOGGER.exception(f"Exception on save token to {self.token_path}")
            elif os.path.isfile(self.token_path):
                os.remove(self.token_path)
    
    async def login(self):
        try:
            payload = await self._login1()
            data = await self._login2(payload)
            location = data['location']
            if not location:
                return False
            token = await self._login3(location)
            self.token = (data['userId'], data['ssecurity'], token)

        except Exception as e:
            _LOGGER.exception(f"Exception on login {self.username}: {e}")
            self.token = None

        self.save_token()
        return self.token

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
        token = r.cookies['serviceToken'].value
        _LOGGER.debug(f"MiCloud step3: %s", token)
        return token


class MiCloud:

    def __init__(self, auth, region=None):
        self.auth = auth
        self.server = 'https://' + ('' if region is None or region == 'cn' else region + '.') + 'api.io.mi.com/app'

    def sign(self, uri, params):
        data = params if type(params) == str else json.dumps(params)
        nonce = gen_nonce()
        signed_nonce = gen_signed_nonce(self.auth.token[1], nonce)
        signature = gen_signature(uri, signed_nonce, nonce, data)
        return {'signature': signature, '_nonce': nonce, 'data': data}

    async def _request(self, uri, params=''):
        try:
            r = await self.auth.session.post(self.server + uri, cookies={
                'userId': self.auth.token[0],
                'serviceToken': self.auth.token[2],
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
        if self.auth.token is None and not await self.auth.login():  # Ensure login
            return None

        resp = await self._request(uri, params)
        code = resp.get('code')
        if code == 0:
            return resp.get('result')

        _LOGGER.error(f"Error on request {uri}: {resp}")
        if code == 2 and await self.auth.login():  # Auth error, relogin
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
        return await self.miotspec('action', {'params': params})

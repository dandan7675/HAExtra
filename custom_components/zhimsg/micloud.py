# The base logic was taken from project https://github.com/squachen/micloud

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

    def __init__(self, session: ClientSession, username, password, token_dir=''):
        self.session = session
        self.username = username
        self.password = password
        self.token_path = os.path.join(token_dir, '.mi.' + username) if token_dir is not None else None
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
            # if payload['code'] != 0:
            #     return False
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

    async def _login3(self, location):
        r = await self.session.get(location, headers={'User-Agent': UA})
        token = r.cookies['serviceToken'].value
        _LOGGER.debug(f"MiCloud step3: %s", token)
        return token


class MiCloud:

    def __init__(self, auth, region=None):
        self.auth = auth
        self.server = 'https://' + ('' if region is None or region == 'cn' else region + '.') + 'api.io.mi.com/app'

    def sign(self, uri, data):
        if type(data) != str:
            data = json.dumps(data)
        nonce = gen_nonce()
        signed_nonce = gen_signed_nonce(self.auth.token[1], nonce)
        signature = gen_signature(uri, signed_nonce, nonce, data)
        return {'signature': signature, '_nonce': nonce, 'data': data}

    async def request(self, uri, data='', relogin=True):
        if self.auth.token is None and not await self.auth.login():  # Ensure login
            return None

        _LOGGER.debug(f"Request {uri} with {data}")
        try:
            r = await self.auth.session.post(self.server + uri, cookies={
                'userId': self.auth.token[0],
                'serviceToken': self.auth.token[2],
                # 'locale': 'en_US'
            }, headers={
                'User-Agent': UA,
                'x-xiaomi-protocal-flag-cli': 'PROTOCAL-HTTP2'
            }, data=self.sign(uri, data), timeout=10)
            resp = await r.json(content_type=None)
            code = resp['code']
            if code == 0:
                result = resp['result']
                if result is not None:
                    return result
            elif code == 2 and relogin:
                _LOGGER.debug(f"Auth error on request {uri}, relogin...")
                self.auth.token = None  # Auth error, reset login
                return self.request(uri, data, False)
        except Exception as e:
            resp = e
        error = f"Request {uri} error: {resp}"
        _LOGGER.exception(error)
        return Exception(error)

    async def miotspec(self, api, data='{}'):
        return await self.request('/miotspec/' + api, data)

    async def miot_prop_get(self, params='[]'):
        if type(params) != str:
            params = json.dumps(params)
        return await self.miotspec('prop/get', '{"datasource":1, "params":' + params + '}')

    async def miot_prop_set(self, params=''):
        # if type(params) != str:
        #     params = json.dumps(params)
        return await self.miotspec('prop/set', params)

    async def miot_action(self, siid, aiid, _in='[]', did=None):
        if type(_in) != str:
            _in = json.dumps(_in)
        elif _in[0] != '[':
            _in = f'["{_in}"]'
        return await self.miotspec('action', '{"params": {"did":"%s", "siid":%s, "aiid":%s, "in":%s}}' % (
            did or f'action-{siid}-{aiid}', siid, aiid, _in))

    async def device_list(self):
        result = await self.request('/home/device_list', '{"getVirtualModel": false, "getHuamiDevices": 0}')
        return result.get('list') if type(result) != Exception else None

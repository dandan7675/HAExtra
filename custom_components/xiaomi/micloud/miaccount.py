import base64
import hashlib
import hmac
import json
import logging
import os
import random
import string
import time

_LOGGER = logging.getLogger(__name__)

USER_AGENT = "Android-7.1.1-1.0.0-ONEPLUS A3010-136-%s APP/xiaomi.smarthome APPV/62830"


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

    def __init__(self, session, username, password, token_path='.micloud'):
        self.session = session
        self.username = username
        self.password = password
        self.token_path = token_path
        self.token = self.load_token()

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
            deviceId = get_random(16)
            payload = await self._login1(deviceId)
            # if payload['code'] != 0:
            #     return False
            data = await self._login2(deviceId, payload)
            location = data['location']
            if not location:
                return False
            serviceToken = await self._login3(deviceId, location)
            self.token = {'deviceId': deviceId, 'userId': data['userId'], 'ssecurity': data['ssecurity'], 'serviceToken': serviceToken}

        except Exception as e:
            _LOGGER.exception(f"Exception on login {self.username}: {e}")
            self.token = None

        self.save_token()
        return self.token

    async def _login1(self, deviceId):
        r = await self.session.get('https://account.xiaomi.com/pass/serviceLogin',
                                   cookies={'sdkVersion': '3.8.6', 'deviceId': deviceId},
                                   headers={'User-Agent': USER_AGENT % deviceId},
                                   params={'sid': 'xiaomiio', '_json': 'true'})
        raw = await r.read()
        resp = json.loads(raw[11:])
        #_LOGGER.debug(f"MiCloud step1: %s", resp)
        return {k: v for k, v in resp.items() if k in ('sid', 'qs', 'callback', '_sign')}

    async def _login2(self, deviceId, payload):
        payload['user'] = self.username
        payload['hash'] = hashlib.md5(self.password.encode()).hexdigest().upper()
        r = await self.session.post('https://account.xiaomi.com/pass/serviceLoginAuth2',
                                    cookies={'sdkVersion': '3.8.6', 'deviceId': deviceId},
                                    data=payload,
                                    headers={'User-Agent': USER_AGENT % deviceId},
                                    params={'_json': 'true'})
        raw = await r.read()
        resp = json.loads(raw[11:])
        #_LOGGER.debug(f"MiCloud step2: %s", resp)
        return resp

    async def _login3(self, deviceId, location):
        r = await self.session.get(location, headers={'User-Agent': USER_AGENT % deviceId})
        serviceToken = r.cookies['serviceToken'].value
        #_LOGGER.debug(f"MiCloud step3: %s", serviceToken)
        return serviceToken

    def sign(self, uri, data):
        if type(data) != str:
            data = json.dumps(data)
        nonce = gen_nonce()
        signed_nonce = gen_signed_nonce(self.token['ssecurity'], nonce)
        signature = gen_signature(uri, signed_nonce, nonce, data)
        return {'signature': signature, '_nonce': nonce, 'data': data}

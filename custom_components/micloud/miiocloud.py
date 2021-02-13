from miaccount import MiAccount, USER_AGENT

import json
import logging

_LOGGER = logging.getLogger(__name__)

#REGIONS = ['cn', 'de', 'i2', 'ru', 'sg', 'us']


class MiIOCloud:

    def __init__(self, account: MiAccount, region=None):
        self.account = account
        self.server = 'https://' + ('' if region is None or region == 'cn' else region + '.') + 'api.io.mi.com/app'

    async def request(self, uri, data='', relogin=True):
        if self.account.token is not None or await self.account.login():  # Ensure login
            _LOGGER.debug(f"Request {uri} with {data}")
            try:
                r = await self.account.session.post(self.server + uri, cookies={
                    'userId': self.account.token['userId'],
                    'serviceToken': self.account.token['serviceToken'],
                    # 'locale': 'en_US'
                }, headers={
                    'User-Agent': USER_AGENT % self.account.token['deviceId'],
                    'x-xiaomi-protocal-flag-cli': 'PROTOCAL-HTTP2'
                }, data=self.account.sign(uri, data), timeout=10)
                resp = await r.json(content_type=None)
                code = resp['code']
                if code == 0:
                    result = resp['result']
                    if result is not None:
                        return result
                elif code == 2 and relogin:
                    _LOGGER.debug(f"Auth error on request {uri}, relogin...")
                    self.token = None  # Auth error, reset login
                    return self.request(uri, data, False)
            except Exception as e:
                resp = e
        else:
            resp = "Login failed"
        error = f"Request {uri} error: {resp}"
        _LOGGER.error(error)
        return Exception(error)

    async def miotspec(self, api, data='{}'):
        return await self.request('/miotspec/' + api, data)

    async def miot_prop_get(self, did, props=[]):
        data = '{"datasource":1, "params": ['
        for prop in props:
            data += '{"did":"%s", "siid":%s, "piid":%s}' % (did, prop[0], prop[1])
        data += ']}'
        return await self.miotspec('prop/get',  data)

    async def miot_prop(self, did, props=[]):
        api = 'prop/get'
        params = ''
        for prop in props:
            if params:
                params += ', '
            params += '{"did":"%s", "siid":%s, "piid":%s' % (did, prop[0], prop[1])
            if (len(prop) > 2):
                api = 'prop/set'
                value = prop[2]
                value_type = type(value)
                if value_type == bool or value is None:
                    value = str(value).lower()
                elif value_type == str and (len(prop) == 3 or prop[3]):
                    value = ('"' + value + '"')
                params += ', "value":%s' % value
            params += '}'
        return await self.miotspec(api, '{"params": [' + params + ']}')

    async def miot_prop_get(self, did, siid, piid=1):
        return await self.miot_prop(did, {(siid, piid)})  # TODO: Parse

    async def miot_prop_set(self, did, siid, piid, value, quote=True):
        return await self.miot_prop(did, {(siid, piid, value, quote)})  # TODO: Parse

    async def miot_action(self, did, siid, aiid, _in='[]'):
        if type(_in) != str:
            _in = json.dumps(_in)
        elif _in[0] != '[':
            _in = f'["{_in}"]'
        return await self.miotspec('action', '{"params": {"did":"%s", "siid":%s, "aiid":%s, "in":%s}}' % (
            did or f'action-{siid}-{aiid}', siid, aiid, _in))

    async def device_list(self):
        result = await self.request('/home/device_list', '{"getVirtualModel": false, "getHuamiDevices": 0}')
        return result.get('list') if type(result) != Exception else None

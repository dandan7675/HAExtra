import logging

_LOGGER = logging.getLogger(__name__)

# REGIONS = ['cn', 'de', 'i2', 'ru', 'sg', 'us']


class MiIOCloud:

    def __init__(self, auth, region=None):
        self.auth = auth
        self.server = 'https://' + ('' if region is None or region == 'cn' else region + '.') + 'api.io.mi.com/app'

    async def miio(self, uri, data, relogin=True):
        if self.auth.token is not None or await self.auth.login():  # Ensure login
            _LOGGER.debug(f"{uri} {data}")
            r = await self.auth.session.post(self.server + uri, cookies={
                'userId': self.auth.token['userId'],
                'serviceToken': self.auth.token['serviceToken'],
                # 'locale': 'en_US'
            }, headers={
                'User-Agent': self.auth.user_agent,
                'x-xiaomi-protocal-flag-cli': 'PROTOCAL-HTTP2'
            }, data=self.auth.sign(uri, data), timeout=10)
            resp = await r.json(content_type=None)
            code = resp['code']
            if code == 0:
                result = resp['result']
                if result is not None:
                    # _LOGGER.debug(f"{result}")
                    return result
            elif code == 2 and relogin:
                _LOGGER.debug(f"Auth error on request {uri}, relogin...")
                self.token = None  # Auth error, reset login
                return self.miio(uri, data, False)
        else:
            resp = "Login failed"
        error = f"Request {uri} error: {resp}"
        _LOGGER.error(error)
        raise Exception(error)

    async def miot_spec(self, cmd, params):
        return await self.miio('/miotspec/' + cmd, {'params': params})

    async def miot_get_props(self, did, props):
        params = [{'did': did, 'siid': prop[0], 'piid': prop[1]} for prop in props]
        result = await self.miot_spec('prop/get', params)
        return [it.get('value') if it.get('code') == 0 else None for it in result]

    async def miot_set_props(self, did, props):
        params = [{'did': did, 'siid': prop[0], 'piid': prop[1], 'value': prop[2]} for prop in props]
        result = await self.miot_spec('prop/set', params)
        return [it.get('code', -1) for it in result]

    async def miot_get_prop(self, did, siid, piid):
        return (await self.miot_get_props(did, [(siid, piid)]))[0]

    async def miot_set_prop(self, did, siid, piid, value):
        return (await self.miot_set_props(did, [(siid, piid, value)]))[0]

    async def miot_action(self, did, siid, aiid, args):
        if not did:
            did = f'action-{siid}-{aiid}'
        result = await self.miot_spec('action', {'did': did, 'siid': siid, 'aiid': aiid, 'in': args})
        return result

    async def device_list(self):
        result = await self.miio('/home/device_list', {'getVirtualModel': False, 'getHuamiDevices': 0})
        return result.get('list')

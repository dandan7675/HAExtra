#!/usr/bin/env python3
import sys
import json
import asyncio
from genie import handleRequest, makeResponse, errorResult, _LOGGER


class RemoteHass:

    def __init__(self, url, token):
        self.url = url + '/api/'
        self.token = token
        self.states = self
        self.services = self

    def rest(self, cmd, data=None):
        import requests
        url = self.url + cmd
        method = 'POST' if data else 'GET'
        _LOGGER.debug('REST %s %s %s', method, url, data or '')
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Content-Type': 'application/json'} if self.token else None
        result = requests.request(method, url, data=data, headers=headers, timeout=3, verify=False).text
        #_LOGGER.info('REST RESPONSE: %s', result)
        return json.loads(result)

    def async_all(self):
        from collections import namedtuple
        states = []
        for d in self.rest('states'):
            states.append(namedtuple('EntityState', d.keys())(*d.values()))
        return states

    def get(self, entity_id):
        from collections import namedtuple
        d = self.rest('states/' + entity_id)
        return namedtuple('EntityState', d.keys())(*d.values())

    async def async_call(self, domain, service, data, blocking=False):
        return self.rest('services/' + domain + '/' + service, data)


async def main():
    if len(sys.argv) < 3:
        print(f'Usage: {sys.argv[0]} <https://192.168.1.x:8123> <token>')
        exit(0)

    headers = [
        {'namespace': 'AliGenie.Iot.Device.Discovery', 'name': 'DiscoveryDevices', 'messageId': 'd0c17289-55df-4c8c-955f-b735e9bdd305'},
        {'namespace': 'AliGenie.Iot.Device.Control', 'name': 'TurnOn', 'messageId': 'd0c17289-55df-4c8c-955f-b735e9bdd305'},
        {'namespace': 'AliGenie.Iot.Device.Query', 'name': 'Query', 'messageId': 'd0c17289-55df-4c8c-955f-b735e9bdd305'},
    ]
    data = {
        'header': headers[sys.argv[3] if len(sys.argv) > 3 else 1],
        'payload': {'deviceId': sys.argv[4] if len(sys.argv) > 4 else 'light.er_tong_fang_tai_deng', 'deviceType': 'light'}
    }

    try:
        result = await handleRequest(RemoteHass(sys.argv[1], sys.argv[2]), data)
    except:
        import traceback
        print(traceback.format_exc())
        result = errorResult('SERVICE_ERROR')
    print(json.dumps(makeResponse(data, result), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()

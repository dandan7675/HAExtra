#!/usr/bin/env python3
# encoding: utf-8

from aiohttp import ClientSession
from micloud import (MiAuth, MiCloud, _LOGGER)

import asyncio
import logging
import json


async def main(argv):
    async with ClientSession() as session:
        auth = MiAuth(session, sys.argv[1], sys.argv[2])
        cloud = MiCloud(auth)
        argc = len(argv)
        if argc < 4 or argv[3] == 'list':
            result = await cloud.device_list()
        else:
            api = argv[3]
            params = argv[4] if argc > 4 else ''
            if api == 'get':
                if argc > 5:
                    params = []
                    for i in range(5, argc):
                        parts = argv[i].split('/')
                        siid = int(parts[0])
                        piid = int(parts[1]) if len(parts) > 1 else 1
                        params.append({'did': argv[4], 'siid': siid, 'piid': piid})
                result = await cloud.miot_prop_get(params)
            elif api == 'set':
                result = await cloud.miot_prop_set(params)
            elif api == 'do':
                result = await cloud.miot_action(params)
            else:
                result = await cloud.miotspec(api, params)
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    import sys
    argc = len(sys.argv)
    if argc <= 2:
        print("Usage: %s <username> <password> [list|get|set|do|<api>] [params]\n" % sys.argv[0])
        print(sys.argv[0] + ' 139xxxxxxxx ******** get 267090026 1/1 1/2 1/3')
        print(sys.argv[0] + ' 139xxxxxxxx ******** do \'{"did":"267090026","siid":5,"aiid":1,"in":["hello"]}\'')
        print(sys.argv[0] + ' 139xxxxxxxx ******** action \'{"params":{"did":"267090026","siid":5,"aiid":1,"in":["hello"]}}\'')
        exit(0)
    _LOGGER.setLevel(logging.DEBUG)
    _LOGGER.addHandler(logging.StreamHandler())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
    loop.close()

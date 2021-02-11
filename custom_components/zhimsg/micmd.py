#!/usr/bin/env python3

from aiohttp import ClientSession
from micloud import (MiAccount, MiCloud)

import asyncio
import logging
import json

_LOGGER = logging.getLogger(__name__)


async def main(argv):
    async with ClientSession() as session:
        cloud = MiCloud(MiAccount(session, sys.argv[1], sys.argv[2]))
        if len(argv) <= 4:
            print(json.dumps(await cloud.device_list(), indent=2, ensure_ascii=False))
        else:
            await cloud.miotspec(argv[3], argv[4])


if __name__ == '__main__':
    import sys
    argc = len(sys.argv)
    if argc <= 2:
        print("Usage: %s <username> <password> [api] [params]" % sys.argv[0])
        print('\n%s 139xxxxxxxx ******** action \'{"params":{"did":"267090026","siid":5,"aiid":1,"in":["hello"]}}\'' % sys.argv[0])
        exit(0)
    _LOGGER.setLevel(logging.DEBUG)
    _LOGGER.addHandler(logging.StreamHandler())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
    loop.close()

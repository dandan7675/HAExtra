#!/usr/bin/env python3
from aiohttp import ClientSession
import asyncio
import logging
import json
import os
import sys

from miauth import MiAuth, _LOGGER as _LOGGER1
from miio import MiIO, _LOGGER as _LOGGER2
from miiocmd import miio_cmd, miio_cmd_help


def usage(did):
    print("Usage: The following variables must be set:")
    print("           export MI_USER=<username>")
    print("           export MI_PASS=<password>")
    print("           export MIIO_DID=<deviceId>\n")
    print(miio_cmd_help(did, sys.argv[0] + ' '))


async def main(username, password, did, text):
    async with ClientSession() as session:
        auth = MiAuth(session, username, password)
        cloud = MiIO(auth)
        result = await miio_cmd(cloud, did, text)
        if not isinstance(result, str):
            result = json.dumps(result, indent=2, ensure_ascii=False)
        elif result == 'HELP':
            return usage(did)
        print(result)


if __name__ == '__main__':
    argv = sys.argv
    argc = len(argv)
    username = os.environ.get('MI_USER')
    password = os.environ.get('MI_PASS')
    did = os.environ.get('MIIO_DID')
    if argc > 1 and username and password:
        _LOGGER1.setLevel(logging.DEBUG)
        _LOGGER1.addHandler(logging.StreamHandler())
        _LOGGER2.setLevel(logging.DEBUG)
        _LOGGER2.addHandler(logging.StreamHandler())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(username, password, did, ' '.join(argv[1:])))
        loop.close()
    else:
        usage(did)

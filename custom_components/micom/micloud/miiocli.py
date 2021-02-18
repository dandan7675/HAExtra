#!/usr/bin/env python3
from aiohttp import ClientSession
import asyncio
import logging
import json
import os
import sys

from miauth import MiAuth, _LOGGER as _LOGGER1
from miiocloud import MiIOCloud, _LOGGER as _LOGGER2
from miiocmd import miio_cmd, miio_cmd_help


def usage():
    print(f"Usage:     {sys.argv[0]} [username] [password] <cmd>\n")
    print(f"Username:  export MI_USER=<username>")
    print(f"Password:  export MI_PASS=<password>\n")
    print(miio_cmd_help().replace(": ", f": {sys.argv[0]} '").replace("\n", "'\n"))


async def main(username, password, cmd):
    async with ClientSession() as session:
        auth = MiAuth(session, username, password)
        cloud = MiIOCloud(auth)
        result = await miio_cmd(cloud, cmd)
        if not isinstance(result, str):
            result = json.dumps(result, indent=2, ensure_ascii=False)
        print(result)


if __name__ == '__main__':
    argv = sys.argv
    argc = len(argv)
    username = argv[argc - 3] if argc > 3 else os.environ.get('MI_USER')
    password = argv[argc - 2] if argc > 2 else os.environ.get('MI_PASS')
    if argc > 1 and username and password:
        _LOGGER1.setLevel(logging.DEBUG)
        _LOGGER1.addHandler(logging.StreamHandler())
        _LOGGER2.setLevel(logging.DEBUG)
        _LOGGER2.addHandler(logging.StreamHandler())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(username, password, argv[argc - 1]))
        loop.close()
    else:
        usage()

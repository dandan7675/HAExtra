#!/usr/bin/env python3
# encoding: utf-8

from aiohttp import ClientSession
from micloud import (MiAuth, MiCloud, _LOGGER)

import asyncio
import logging
import json
import os
import sys


def usage(arg0):
    print("Usage:")
    print("  List Devs: micmd.py [username] [password]")
    print("  Get Infos: micmd.py [username] [password] <did>")
    print("  Get Props: micmd.py [username] [password] <did> <siid>[/piid] [...]")
    print("  Set Props: micmd.py [username] [password] <did> <siid>[/piid]=<value> [...]")
    print("  Do Action: micmd.py [username] [password] <did> <siid>[/aiid] <in|'[in1,...]'>")
    print("  Call MIoT: micmd.py [username] [password] <'{params}'> [api]")
    print("\nExample:")
    print("  Username:  export MI_USER=<username>")
    print("  Password:  export MI_PASS=<password>")
    print(f"  List Devs: {arg0}")
    print(f"  Get Infos: {arg0} 267090026")
    print(f"  Get Props: {arg0} 267090026 1 1/2 2")
    print(f"  Set Props: {arg0} 267090026 2=60 2/2=false")
    print(f"  Do Action: {arg0} 267090026 5 您好")
    print(f"  Do Action: {arg0} 267090026 5/4 '[\"天气\",1]'")
    print(f'  Call MIoT: {arg0} \'{{"params":{{"did":"267090026","siid":5,"aiid":1,"in":["您好"]}}}}\' action')


async def main(username, password, argv):
    async with ClientSession() as session:
        auth = MiAuth(session, username, password)
        cloud = MiCloud(auth)
        if len(argv) > 1:
            result = await miot(cloud, argv)
        else:
            result = await cloud.device_list()
        if type(result) != Exception:
            print(json.dumps(result, indent=2, ensure_ascii=False))


async def miot(cloud, argv):
    argc = len(argv)
    arg1 = argv[1]

    if arg1[0] == '{':
        return await cloud.miotspec(argv[2] if argc > 2 else 'action', arg1)

    if argc == 2:
        return arg1  # TODO: info

    if argc > 3:
        _in = argv[3]
        if _in[0] < '0' or _in[0] > '9':
            siid, aiid = twins_split(argv[2], '/', 1)
            return await cloud.miot_action(siid, aiid, _in, arg1)

    return await miot_prop(cloud, arg1, argv)


async def miot_prop(cloud, did, argv):
    gets = []
    sets = []
    for i in range(2, len(argv)):
        arg = argv[i]
        key, value = twins_split(arg, '=')
        siid, piid = twins_split(key, '/', 1)
        if value is None:
            gets.append({'did': did, 'siid': int(siid), 'piid': int(piid)})
        else:
            sets.append({'did': did, 'siid': int(siid), 'piid': int(piid), 'value': value})
    if len(sets):
        result = await cloud.miot_prop_set(sets)
    if len(gets):
        result = await cloud.miot_prop_get(gets)
    return result


def twins_split(string, sep='/', default=None):
    pos = string.find(sep)
    return (string, default) if pos == -1 else (string[0:pos], string[pos + 1:])


if __name__ == '__main__':
    argv = sys.argv
    username = os.environ.get('MI_USER')
    password = os.environ.get('MI_PASS')
    argc = len(argv)
    if username and password:
        help = argc > 1 and argv[1] == '-h'
    else:
        help = argc < 3 or argv[1] == '-h'
    if help:
        usage(argv[0])
        exit(0)
    if not username or not password:
        username = argv[1]
        password = argv[2]
        argv = argv[2:]

    _LOGGER.setLevel(logging.DEBUG)
    _LOGGER.addHandler(logging.StreamHandler())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(username, password, argv))
    loop.close()

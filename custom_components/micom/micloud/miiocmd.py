
import json


def twins_split(string, sep, default=None):
    pos = string.find(sep)
    return (string, default) if pos == -1 else (string[0:pos], string[pos+1:])


def pause_split(string, sep, default=None):
    pos = string.rfind(sep)
    return (string, default) if pos == -1 else (string[0:pos+1], string[pos+1:].strip())


def string_to_value(string):
    if string == 'null' or string == 'none':
        return None
    elif string == 'false':
        return False
    elif string == 'true':
        return True
    else:
        return int(string)


def string_or_value(string):
    return string_to_value(string[1:]) if string[0] == '=' else string


def miio_cmd_help(did, prefix='?'):
    quote = '' if prefix == '?' else "'"
    return f'\
Get Props: {prefix}<siid[-piid]>[,...]\n\
           {prefix}1,1-2,1-3,1-4,2-1,2-2,3\n\
Set Props: {prefix}<siid[-piid]=[=]value>[,...]\n\
           {prefix}2==60,2-2==false,3=test\n\
Do Action: {prefix}<siid[-piid]> <arg1> [...] \n\
           {prefix}5 您好\n\
           {prefix}5-4 天气 =1\n\n\
Call MIoT: {prefix}<cmd=prop/get|/prop/set|action> <params>\n\
           {prefix}action {quote}{{"did":"{did or "267090026"}","siid":5,"aiid":1,"in":["您好"]}}{quote}\n\n\
Call MiIO: {prefix}/<uri> <data>\n\
           {prefix}/home/device_list {quote}{{"getVirtualModel":false,"getHuamiDevices":1}}{quote}\n\n\
Devs List: {prefix}list [getVirtualModel=false|true] [getHuamiDevices=0|1]\n\
           {prefix}list true 1'


async def miio_cmd(cloud, did, text, prefix='?'):

    cmd, arg = twins_split(text, ' ')
    if not cmd or cmd == 'help' or cmd == '-h' or cmd == '--help':
        return miio_cmd_help(did, prefix)

    if cmd.startswith('/'):
        return await cloud.miio(cmd, arg)

    if cmd.startswith('prop') or cmd == 'action':
        return await cloud.miot_spec(cmd, json.loads(arg) if arg else None)

    argv = arg.split(' ') if arg else []
    argc = len(argv)
    if cmd == 'list':
        return await cloud.device_list(bool(argc > 0 and string_to_value(argv[0])), int(argv[1]) if argc > 1 else 0)

    if not did:
        return "Empty Device ID"

    if argc > 0:
        siid, aiid = twins_split(cmd, '-', 1)
        args = [string_or_value(a) for a in argv]
        return await cloud.miot_action(did, int(siid), int(aiid), args)

    props = []
    isget = False
    for item in cmd.split(','):
        iid, value = twins_split(item, '=')
        siid, piid = twins_split(iid, '-', 1)
        prop = [int(siid), int(piid)]
        if not isget:
            if value is None:
                isget = True
            else:
                prop.append(string_or_value(value))
        props.append(prop)

    return await (cloud.miot_get_props if isget else cloud.miot_set_props)(did, props)

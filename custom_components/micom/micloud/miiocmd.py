
import json


def twins_split(twins, sep, default=None):
    pos = twins.find(sep)
    return (twins, default) if pos == -1 else (twins[0:pos], twins[pos + 1:])


def string_value(value):
    if value[0] == '=':
        value = value[1:]
        if value == 'none':
            return None
        elif value == 'false':
            return False
        elif value == 'true':
            return True
        else:
            return int(value)
    return value


def miio_cmd_help(did=None, prop_prefix=''):
    if did:
        end = '\n'
    else:
        did = '267090026'
        end = '@' + did + '\n'
    return \
        'Get Props: ' + prop_prefix + '1,1-2,1-3,1-4,2,3' + end + \
        'Set Props: ' + prop_prefix + '2==60,2-2==false,3=test' + end + \
        'Do Action: ["您好"]5' + end + \
        'Do Action: ["天气",1]5-4' + end + \
        'Call MIoT: {"did":"' + did + '","siid":5,"aiid":1,"in":["您好"]}action\n' + \
        'Call MiIO: {"getVirtualModel":false,"getHuamiDevices":1}/home/device_list\n'


async def miio_cmd(cloud, cmd, did=None, prop_prefix=''):
    if cmd == '?' or cmd == '-h' or cmd == '--help':
        return miio_cmd_help(did, prop_prefix)

    elif cmd.startswith('{'):
        pos = cmd.rfind('}')
        if pos != -1:
            data = cmd[0:pos+1]
            uri = cmd[pos+1:].strip()
            if uri.startswith('/'):
                return await cloud.miio(uri, data)
            return await cloud.miot_spec(uri, json.loads(data))

    elif cmd.startswith('['):
        pos = cmd.rfind(']')
        if pos != -1:
            iid, did = twins_split(cmd[pos+1:], '@', did)
            if did:
                siid, aiid = twins_split(iid, '-', 1)
                try:
                    siid = int(siid)
                    aiid = int(aiid)
                except:
                    return 'IID not a number'
                return await cloud.miot_action(did, siid, aiid, json.loads(cmd[0:pos+1]))

    else:
        if prop_prefix:
            if cmd.startswith(prop_prefix):
                cmd = cmd[len(prop_prefix):]
            else:
                return 'Invalid command'
        items, did = twins_split(cmd, '@', did)
        if did and items:
            props = []
            isget = False
            for item in items.split(','):
                iid, value = twins_split(item, '=')
                siid, piid = twins_split(iid, '-', 1)
                try:
                    prop = [int(siid), int(piid)]
                    if not isget:
                        if value is None:
                            isget = True
                        else:
                            prop.append(string_value(value))
                except:
                    return 'IID or value not a number'
                props.append(prop)
            result = await (cloud.miot_get_props if isget else cloud.miot_set_props)(did, props)
            return result

    return 'Corrupt parameter'

#!/usr/bin/env python3
import os
import sys
import json
import asyncio
from genie import handleRequest, errorResult


async def main():
    try:
        data = {
            'header': {'namespace': 'AliGenie.Iot.Device.Discovery', 'name': 'DiscoveryDevices', 'messageId': 'd0c17289-55df-4c8c-955f-b735e9bdd305'},
            # 'header': {'namespace': 'AliGenie.Iot.Device.Control', 'name': 'TurnOn', 'messageId': 'd0c17289-55df-4c8c-955f-b735e9bdd305'},
            # 'header': {'namespace': 'AliGenie.Iot.Device.Query', 'name': 'Query', 'messageId': 'd0c17289-55df-4c8c-955f-b735e9bdd305'},
            'payload': {'accessToken': sys.argv[1] if len(sys.argv) > 1 else 'https_192.168.1.12_8123_token', 'deviceId': 'weather.caiyun', 'deviceType': 'sensor'}
        }
        response = await handleRequest(data)
    except:
        import traceback
        print(traceback.format_exc())
        response = {'header': {'name': 'errorResult'},
                    'payload': errorResult('SERVICE_ERROR', 'json error')}

    print('Content-Type: application/json\r\n')
    print(json.dumps(response, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()

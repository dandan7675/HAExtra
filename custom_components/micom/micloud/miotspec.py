#!/usr/bin/env python3
import sys
import json
import requests

url_all = 'http://miot-spec.org/miot-spec-v2/instances?status=all'
url_spec = 'http://miot-spec.org/miot-spec-v2/instance'

if __name__ == '__main__':
    if len(sys.argv) > 1:
        model = sys.argv[1]
    else:
        model = input("请输入设备型号：")

    print("正在加载设备列表…")
    dev_list = requests.get(url_all).json().get('instances')

    result = []
    for item in dev_list:
        if model in item['model'] or model in item['type']:
            result.append(item)

    if not result:
        print("未找到相关设备")
        exit(-1)

    if len(result) > 1:
        for idx, item in enumerate(result):
            print(f"{idx+1}\t{item['model']}\t{item['type']}")
        inp = input(f"找到 {len(result)} 个设备，请输入序号[1]：")
    else:
        inp = 0

    item = result[int(inp) - 1 if inp else 0]
    urn = item['type']
    print(f"正在加载 {item['model']} 设备规范…")
    result = requests.get(url_spec, params={'type': urn}).json()
    print(json.dumps(result, indent=2, ensure_ascii=None))

# -*- coding: utf-8 -*-
# create-gateway.py
#
# This script automates the creation of a gateway device in ThingsBoard, including setting up device profiles,
# attributes, and retrieving the access token. It is designed to streamline the process of managing IoT devices
# on the ThingsBoard platform.
#
# Author: LockOn
# Date: April 30, 2025
# Version: 1.0
# License: MIT
# Repository: https://github.com/DarkHexBoy

import requests
import json  # 用于处理 JSON 数据
import configparser
import time  # 用于循环和时间处理

# 读取配置文件
config = configparser.ConfigParser()
config.read('config.ini')

# 从配置文件中获取参数
TB_HOST = config['ThingsBoard']['TB_HOST']
USERNAME = config['ThingsBoard']['USERNAME']
PASSWORD = config['ThingsBoard']['PASSWORD']

device_name = config['Device']['device_name']
device_profile_name = config['Device']['device_profile_name']

attributes = {
    "Model": config['Attributes']['Model'],
    "Partnumber": config['Attributes']['Partnumber'],
    "Region": config['Attributes']['Region'],
    "Serial Number": config['Attributes']['Serial Number'],
    "Firmware Version": config['Attributes']['Firmware Version'],
    "Hardware Version": config['Attributes']['Hardware Version']
}

# === 第一步：登录，获取 JWT token ===
login_url = f'{TB_HOST}/api/auth/login'
login_payload = {'username': USERNAME, 'password': PASSWORD}
login_resp = requests.post(login_url, json=login_payload)
login_resp.raise_for_status()
jwt_token = login_resp.json()['token']
headers = {
    'Content-Type': 'application/json',
    'X-Authorization': f'Bearer {jwt_token}'
}
print(f"[INFO] 登录成功，JWT token 获取完毕")

# === 第二步：检查并跳过已存在的 Device Profile ===
create_device_profile_url = f'{TB_HOST}/api/deviceProfile'

# 检查是否存在同名 Device Profile
get_device_profiles_url = f'{TB_HOST}/api/deviceProfiles?pageSize=100&page=0'
profiles_resp = requests.get(get_device_profiles_url, headers=headers)
profiles_resp.raise_for_status()
profiles = profiles_resp.json().get('data', [])
existing_profile = next((p for p in profiles if p['name'] == device_profile_name), None)

if existing_profile:
    print(f"[INFO] Device Profile 已存在，跳过创建: {device_profile_name}")
    device_profile_id = existing_profile['id']['id']
else:
    device_profile_payload = {
        "name": device_profile_name,
        "description": "Device Profile for Gateway",
        "type": "DEFAULT",
        "transportType": "DEFAULT",
        "provisionType": "DISABLED",
        "default": False,
        "profileData": {
            "configuration": {
                "type": "DEFAULT"
            },
            "transportConfiguration": {
                "type": "DEFAULT"
            },
            "provisionConfiguration": {
                "type": "DISABLED"
            },
            "alarms": [
                {
                    "id": "gatewayOnlineAlarmID",
                    "alarmType": "Gateway Online Alarm",
                    "createRules": {
                        "MINOR": {
                            "condition": {
                                "condition": [
                                    {
                                        "key": {
                                            "type": "ATTRIBUTE",
                                            "key": "active"
                                        },
                                        "valueType": "BOOLEAN",
                                        "predicate": {
                                            "type": "BOOLEAN",
                                            "operation": "EQUAL",
                                            "value": {
                                                "defaultValue": True
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    },
                    "clearRule": {
                        "condition": {
                            "condition": [
                                {
                                    "key": {
                                        "type": "ATTRIBUTE",
                                        "key": "active"
                                    },
                                    "valueType": "BOOLEAN",
                                    "predicate": {
                                        "type": "BOOLEAN",
                                        "operation": "EQUAL",
                                        "value": {
                                            "defaultValue": False
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "detail": None
                },
                {
                    "id": "gatewayOfflineAlarmID",
                    "alarmType": "Gateway Offline Alarm",
                    "createRules": {
                        "CRITICAL": {
                            "condition": {
                                "condition": [
                                    {
                                        "key": {
                                            "type": "ATTRIBUTE",
                                            "key": "active"
                                        },
                                        "valueType": "BOOLEAN",
                                        "predicate": {
                                            "type": "BOOLEAN",
                                            "operation": "EQUAL",
                                            "value": {
                                                "defaultValue": False
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    },
                    "clearRule": {
                        "condition": {
                            "condition": [
                                {
                                    "key": {
                                        "type": "ATTRIBUTE",
                                        "key": "active"
                                    },
                                    "valueType": "BOOLEAN",
                                    "predicate": {
                                        "type": "BOOLEAN",
                                        "operation": "EQUAL",
                                        "value": {
                                            "defaultValue": True
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "detail": None
                }
            ]  # 移除 no data alarm
        }
    }
    create_profile_resp = requests.post(create_device_profile_url, json=device_profile_payload, headers=headers)
    try:
        create_profile_resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"服务器返回错误: {create_profile_resp.status_code}, 响应内容: {create_profile_resp.text}")
        raise e
    device_profile_id = create_profile_resp.json()['id']['id']
    print(f"[INFO] Device Profile 创建成功，名字: {device_profile_name}")

# === 第三步：检查设备是否存在 ===
get_devices_url = f'{TB_HOST}/api/tenant/devices?pageSize=100&page=0'
get_devices_resp = requests.get(get_devices_url, headers=headers)
get_devices_resp.raise_for_status()
existing_devices = get_devices_resp.json().get('data', [])
existing_device = next((d for d in existing_devices if d['name'] == device_name), None)

# 如果设备已存在，从配置文件中读取 Access Token
if existing_device:
    device_id = existing_device['id']['id']
    print(f"[INFO] {device_name} 设备已存在，跳过创建")

    # 从配置文件中读取 Access Token
    access_token = config['Device'].get('access_token')

    # 测试 Access Token 是否有效
    if access_token:
        test_url = f"{TB_HOST}/api/v1/{access_token}/attributes"
        try:
            test_resp = requests.get(test_url, headers={'Content-Type': 'application/json'})
            if test_resp.status_code == 200:
                print(f"[INFO] 配置文件中的 Access Token 有效，继续使用")
            else:
                print(f"[WARNING] Access Token 测试返回非 200 状态码: {test_resp.status_code}, 响应内容: {test_resp.text}")
                raise Exception("Access Token 无效")
        except Exception as e:
            print(f"[WARNING] 当前 Access Token 无效，尝试从 ThingsBoard 重新获取: {e}")
            access_token = None

    if not access_token:
        # 从 ThingsBoard 重新获取 Access Token
        get_credentials_url = f"{TB_HOST}/api/device/{device_id}/credentials"
        credentials_resp = requests.get(get_credentials_url, headers=headers)
        credentials_resp.raise_for_status()
        access_token = credentials_resp.json()['credentialsId']
        print(f"[INFO] 重新获取的 Access Token: {access_token}")

        # 更新配置文件
        config.set('Device', 'access_token', access_token)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        print(f"[INFO] Access Token 已更新并保存到配置文件")
else:
    # 如果设备不存在，创建设备
    device_payload = {
        "name": device_name,
        "type": "DEFAULT",
        "deviceProfileId": {"id": device_profile_id, "entityType": "DEVICE_PROFILE"},
        "additionalInfo": {
            "gateway": True
        }
    }
    create_device_url = f'{TB_HOST}/api/device'
    create_device_resp = requests.post(create_device_url, json=device_payload, headers=headers)
    create_device_resp.raise_for_status()
    device_id = create_device_resp.json()['id']['id']
    print(f"[INFO] 设备创建成功，设备 ID: {device_id}")

    # 获取 Access Token
    get_credentials_url = f"{TB_HOST}/api/device/{device_id}/credentials"
    credentials_resp = requests.get(get_credentials_url, headers=headers)
    credentials_resp.raise_for_status()
    access_token = credentials_resp.json()['credentialsId']
    print(f"[INFO] 设备的 Access Token 获取成功: {access_token}")

    # 将 Access Token 写入配置文件
    config.set('Device', 'access_token', access_token)
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    print(f"[INFO] Access Token 已写入配置文件: {access_token}")

# === 第四步：设置服务器端属性 ===
server_attributes_url = f"{TB_HOST}/api/plugins/telemetry/DEVICE/{device_id}/attributes/SERVER_SCOPE"
server_attributes_payload = attributes  # 从配置文件中读取的 attributes 替代硬编码
server_attributes_resp = requests.post(server_attributes_url, json=server_attributes_payload, headers=headers)
try:
    server_attributes_resp.raise_for_status()
except requests.exceptions.HTTPError as e:
    print(f"设置服务器端属性时出错: {server_attributes_resp.status_code}, 响应内容: {server_attributes_resp.text}")
    raise e
print(f"[INFO] 服务器端属性设置成功: {server_attributes_payload}")

# === 第五步：获取设备的 Access Token ===
get_credentials_url = f"{TB_HOST}/api/device/{device_id}/credentials"
credentials_resp = requests.get(get_credentials_url, headers=headers)
credentials_resp.raise_for_status()
access_token = credentials_resp.json()['credentialsId']
print(f"[INFO] 设备的 Access Token 获取成功: {access_token}")

# 将 Access Token 写入配置文件
config.set('Device', 'access_token', access_token)
with open('config.ini', 'w') as configfile:
    config.write(configfile)
print(f"[INFO] Access Token 已写入配置文件: {access_token}")

# === 第六步：循环发送设备状态数据 ===
telemetry_url = f"{TB_HOST}/api/v1/{access_token}/telemetry"

while True:
    # 构造数据
    telemetry_data = {
        "Local Time": time.strftime("%Y-%m-%d %H:%M:%S %A"),
        "Uptime": "13days,03:26:19",
        "CPU Load": "7%",
        "RAM": {
            "Capacity": "512MB",
            "Available": "121MB",
            "Usage": "23.63%"
        },
        "eMMC": {
            "Capacity": "8.0GB",
            "Available": "6.5GB",
            "Usage": "80.88%"
        },
        "storageCapacity": 8.0,  # 存储总容量，单位：GB
        "storageUsed": 1.5,      # 已用存储空间，单位：GB
        "storageAvailable": 6.5, # 可用存储空间，单位：GB
        "storage.messageCount": 1,  # 模拟存储消息计数
        "storage.dataPoints": 10   # 模拟推送的数据点
    }

    # 发送数据
    try:
        telemetry_resp = requests.post(telemetry_url, json=telemetry_data, headers={'Content-Type': 'application/json'})
        telemetry_resp.raise_for_status()
        print(f"[INFO] 遥测数据发送成功: {telemetry_data}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 遥测数据发送失败: {e}")

    # 等待 10 秒后发送下一次数据
    time.sleep(10)

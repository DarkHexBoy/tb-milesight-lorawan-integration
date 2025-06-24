# -*- coding: utf-8 -*-
#  @Time    : 2025/04/29 15:17
#  @Author  : LockOn
#  @FileName: create-sensor.py
#  @Software: PyCharm
#  @Github  : https://github.com/DarkHexBoy
#  @Version : 1.0


import requests
import json
import configparser
import time

# 读取配置文件
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

# 从配置文件中加载配置项
THINGSBOARD_HOST = config.get('ThingsBoard', 'tb_host')
USERNAME = config.get('ThingsBoard', 'username')
PASSWORD = config.get('ThingsBoard', 'password')
DEVICE_NAME = "am308-lora"
DEVICE_PROFILE_NAME = "AM08-Profile"

# 登录获取 JWT Token
def get_jwt_token():
    url = f"{THINGSBOARD_HOST}/api/auth/login"
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()['token']

# 创建设备配置文件
def create_device_profile(jwt_token):
    url = f"{THINGSBOARD_HOST}/api/deviceProfile"
    headers = {
        "Content-Type": "application/json",
        "X-Authorization": f"Bearer {jwt_token}"
    }
    payload = {
        "name": DEVICE_PROFILE_NAME,
        "type": "DEFAULT",
        "transportType": "DEFAULT",
        "profileData": {
            "transportConfiguration": {
                "type": "DEFAULT"
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
            ]
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"设备配置文件 {DEVICE_PROFILE_NAME} 创建成功")
    else:
        print(f"设备配置文件创建失败: {response.text}")

# 创建设备
def create_device(jwt_token):
    url = f"{THINGSBOARD_HOST}/api/device"
    headers = {
        "Content-Type": "application/json",
        "X-Authorization": f"Bearer {jwt_token}"
    }
    payload = {
        "name": DEVICE_NAME,
        "type": DEVICE_PROFILE_NAME
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"设备 {DEVICE_NAME} 创建成功")
    else:
        print(f"设备创建失败: {response.text}")

# 发送设备属性数据
def send_device_attributes(jwt_token, device_id):
    server_attributes_url = f"{THINGSBOARD_HOST}/api/plugins/telemetry/DEVICE/{device_id}/attributes/SERVER_SCOPE"
    server_attributes_payload = {
        "Device Name": config.get('Device', 'device_name'),
        "Device EUI": "24E124710D371756",
        "Device-Profile": "ClassC-OTAA",
        "Payload Codec": "AM319-Ecobook",
        "Application": "Ecobook-IAQ-24E124710D371756"
    }
    headers = {
        "Content-Type": "application/json",
        "X-Authorization": f"Bearer {jwt_token}"
    }
    server_attributes_resp = requests.post(server_attributes_url, json=server_attributes_payload, headers=headers)
    try:
        server_attributes_resp.raise_for_status()
        print(f"设备属性数据已发送成功: {server_attributes_payload}")
    except requests.exceptions.HTTPError as e:
        print(f"设备属性数据发送失败: {server_attributes_resp.status_code}, 响应内容: {server_attributes_resp.text}")
        raise e

# 检查设备配置文件是否已存在
def check_device_profile_exists(jwt_token):
    url = f"{THINGSBOARD_HOST}/api/deviceProfiles?limit=100"
    headers = {
        "X-Authorization": f"Bearer {jwt_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        profiles = response.json().get('data', [])
        for profile in profiles:
            if profile['name'] == DEVICE_PROFILE_NAME:
                print(f"设备配置文件 {DEVICE_PROFILE_NAME} 已存在，跳过创建")
                return True
    return False

# 检查设备是否已存在并返回设备 ID
def check_device_exists(jwt_token):
    url = f"{THINGSBOARD_HOST}/api/tenant/devices?deviceName={DEVICE_NAME}"
    headers = {
        "X-Authorization": f"Bearer {jwt_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        device = response.json()
        if device:
            print(f"设备 {DEVICE_NAME} 已存在，跳过创建")
            return device['id']['id']  # 返回设备 ID
    return None

# 发送遥测数据
def send_telemetry(jwt_token, device_id):
    access_token = config.get('Device', 'access_token')
    telemetry_url = f"{THINGSBOARD_HOST}/api/v1/{access_token}/telemetry"
    headers = {
        "Content-Type": "application/json"
    }
    while True:
        telemetry_payload = {
            "temperature": 25 + int(time.time()) % 5,
            "humidity": 50 + int(time.time()) % 10
        }
        resp = requests.post(telemetry_url, json=telemetry_payload, headers=headers)
        if resp.status_code == 200:
            print(f"遥测数据已发送: {telemetry_payload}")
        else:
            print(f"遥测数据发送失败: {resp.status_code}, {resp.text}")
        time.sleep(10)

# 主流程
if __name__ == "__main__":
    try:
        jwt_token = get_jwt_token()
        if not check_device_profile_exists(jwt_token):
            create_device_profile(jwt_token)
        device_id = check_device_exists(jwt_token)
        if not device_id:
            create_device(jwt_token)
            device_id = check_device_exists(jwt_token)
        send_device_attributes(jwt_token, device_id)
        send_telemetry(jwt_token, device_id)
    except Exception as e:
        print(f"发生错误: {e}")

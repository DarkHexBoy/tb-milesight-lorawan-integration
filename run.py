# -*- coding: utf-8 -*-
import requests
import time
import threading
import paho.mqtt.client as mqtt
import json

# ================= 配置 =================
TB_HOST = "https://thingsboard.cloud"
USERNAME = "van.fan@milesight.com"
PASSWORD = "*******"

GATEWAY_NAME = "MyPythonGateway"
DEVICE_PROFILE_NAME = "GatewayProfile"
SENSORS = ["Sensor1", "Sensor2", "Sensor3"]

# 网关固定属性
CLIENT_ATTRIBUTES = {
    "Model": "UG65-L04EU-915M-EA",
    "Partnumber": "UG65-915",
    "Region": "US915",
    "SerialNumber": "6221E1789420",
    "FirmwareVersion": "60.0.0.47-a4",
    "HardwareVersion": "V1.3"
}

# ================= HTTP 登录获取 JWT =================
login_url = f"{TB_HOST}/api/auth/login"
login_resp = requests.post(login_url, json={"username": USERNAME, "password": PASSWORD})
login_resp.raise_for_status()
jwt_token = login_resp.json()['token']
headers = {'Content-Type': 'application/json', 'X-Authorization': f'Bearer {jwt_token}'}
print(f"[INFO] 登录成功，JWT token 获取完毕")

# ================= HTTP 创建网关设备 =================
# 检查 Device Profile
profiles_resp = requests.get(f"{TB_HOST}/api/deviceProfiles?pageSize=100&page=0", headers=headers)
profiles_resp.raise_for_status()
profiles = profiles_resp.json().get('data', [])
existing_profile = next((p for p in profiles if p['name'] == DEVICE_PROFILE_NAME), None)

if existing_profile:
    device_profile_id = existing_profile['id']['id']
    print(f"[INFO] Device Profile 已存在: {DEVICE_PROFILE_NAME}")
else:
    profile_payload = {
        "name": DEVICE_PROFILE_NAME,
        "type": "DEFAULT",
        "transportType": "DEFAULT",
        "profileData": {"configuration": {"type": "DEFAULT"},
                        "transportConfiguration": {"type": "DEFAULT"}}
    }
    resp = requests.post(f"{TB_HOST}/api/deviceProfile", json=profile_payload, headers=headers)
    resp.raise_for_status()
    device_profile_id = resp.json()['id']['id']
    print(f"[INFO] Device Profile 创建成功: {DEVICE_PROFILE_NAME}")

# 检查并创建网关
devices_resp = requests.get(f"{TB_HOST}/api/tenant/devices?pageSize=100&page=0", headers=headers)
devices_resp.raise_for_status()
devices = devices_resp.json().get('data', [])
existing_device = next((d for d in devices if d['name'] == GATEWAY_NAME), None)

if existing_device:
    device_id = existing_device['id']['id']
    print(f"[INFO] 网关设备已存在: {GATEWAY_NAME}")
else:
    device_payload = {
        "name": GATEWAY_NAME,
        "type": "DEFAULT",
        "deviceProfileId": {"id": device_profile_id, "entityType": "DEVICE_PROFILE"},
        "additionalInfo": {"gateway": True}
    }
    resp = requests.post(f"{TB_HOST}/api/device", json=device_payload, headers=headers)
    resp.raise_for_status()
    device_id = resp.json()['id']['id']
    print(f"[INFO] 网关设备创建成功，ID: {device_id}")

# 获取网关 Access Token
credentials_resp = requests.get(f"{TB_HOST}/api/device/{device_id}/credentials", headers=headers)
credentials_resp.raise_for_status()
GATEWAY_TOKEN = credentials_resp.json()['credentialsId']
print(f"[INFO] 网关 Access Token 获取成功: {GATEWAY_TOKEN}")

# 上报网关固定属性
attr_url = f"{TB_HOST}/api/v1/{GATEWAY_TOKEN}/attributes"
requests.post(attr_url, json=CLIENT_ATTRIBUTES, headers={'Content-Type': 'application/json'}).raise_for_status()
print(f"[INFO] 网关属性上报成功")

# ================= MQTT 客户端 =================
MQTT_CLIENT = mqtt.Client(GATEWAY_NAME)
MQTT_CLIENT.username_pw_set(GATEWAY_TOKEN)
MQTT_CLIENT.connect("thingsboard.cloud", 1883, 60)
MQTT_CLIENT.loop_start()
time.sleep(1)

# 注册子设备
for sensor in SENSORS:
    payload = {"device": sensor, "type": "Sensor"}
    MQTT_CLIENT.publish("v1/gateway/connect", json.dumps(payload), qos=1)
    print(f"[INFO] 注册子设备: {sensor}")
time.sleep(2)

# ================= 网关 telemetry 线程 =================
def gateway_telemetry_thread():
    url = f"{TB_HOST}/api/v1/{GATEWAY_TOKEN}/telemetry"
    while True:
        data = {
            "LocalTime": time.strftime("%Y-%m-%d %H:%M:%S %A"),
            "Uptime": "13days,03:26:19",
            "CPULoad": 7.0,
            "RAM_Capacity_MB": 512,
            "RAM_Available_MB": 121,
            "RAM_Usage_Percent": 23.63,
            "eMMC_Capacity_GB": 8.0,
            "eMMC_Available_GB": 6.5,
            "eMMC_Usage_Percent": 80.88
        }
        try:
            requests.post(url, json=data, headers={'Content-Type': 'application/json'}).raise_for_status()
            print(f"[INFO] 网关 telemetry: {data}")
        except Exception as e:
            print(f"[ERROR] 网关 telemetry 发送失败: {e}")
        time.sleep(10)

# ================= 子设备 telemetry 线程 =================
def sensor_telemetry_thread(sensor_name):
    while True:
        ts = int(time.time() * 1000)
        telemetry = [{
            "ts": ts,
            "values": {
                "temperature": round(20 + 5*(time.time()%6)/5, 2),
                "humidity": round(50 + 10*(time.time()%6)/5, 2)
            }
        }]
        payload = {sensor_name: telemetry}
        MQTT_CLIENT.publish("v1/gateway/telemetry", json.dumps(payload), qos=1)
        print(f"[INFO] {sensor_name} telemetry: {telemetry}")
        time.sleep(10)

# 启动线程
threading.Thread(target=gateway_telemetry_thread, daemon=True).start()
for sensor in SENSORS:
    threading.Thread(target=sensor_telemetry_thread, args=(sensor,), daemon=True).start()

# 主线程保持
while True:
    time.sleep(1)

"""
MQTT Publisher - Excel-driven HR/SpO2 publisher
Uses your dataset from:
D:\\Semester 7\\DTCA Project\\iot-health-dashboard\\patients_data_with_alerts.xlsx
"""

import json
import time
import os
import ssl
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

# MQTT config
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC_HR = os.getenv("MQTT_TOPIC_HR", "sensors/hr")
MQTT_TOPIC_SPO2 = os.getenv("MQTT_TOPIC_SPO2", "sensors/spo2")
INTERVAL = float(os.getenv("DATA_GENERATION_INTERVAL", 2.0))

# Your Excel dataset path
EXCEL_PATH = r"D:\Semester 7\DTCA Project\iot-health-dashboard\patients_data_with_alerts.xlsx"

# Accepted column names
HR_KEYS = ("HeartRate", "HR", "heart_rate", "hr", "Heart Rate")
SPO2_KEYS = ("SpO2", "spo2", "SPO2", "O2", "Sp O2")

def load_excel_rows(path):
    try:
        df = pd.read_excel(path, engine="openpyxl")
        print(f"📥 Excel loaded successfully ({len(df)} rows)")
        print("Columns detected:", list(df.columns))
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        print(f"❌ Failed to load Excel: {e}")
        return []

def get_value(row, keys):
    # check case-insensitive header matches
    for key in row.keys():
        for k in keys:
            if str(key).strip().lower() == str(k).strip().lower():
                return row[key]
    return None

def safe_int(v):
    if v in (None, ""): return None
    try:
        return int(float(v))
    except:
        return None

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT")
    else:
        print("❌ MQTT connection failed:", rc)

def on_publish(client, userdata, mid):
    print(f"📤 Published MID={mid}")

def main():
    rows = load_excel_rows(EXCEL_PATH)
    if not rows:
        print("❌ No data to publish.")
        return

    client = mqtt.Client(client_id="excel_health_publisher")
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    # TLS for HiveMQ Cloud
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
    client.on_connect = on_connect
    client.on_publish = on_publish

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    idx = 0
    last_hr = None
    last_spo2 = None

    print(f"🚀 Publishing data from Excel every {INTERVAL} seconds…")

    try:
        while True:
            row = rows[idx]

            raw_hr = get_value(row, HR_KEYS)
            raw_spo2 = get_value(row, SPO2_KEYS)

            hr = safe_int(raw_hr)
            spo2 = safe_int(raw_spo2)

            if hr is None: hr = last_hr
            else: last_hr = hr

            if spo2 is None: spo2 = last_spo2
            else: last_spo2 = spo2

            timestamp = datetime.utcnow().isoformat()

            hr_payload = {
                "value": hr,
                "timestamp": timestamp,
                "unit": "BPM"
            }

            spo2_payload = {
                "value": spo2,
                "timestamp": timestamp,
                "unit": "%"
            }

            client.publish(MQTT_TOPIC_HR, json.dumps(hr_payload), qos=1)
            client.publish(MQTT_TOPIC_SPO2, json.dumps(spo2_payload), qos=1)

            print(f"📡 [{idx+1}/{len(rows)}] HR={hr}, SpO2={spo2} → sent")

            idx += 1
            if idx >= len(rows):   # Loop again
                idx = 0

            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")

    finally:
        client.loop_stop()
        client.disconnect()
        print("👋 Publisher stopped")

if __name__ == "__main__":
    main()

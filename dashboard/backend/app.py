"""
Flask Backend - IoT Health Monitoring System
- Subscribes to MQTT for sensor data
- Runs ML predictions (4 models)
- Writes results to OPC UA server
- Saves to Firebase Cloud
"""

from flask import Flask, jsonify
from flask_cors import CORS
import paho.mqtt.client as mqtt
from opcua import Client as OPCUAClient
import firebase_admin
from firebase_admin import credentials, db
import joblib
import numpy as np
import json
import ssl
from datetime import datetime
from dotenv import load_dotenv
import os
import threading
import traceback
from opcua import ua

# Load environment variables
load_dotenv()

# Initialize Flask
app = Flask(__name__)
CORS(app)

# =========================
# CONFIGURATION
# =========================
MQTT_BROKER = os.getenv('MQTT_BROKER')
MQTT_PORT = int(os.getenv('MQTT_PORT', 8883))
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
MQTT_TOPIC_HR = os.getenv('MQTT_TOPIC_HR')
MQTT_TOPIC_SPO2 = os.getenv('MQTT_TOPIC_SPO2')

OPCUA_SERVER_URL = os.getenv('OPCUA_SERVER_URL')
OPCUA_USER = os.getenv('OPCUA_USER', 'yourservername')
OPCUA_PASSWORD = os.getenv('OPCUA_PASSWORD', 'yourpassword')
OPCUA_NAMESPACE = os.getenv('OPCUA_NAMESPACE', 'HealthMonitoring')

# =========================
# GLOBAL VARIABLES
# =========================
latest_hr = 70
latest_spo2 = 98
latest_sensor_timestamp = None  
mqtt_client = None
opcua_client = None
mqtt_connected = False
opcua_connected = False

# =========================
# LOAD ML MODELS
# =========================
print("🤖 Loading ML Models...")

try:
    anomaly_model = joblib.load('models/anomaly_iforest.joblib')
    arrhythmia_model = joblib.load('models/arrhythmia_model.joblib')
    brady_model = joblib.load('models/brady_model.joblib')
    tachy_model = joblib.load('models/tachy_model.joblib')
    print("✅ All models loaded successfully!")
except Exception as e:
    print(f"⚠️  Models not found: {e}")
    print("📝 Using dummy predictions for now. Add your models to 'models/' folder")
    anomaly_model = None
    arrhythmia_model = None
    brady_model = None
    tachy_model = None

# =========================
# FIREBASE INITIALIZATION
# =========================
print("🔥 Initializing Firebase...")
try:
    cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
    if cred_path:
        cred = credentials.Certificate(cred_path)
        # initialize_app will raise if already initialized in the same process
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'databaseURL': os.getenv('FIREBASE_DATABASE_URL',
                                         'https://iot-project-27-default-rtdb.firebaseio.com')
            })
        firebase_ref = db.reference('realtime_data')
        logs_ref = db.reference('logs')
        print("✅ Firebase connected!")
    else:
        raise RuntimeError("FIREBASE_CREDENTIALS_PATH not set")
except Exception as e:
    print(f"⚠️  Firebase initialization failed: {e}")
    firebase_ref = None
    logs_ref = None

# =========================
# ML PREDICTION FUNCTION
# =========================
def predict_health_status(heart_rate, spo2):
    """
    Run all ML models and generate predictions
    Input: heart_rate (int|str), spo2 (int|str)
    Output: dict with predictions and recommendation
    """

    # Defensive: coerce to ints (if possible)
    try:
        hr = int(float(heart_rate))
    except Exception:
        print(f"⚠️ predict_health_status: invalid heart_rate input: {heart_rate!r}. Using 0.")
        hr = 0

    try:
        sp = int(float(spo2))
    except Exception:
        print(f"⚠️ predict_health_status: invalid spo2 input: {spo2!r}. Using 0.")
        sp = 0

    features = np.array([[hr, sp]])

    # Initialize predictions (defaults)
    predictions = {
        'anomaly': False,
        'arrhythmia': 0,
        'bradycardia': 0,
        'tachycardia': 0
    }

    # Run predictions if models are loaded; print exceptions if any
    if anomaly_model:
        try:
            # some anomaly models require different input; be careful
            anomaly_pred = anomaly_model.predict(features)[0]
            predictions['anomaly'] = (anomaly_pred == -1 or bool(anomaly_pred))
        except Exception as e:
            print("⚠️ anomaly_model.predict failed:", e)
            traceback.print_exc()

    if arrhythmia_model:
        try:
            predictions['arrhythmia'] = int(arrhythmia_model.predict(features)[0])
        except Exception as e:
            print("⚠️ arrhythmia_model.predict failed:", e)
            traceback.print_exc()

    if brady_model:
        try:
            predictions['bradycardia'] = int(brady_model.predict(features)[0])
        except Exception as e:
            print("⚠️ brady_model.predict failed:", e)
            traceback.print_exc()

    if tachy_model:
        try:
            predictions['tachycardia'] = int(tachy_model.predict(features)[0])
        except Exception as e:
            print("⚠️ tachy_model.predict failed:", e)
            traceback.print_exc()

    # If none of the models are available or all failed, use rule-based fallback
    if not any([anomaly_model, arrhythmia_model, brady_model, tachy_model]):
        predictions = {
            'anomaly': (hr < 40 or hr > 140 or sp < 90),
            'arrhythmia': 1 if (hr < 45 or hr > 130) else 0,
            'bradycardia': 1 if hr < 60 else 0,
            'tachycardia': 1 if hr > 100 else 0
        }

    # If models existed but predictions are all zeros (possible model error), optionally fallback:
    # if all values are falsy here you may still want to run rule-based fallback — optional:
    if not any([predictions['anomaly'], predictions['arrhythmia'], predictions['bradycardia'], predictions['tachycardia']]) and any([anomaly_model, arrhythmia_model, brady_model, tachy_model]):
        # no predicted events from models — but we might still want rule based check to avoid silent misses
        try:
            rule_preds = {
                'anomaly': (hr < 40 or hr > 140 or sp < 90),
                'arrhythmia': 1 if (hr < 45 or hr > 130) else 0,
                'bradycardia': 1 if hr < 60 else 0,
                'tachycardia': 1 if hr > 100 else 0
            }
            # If rule says something is flagged, accept it as a fallback
            if any(rule_preds.values()):
                print("⚠️ Models returned no flags — using rule-based fallback:", rule_preds)
                predictions = rule_preds
        except Exception:
            pass

    status, recommendation = generate_recommendation(predictions, hr, sp)
    return { **predictions, 'status': status, 'recommendation': recommendation }

# =========================
# RECOMMENDATION GENERATOR
# =========================
def generate_recommendation(predictions, heart_rate, spo2):
    """Generate detailed health recommendations based on predictions"""

    if predictions['anomaly']:
        return "Anomaly Detected", (
            "⚠️ ANOMALY DETECTED: Unusual health pattern identified. "
            f"Your current readings (HR: {heart_rate} BPM, SpO2: {spo2}%) fall outside normal ranges. "
            "This could indicate multiple underlying issues. "
            "IMMEDIATE ACTION: Monitor closely for the next 15-30 minutes. "
            "If symptoms like dizziness, chest pain, or shortness of breath occur, seek emergency medical attention. "
            "Contact your healthcare provider as soon as possible for evaluation."
        )

    if predictions['arrhythmia'] == 1:
        return "Arrhythmia Detected", (
            "⚠️ IRREGULAR HEART RHYTHM: Your heart is beating in an irregular pattern. "
            "Arrhythmia means your heart may be beating too fast, too slow, or with an irregular rhythm. "
            f"Current heart rate: {heart_rate} BPM. "
            "WHAT TO DO: Sit or lie down immediately. Take slow, deep breaths. "
            "Avoid caffeine, alcohol, and strenuous activity. "
            "SEEK MEDICAL ATTENTION if you experience chest pain, extreme shortness of breath, "
            "dizziness, or fainting. This condition requires professional medical evaluation. "
            "Keep a record of when these episodes occur and their duration."
        )

    if predictions['bradycardia'] == 1:
        return "Bradycardia Detected", (
            f"⚠️ LOW HEART RATE: Your heart rate of {heart_rate} BPM is below the normal resting range (60-100 BPM). "
            "Bradycardia means your heart is beating slower than normal. While this can be normal for athletes, "
            "it may indicate an underlying condition if accompanied by symptoms. "
            "SYMPTOMS TO WATCH: Fatigue, dizziness, weakness, confusion, or fainting. "
            "IMMEDIATE STEPS: Sit or lie down, stay warm, and avoid sudden movements. "
            "WHEN TO SEEK HELP: Contact your doctor if this persists or you feel unwell. "
            "Call emergency services if you experience severe symptoms like fainting, chest pain, or extreme fatigue. "
            "Possible causes include heart problems, medications, or electrolyte imbalances."
        )

    if predictions['tachycardia'] == 1:
        return "Tachycardia Detected", (
            f"⚠️ ELEVATED HEART RATE: Your heart rate of {heart_rate} BPM exceeds the normal resting range (60-100 BPM). "
            "Tachycardia means your heart is beating faster than normal, which can reduce blood flow efficiency. "
            "IMMEDIATE ACTIONS: Sit down and relax. Practice deep breathing exercises - inhale for 4 counts, hold for 4, exhale for 4. "
            "Apply cold water to your face or drink cold water slowly. "
            "AVOID: Caffeine, energy drinks, alcohol, smoking, and strenuous activity. "
            "CAUSES: Can be triggered by stress, anxiety, dehydration, fever, medications, or underlying heart conditions. "
            "SEEK MEDICAL ATTENTION if your heart rate stays above 120 BPM at rest, or if you experience "
            "chest pain, severe shortness of breath, or dizziness. "
            "If this is recurring, schedule a check-up with your cardiologist."
        )

    # Normal condition
    if spo2 < 95:
        return "Low Oxygen Levels", (
            f"⚠️ OXYGEN SATURATION LOW: Your SpO2 level of {spo2}% is below the healthy range (95-100%). "
            "This means your blood isn't carrying enough oxygen to your organs. "
            "IMMEDIATE STEPS: Sit upright to maximize lung capacity. Take slow, deep breaths. "
            "Move to fresh air if possible. Remove any tight clothing around chest/neck. "
            "WHEN TO WORRY: SpO2 below 90% requires immediate medical attention. "
            "Seek emergency help if you have severe shortness of breath, bluish lips or fingernails, "
            "chest pain, or confusion. Causes can include lung problems, heart issues, or high altitude. "
            "If you have chronic conditions like COPD or asthma, follow your action plan and contact your doctor."
        )

    return "Normal", (
        f"✅ HEALTHY VITALS: Your health parameters are within normal ranges. "
        f"Heart Rate: {heart_rate} BPM (Normal: 60-100), SpO2: {spo2}% (Normal: 95-100%). "
        "MAINTAIN GOOD HEALTH: Continue regular exercise (at least 150 minutes of moderate activity per week), "
        "eat a balanced diet rich in fruits, vegetables, and whole grains, "
        "stay hydrated (8 glasses of water daily), get 7-9 hours of quality sleep, "
        "manage stress through relaxation techniques, and avoid smoking and excessive alcohol. "
        "Regular check-ups with your healthcare provider are recommended every 6-12 months. "
        "Monitor your vitals regularly and report any significant changes to your doctor."
    )

# =========================
# OPC UA FUNCTIONS
# =========================
def connect_opcua():
    """Create and connect the global OPC UA client"""
    global opcua_client, opcua_connected
    if not OPCUA_SERVER_URL:
        print("⚠️  OPCUA_SERVER_URL not set")
        opcua_connected = False
        return False

    try:
        opcua_client = OPCUAClient(OPCUA_SERVER_URL)
        # set user/password if provided
        if OPCUA_USER:
            try:
                opcua_client.set_user("dtcaproject")
                opcua_client.set_password("dtca")
            except Exception:
                print(f"⚠️ Failed to set OPC UA authentication: {e}")

        opcua_client.connect()
        opcua_connected = True
        print(f"✅ Connected to OPC UA Server: {OPCUA_SERVER_URL}")
        return True
    except Exception as e:
        opcua_client = None
        opcua_connected = False
        print(f"❌ OPC UA connection failed: {e}")
        return False
    
from opcua import ua
import traceback

def write_to_opcua(heart_rate, spo2, predictions):
    """
    Typed write + immediate readback diagnostics for OPC UA nodes.
    Assumes opcua_client is already connected and authenticated.
    """
    global opcua_client
    if not opcua_client:
        print("⚠️ No OPC UA client available for writing.")
        return

    try:
        # get nodes either via browse path or fallback to nodeids (use what's working)
        try:
            objects = opcua_client.get_objects_node()
            health_monitoring = objects.get_child([f"3:{OPCUA_NAMESPACE}"])
            hr_node = health_monitoring.get_child(["3:HeartRate"])
            spo2_node = health_monitoring.get_child(["3:SpO2"])
            timestamp_node = health_monitoring.get_child(["3:Timestamp"])
            predictions_folder = health_monitoring.get_child(["3:Predictions"])
            anomaly_node = predictions_folder.get_child(["3:Anomaly"])
            arrhythmia_node = predictions_folder.get_child(["3:Arrhythmia"])
            brady_node = predictions_folder.get_child(["3:Bradycardia"])
            tachy_node = predictions_folder.get_child(["3:Tachycardia"])
            status_node = health_monitoring.get_child(["3:Status"])
            rec_node = health_monitoring.get_child(["3:Recommendation"])
        except Exception as e:
            # fallback node ids you showed in UA Expert
            print("ℹ️ Browse path failed, using direct node ids as fallback.")
            hr_node = opcua_client.get_node("ns=3;i=1020")
            spo2_node = opcua_client.get_node("ns=3;i=1021")
            timestamp_node = opcua_client.get_node("ns=3;i=1022")
            arrhythmia_node = opcua_client.get_node("ns=3;i=1023")
            anomaly_node = opcua_client.get_node("ns=3;i=1024")
            brady_node = opcua_client.get_node("ns=3;i=1025")
            tachy_node = opcua_client.get_node("ns=3;i=1026")
            status_node = opcua_client.get_node("ns=3;s=1027")
            rec_node = opcua_client.get_node("ns=3;s=1028")

        # Build typed Variants (match your UA Expert types)
        hr_variant = ua.Variant(int(heart_rate), ua.VariantType.Int32)
        spo2_variant = ua.Variant(int(spo2), ua.VariantType.Int32)

        anomaly_variant = ua.Variant(bool(predictions.get('anomaly', False)), ua.VariantType.Boolean)
        arrhythmia_variant = ua.Variant(bool(predictions.get('arrhythmia', 0)), ua.VariantType.Boolean)
        brady_variant = ua.Variant(bool(predictions.get('bradycardia', 0)), ua.VariantType.Boolean)
        tachy_variant = ua.Variant(bool(predictions.get('tachycardia', 0)), ua.VariantType.Boolean)

        status_variant = ua.Variant(str(predictions.get('status', '')), ua.VariantType.String)
        rec_text = str(predictions.get('recommendation', ''))[:2000]
        rec_variant = ua.Variant(rec_text, ua.VariantType.String)

        # Timestamp node on your server is String per UA Expert screenshots
        timestamp_str = datetime.now().isoformat()
        timestamp_variant = ua.Variant(timestamp_str, ua.VariantType.String)

        # Now write DataValues
        hr_node.set_value(ua.DataValue(hr_variant))
        spo2_node.set_value(ua.DataValue(spo2_variant))
        anomaly_node.set_value(ua.DataValue(anomaly_variant))
        arrhythmia_node.set_value(ua.DataValue(arrhythmia_variant))
        brady_node.set_value(ua.DataValue(brady_variant))
        tachy_node.set_value(ua.DataValue(tachy_variant))
        status_node.set_value(ua.DataValue(status_variant))
        rec_node.set_value(ua.DataValue(rec_variant))
        timestamp_node.set_value(ua.DataValue(timestamp_variant))

        print("✅ Typed write calls completed — now reading back values for diagnostics...")

        # Readback diagnostics helper
        def readback(node, label):
            dv = node.get_data_value()  # returns ua.DataValue
            val = dv.Value.Value if dv and dv.Value else None
            sc = dv.StatusCode.Name if dv and dv.StatusCode else None
            s_ts = dv.ServerTimestamp if dv else None
            src_ts = dv.SourceTimestamp if dv else None
            print(f"[READBACK] {label} -> Value: {val!r} | StatusCode: {sc} | SourceTS: {src_ts} | ServerTS: {s_ts}")

        readback(hr_node, "HeartRate")
        readback(spo2_node, "SpO2")
        readback(anomaly_node, "Anomaly")
        readback(arrhythmia_node, "Arrhythmia")
        readback(brady_node, "Bradycardia")
        readback(tachy_node, "Tachycardia")
        readback(status_node, "Status")
        readback(rec_node, "Recommendation")
        readback(timestamp_node, "Timestamp")

    except Exception as e:
        # print(f"⚠️ OPC UA typed write/readback failed: {e}")
        traceback.print_exc()

# Alternative: Simple node finder helper function
def find_and_print_node_ids():
    """
    Helper function to find all your node IDs
    Run this once to get all the node IDs, then update write_to_opcua()
    """
    global opcua_client
    if not opcua_client:
        print("OPC UA client not connected")
        return

    try:
        objects = opcua_client.get_objects_node()

        # Browse HealthMonitoring folder
        print("\n🔍 Finding all node IDs in HealthMonitoring:")
        print("=" * 60)

        health_monitoring = objects.get_child([f"3:{OPCUA_NAMESPACE}"])
        print(f"HealthMonitoring: {health_monitoring.nodeid}")

        # Get all children
        children = health_monitoring.get_children()
        for child in children:
            browse_name = child.get_browse_name()
            node_id = child.nodeid
            print(f"  {browse_name.Name}: {node_id}")

            # If it's the Predictions folder, browse its children too
            if browse_name.Name == "Predictions":
                pred_children = child.get_children()
                for pred_child in pred_children:
                    pred_browse_name = pred_child.get_browse_name()
                    pred_node_id = pred_child.nodeid
                    print(f"    {pred_browse_name.Name}: {pred_node_id}")

        print("=" * 60)
        print("Copy these node IDs and update write_to_opcua() function!")

    except Exception as e:
        print(f"Error browsing nodes: {e}")

# =========================
# FIREBASE FUNCTIONS
# =========================
def write_to_firebase(heart_rate, spo2, predictions):
    """Write data to Firebase Realtime Database"""
    if not firebase_ref:
        return

    try:
        timestamp = datetime.now().isoformat()

        data = {
            'HeartRate': heart_rate,
            'SpO2': spo2,
            'anomaly': predictions['anomaly'],
            'arrhythmia': predictions['arrhythmia'],
            'bradycardia': predictions['bradycardia'],
            'tachycardia': predictions['tachycardia'],
            'prediction': predictions['status'],
            'recommendation': predictions['recommendation'],
            'timestamp': timestamp
        }

        # Update realtime data
        firebase_ref.set(data)

        # Add to logs
        if logs_ref:
            logs_ref.push(data)

        print("✅ Data written to Firebase")

    except Exception as e:
        print(f"⚠️  Firebase write failed: {e}")

# =========================
# MQTT CALLBACKS
# =========================
def on_connect(client, userdata, flags, rc):
    """Callback when MQTT client connects"""
    global mqtt_connected
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        try:
            client.subscribe([(MQTT_TOPIC_HR, 1), (MQTT_TOPIC_SPO2, 1)])
            print(f"📡 Subscribed to: {MQTT_TOPIC_HR}, {MQTT_TOPIC_SPO2}")
        except Exception as e:
            print(f"❌ Subscription failed: {e}")
        mqtt_connected = True
    else:
        print(f"❌ MQTT Connection failed with code {rc}")
        mqtt_connected = False

def on_message(client, userdata, msg):
    """Callback when MQTT message is received"""
    global latest_hr, latest_spo2

    try:
        payload = json.loads(msg.payload.decode())

        # Accept payloads with {"value": 72} or numeric values directly
        if msg.topic == MQTT_TOPIC_HR:
            raw = payload.get('value', payload.get('HeartRate', payload.get('hr', latest_hr)))
            try:
                latest_hr = int(float(raw))
            except Exception:
                print(f"⚠️ Could not parse HR value: {raw!r} — keeping previous: {latest_hr}")
            print(f"💓 Received HR: {latest_hr} BPM")

        elif msg.topic == MQTT_TOPIC_SPO2:
            raw = payload.get('value', payload.get('SpO2', payload.get('spo2', latest_spo2)))
            try:
                latest_spo2 = int(float(raw))
            except Exception:
                print(f"⚠️ Could not parse SpO2 value: {raw!r} — keeping previous: {latest_spo2}")
            print(f"🫁 Received SpO2: {latest_spo2}%")

        # Process data when values are updated
        process_health_data()

    except Exception as e:
        print(f"⚠️  Error processing MQTT message: {e}")
        traceback.print_exc()

def process_health_data():
    """Process health data and make predictions"""
    global latest_hr, latest_spo2

    print(f"\n🔬 Processing: HR={latest_hr}, SpO2={latest_spo2}")

    # Run ML predictions
    predictions = predict_health_status(latest_hr, latest_spo2)

    print(f"📊 Predictions:")
    print(f"   - Anomaly: {predictions['anomaly']}")
    print(f"   - Arrhythmia: {predictions['arrhythmia']}")
    print(f"   - Bradycardia: {predictions['bradycardia']}")
    print(f"   - Tachycardia: {predictions['tachycardia']}")
    print(f"   - Status: {predictions['status']}")

    # Write to OPC UA
    write_to_opcua(latest_hr, latest_spo2, predictions)

    # Write to Firebase
    write_to_firebase(latest_hr, latest_spo2, predictions)

    print("-" * 60)

# =========================
# MQTT INITIALIZATION
# =========================
def init_mqtt():
    """Initialize MQTT client"""
    global mqtt_client, mqtt_connected

    print("🚀 Initializing MQTT Client...")
    mqtt_client = mqtt.Client(client_id="health_ml_backend")
    if MQTT_USERNAME or MQTT_PASSWORD:
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    # Enable TLS for HiveMQ Cloud (if using TLS)
    try:
        mqtt_client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
    except Exception:
        # If broker doesn't support TLS or certs are not present, ignore and proceed (or configure properly)
        pass

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        # mqtt_connected will be set in on_connect callback
        return True
    except Exception as e:
        print(f"❌ MQTT connection failed: {e}")
        mqtt_connected = False
        return False

# =========================
# FLASK ROUTES
# =========================
@app.route('/')
def home():
    try:
        mqtt_status = mqtt_connected
    except Exception:
        mqtt_status = False

    try:
        opcua_status = opcua_connected
    except Exception:
        opcua_status = False

    return jsonify({
        "status": "running",
        "service": "IoT Health Monitoring Backend",
        "mqtt_connected": mqtt_status,
        "opcua_connected": opcua_status,
        "firebase_connected": firebase_ref is not None
    })

@app.route('/health')
def health():
    return jsonify({
        "HeartRate": latest_hr,
        "SpO2": latest_spo2
    })

@app.route('/status')
def status():
    predictions = predict_health_status(latest_hr, latest_spo2)
    return jsonify({
        "HeartRate": latest_hr,
        "SpO2": latest_spo2,
        **predictions
    })

# =========================
# MAIN FUNCTION
# =========================
def main():
    print("\n" + "="*60)
    print("🏥 IoT HEALTH MONITORING SYSTEM - BACKEND")
    print("="*60 + "\n")

    # Initialize connections
    mqtt_ok = init_mqtt()
    opcua_ok = connect_opcua()

    if not mqtt_ok:
        print("⚠️  Warning: MQTT init failed. Check your HiveMQ credentials and broker URL.")

    if not opcua_ok:
        print("⚠️  Warning: OPC UA not connected. Check your Prosys server or OPCUA_SERVER_URL.")

    # Start Flask app
    print("\n🌐 Starting Flask Backend on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()

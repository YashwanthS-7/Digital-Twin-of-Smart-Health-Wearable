# 🏥 IoT Health Monitoring System

<div align="center">

![Status](https://img.shields.io/badge/status-active-success.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![React](https://img.shields.io/badge/react-18.0+-61dafb.svg)

**A complete IoT-based health monitoring system with AI-powered predictions, real-time data visualization, and industrial protocols (MQTT & OPC UA)**

[Features](#features) • [Architecture](#architecture) • [Installation](#installation) • [Usage](#usage) • [Documentation](#documentation)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technologies](#technologies)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Machine Learning Models](#machine-learning-models)
- [Communication Protocols](#communication-protocols)
- [Screenshots](#screenshots)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## 🎯 Overview

The **IoT Health Monitoring System** is a comprehensive solution for real-time patient health monitoring using Internet of Things (IoT) technologies. It combines **Machine Learning**, **Cloud Computing**, and **Industrial IoT Protocols** to provide:

- 🔴 Real-time vital signs monitoring (Heart Rate & Blood Oxygen)
- 🤖 AI-powered health condition detection
- 📊 Interactive data visualization dashboard
- ☁️ Cloud-based data storage and synchronization
- 🏭 Industrial protocol support (MQTT & OPC UA)
- 📱 Responsive web interface
- 📈 Historical data analysis and export

### 🎓 Perfect For:
- Healthcare IoT demonstrations
- Medical research projects
- Remote patient monitoring systems
- IoT and ML learning projects
- Industrial automation integration

---

## ✨ Features

### Core Features
- ✅ **Real-time Monitoring**: Track heart rate and SpO2 levels every 2 seconds
- ✅ **AI Predictions**: 4 ML models detect:
  - Anomaly Detection (Isolation Forest)
  - Arrhythmia (Irregular heart rhythm)
  - Bradycardia (Low heart rate)
  - Tachycardia (High heart rate)
- ✅ **Smart Recommendations**: Detailed health advice based on detected conditions
- ✅ **Cloud Storage**: Firebase Realtime Database for data persistence
- ✅ **Industrial Protocols**: 
  - MQTT for IoT communication
  - OPC UA for industrial monitoring
- ✅ **Data Export**: Download historical data as CSV
- ✅ **Dark/Light Mode**: Beautiful, responsive UI

### Technical Features
- 🔐 Secure TLS/SSL communication
- 📡 Real-time WebSocket updates
- 🎨 Modern React dashboard with Recharts
- 🐍 Python Flask backend
- 🔄 Synthetic data generation for testing
- 📊 Historical data logging
- 🌐 Cross-platform compatibility

---

## 🏗️ Architecture

```
┌─────────────────┐
│ MQTT Publisher  │ (Synthetic Data Generator)
└────────┬────────┘
         │ MQTT Protocol (Port 8883, TLS)
         ▼
┌─────────────────┐
│  HiveMQ Cloud   │ (MQTT Broker)
└────────┬────────┘
         │ Subscribe
         ▼
┌─────────────────────────────────────┐
│      Flask Backend (Python)         │
│  ┌─────────────────────────────┐   │
│  │   ML Prediction Engine      │   │
│  │   • Anomaly Detection       │   │
│  │   • Arrhythmia Detection    │   │
│  │   • Bradycardia Detection   │   │
│  │   • Tachycardia Detection   │   │
│  └─────────────────────────────┘   │
└────────┬──────────────────┬─────────┘
         │                  │
         │ OPC UA           │ Firebase API
         ▼                  ▼
┌─────────────────┐  ┌─────────────────┐
│ Prosys OPC UA   │  │    Firebase     │
│ Server          │  │ Realtime DB     │
└────────┬────────┘  └────────┬────────┘
         │                    │
         ▼                    ▼
┌─────────────────┐  ┌─────────────────┐
│   UA Expert     │  │ React Dashboard │
│   (Monitoring)  │  │   (Frontend)    │
└─────────────────┘  └─────────────────┘
```

---

## 🛠️ Technologies

### Frontend
- **React 18** - UI framework
- **Recharts** - Data visualization
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Firebase SDK** - Real-time database

### Backend
- **Python 3.8+** - Core language
- **Flask 3.0** - Web framework
- **Paho MQTT** - MQTT client
- **OPC UA** - Industrial protocol
- **Firebase Admin SDK** - Backend database
- **Scikit-learn** - ML models
- **NumPy & Pandas** - Data processing

### IoT Protocols
- **MQTT** - Lightweight pub/sub messaging
- **OPC UA** - Industrial communication
- **HTTP/HTTPS** - Web communication
- **WebSocket** - Real-time updates

### Cloud Services
- **HiveMQ Cloud** - Managed MQTT broker
- **Firebase** - NoSQL cloud database
- **Prosys OPC UA** - Simulation server

---

## 📦 Prerequisites

### Software Requirements
- Python 3.8 or higher
- Node.js 16+ and npm
- Prosys OPC UA Simulation Server
- UA Expert (optional, for monitoring)

### Cloud Services
- HiveMQ Cloud account (free tier available)
- Firebase project with Realtime Database

### Hardware (Optional)
- IoT sensors (for real data instead of synthetic)
- Raspberry Pi or similar (for edge deployment)

---

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/iot-health-monitoring.git
cd iot-health-monitoring
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### Create Models Folder
```bash
mkdir models
```

#### Add Your ML Models
Place your trained models in `backend/models/`:
- `anomaly_iforest.joblib`
- `arrhythmia_model.joblib`
- `brady_model.joblib`
- `tachy_model.joblib`

#### Configure Environment Variables
Create `.env` file in `backend/`:
```env
# HiveMQ Cloud MQTT Configuration
MQTT_BROKER=your-hivemq-cluster.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password
MQTT_TOPIC_HR=iot/health/heartrate
MQTT_TOPIC_SPO2=iot/health/spo2

# OPC UA Server Configuration
OPCUA_SERVER_URL=opc.tcp://localhost:53530/OPCUA/SimulationServer
OPCUA_NAMESPACE=HealthMonitoring

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json

# Data Generation Settings
DATA_GENERATION_INTERVAL=2
```

#### Add Firebase Credentials
1. Download `firebase-credentials.json` from Firebase Console
2. Place it in `backend/` folder

### 3. Frontend Setup

```bash
cd frontend
npm install
```

Update `src/Dashboard.js` with your Firebase configuration.

### 4. OPC UA Server Setup

1. Open **Prosys OPC UA Simulation Server**
2. Create folder structure:
   ```
   Objects/
   └── HealthMonitoring/
       ├── HeartRate (Double)
       ├── SpO2 (Double)
       ├── Timestamp (String)
       ├── Predictions/
       │   ├── Anomaly (Boolean)
       │   ├── Arrhythmia (Boolean)
       │   ├── Bradycardia (Boolean)
       │   └── Tachycardia (Boolean)
       ├── Status (String)
       └── Recommendation (String)
   ```
3. Set security to **None** and authentication to **Anonymous**
4. Start the server

---

## ⚙️ Configuration

### MQTT Configuration
```python
# mqtt_publisher.py
MQTT_BROKER = "your-cluster.s1.eu.hivemq.cloud"
MQTT_PORT = 8883  # TLS port
MQTT_TOPICS = {
    'heartrate': 'iot/health/heartrate',
    'spo2': 'iot/health/spo2'
}
```

### OPC UA Configuration
```python
# app.py
OPCUA_SERVER_URL = "opc.tcp://localhost:53530/OPCUA/SimulationServer"
OPCUA_NAMESPACE = "HealthMonitoring"
```

### Firebase Configuration
```javascript
// Dashboard.js
const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  databaseURL: "https://your-project.firebaseio.com",
  projectId: "your-project",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "your-sender-id",
  appId: "your-app-id"
};
```

---

## 🎮 Usage

### Start the System

#### Terminal 1: Start Backend
```bash
cd backend
python app.py
```

Expected output:
```
🤖 Loading ML Models...
✅ All models loaded successfully!
🔥 Initializing Firebase...
✅ Firebase connected!
🚀 Initializing MQTT Client...
✅ Connected to MQTT Broker
🔌 Connecting to OPC UA Server...
✅ OPC UA Client connected!
🌐 Starting Flask Backend on http://localhost:5000
```

#### Terminal 2: Start Data Publisher
```bash
cd backend
python mqtt_publisher.py
```

Expected output:
```
✅ Connected to HiveMQ Cloud MQTT Broker
📡 Publishing to topics: iot/health/heartrate, iot/health/spo2
💓 HR: 72 BPM | 🫁 SpO2: 98% | 📊 Scenario: normal
```

#### Terminal 3: Start Frontend
```bash
cd frontend
npm start
```

Browser opens at: `http://localhost:3000`

### Monitor with UA Expert (Optional)
1. Open **UA Expert**
2. Connect to: `opc.tcp://localhost:53530/OPCUA/SimulationServer`
3. Browse to `Objects/HealthMonitoring`
4. Watch values update in real-time

---

## 📁 Project Structure

```
iot-health-monitoring/
├── backend/
│   ├── models/
│   │   ├── anomaly_iforest.joblib
│   │   ├── arrhythmia_model.joblib
│   │   ├── brady_model.joblib
│   │   └── tachy_model.joblib
│   ├── app.py                      # Main Flask backend
│   ├── mqtt_publisher.py           # Synthetic data generator
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # Environment variables
│   ├── firebase-credentials.json   # Firebase service account
│   └── find_node_ids.py           # OPC UA helper script
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.js
│   │   ├── Dashboard.js           # Main dashboard component
│   │   ├── index.js
│   │   └── index.css
│   ├── package.json
│   └── tailwind.config.js
├── docs/
│   ├── SETUP_GUIDE.md
│   ├── MODEL_INTEGRATION.md
│   ├── OPCUA_SETUP.md
│   └── COMPLETE_DOCUMENTATION.md
├── README.md
└── LICENSE
```

---

## 📡 API Documentation

### Backend Endpoints

#### GET `/`
Health check endpoint
```json
{
  "status": "running",
  "service": "IoT Health Monitoring Backend",
  "mqtt_connected": true,
  "opcua_connected": true,
  "firebase_connected": true
}
```

#### GET `/health`
Get current vital signs
```json
{
  "HeartRate": 72,
  "SpO2": 98
}
```

#### GET `/status`
Get full status with predictions
```json
{
  "HeartRate": 72,
  "SpO2": 98,
  "anomaly": false,
  "arrhythmia": 0,
  "bradycardia": 0,
  "tachycardia": 0,
  "status": "Normal",
  "recommendation": "All vitals are within normal range..."
}
```

---

## 🤖 Machine Learning Models

### Model 1: Anomaly Detection
- **Algorithm**: Isolation Forest
- **Input**: `[HeartRate, SpO2]`
- **Output**: `-1` (anomaly) or `1` (normal)
- **Purpose**: Detect unusual patterns

### Model 2: Arrhythmia Detection
- **Algorithm**: Classification (Random Forest/SVM)
- **Input**: `[HeartRate, SpO2]`
- **Output**: `0` (normal) or `1` (detected)
- **Purpose**: Detect irregular heart rhythm

### Model 3: Bradycardia Detection
- **Algorithm**: Classification
- **Input**: `[HeartRate, SpO2]`
- **Output**: `0` (normal) or `1` (detected)
- **Purpose**: Detect slow heart rate (<60 BPM)

### Model 4: Tachycardia Detection
- **Algorithm**: Classification
- **Input**: `[HeartRate, SpO2]`
- **Output**: `0` (normal) or `1` (detected)
- **Purpose**: Detect fast heart rate (>100 BPM)

### Training Your Own Models
See [MODEL_INTEGRATION.md](docs/MODEL_INTEGRATION.md) for detailed instructions.

---

## 📡 Communication Protocols

### MQTT (Message Queue Telemetry Transport)
- **Purpose**: IoT device communication
- **Broker**: HiveMQ Cloud
- **Port**: 8883 (TLS encrypted)
- **Topics**: 
  - `iot/health/heartrate` - Heart rate data
  - `iot/health/spo2` - Blood oxygen data
- **QoS**: 1 (at least once delivery)

### OPC UA (Unified Architecture)
- **Purpose**: Industrial automation
- **Server**: Prosys OPC UA Simulation Server
- **Port**: 53530
- **Namespace**: HealthMonitoring
- **Security**: Configurable (None for testing)

### HTTP/HTTPS
- **Purpose**: Web communication
- **Frontend ↔ Firebase**: Real-time WebSocket
- **Dashboard**: REST API calls

---

## 📸 Screenshots

### Dashboard View
![Dashboard](screenshots/dashboard.png)
*Real-time monitoring with ML predictions*

### Historical Logs
![Logs](screenshots/logs.png)
*Complete data history with export functionality*

### OPC UA Monitoring
![OPC UA](screenshots/opcua.png)
*Industrial monitoring with UA Expert*

---

## 🐛 Troubleshooting

### Models Not Loading
```
Error: Models not found
Solution: Ensure all 4 .joblib files are in backend/models/ folder
```

### MQTT Connection Failed
```
Error: Connection failed with code X
Solution: 
1. Check HiveMQ credentials in .env
2. Verify cluster is running
3. Check port 8883 is not blocked
```

### OPC UA Connection Failed
```
Error: OPC UA connection failed
Solution:
1. Ensure Prosys server is running
2. Check server URL is correct
3. Set security to "None" and "Anonymous"
4. Run find_node_ids.py to verify connection
```

### Firebase Not Updating
```
Error: Permission denied
Solution:
1. Check Firebase Realtime Database rules
2. Verify firebase-credentials.json is valid
3. Ensure databaseURL is correct
```

### Dashboard Not Updating
```
Issue: No real-time updates
Solution:
1. Check browser console for errors
2. Verify Firebase connection
3. Ensure backend is writing to Firebase
4. Check network tab for WebSocket connection
```

For more troubleshooting, see [SETUP_GUIDE.md](docs/SETUP_GUIDE.md)

---

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
python test_models.py
```

### Test MQTT Connection
```bash
python mqtt_publisher.py
# Should show: ✅ Connected to HiveMQ Cloud
```

### Test OPC UA Connection
```bash
python find_node_ids.py
# Should list all node IDs
```

### Test Frontend
```bash
cd frontend
npm test
```

---

## 📚 Documentation

Full documentation available in the `docs/` folder:

- **[SETUP_GUIDE.md](docs/SETUP_GUIDE.md)** - Complete installation guide
- **[MODEL_INTEGRATION.md](docs/MODEL_INTEGRATION.md)** - ML model integration
- **[OPCUA_SETUP.md](docs/OPCUA_SETUP.md)** - OPC UA server configuration
- **[COMPLETE_DOCUMENTATION.md](docs/COMPLETE_DOCUMENTATION.md)** - Full technical documentation

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Contribution Guidelines
- Follow existing code style
- Add comments for complex logic
- Update documentation for new features
- Test thoroughly before submitting

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

---

## 🙏 Acknowledgments

- **HiveMQ** - For providing excellent MQTT cloud broker
- **Firebase** - For real-time database services
- **Prosys OPC UA** - For OPC UA simulation server
- **Scikit-learn** - For machine learning libraries
- **React & Recharts** - For beautiful UI components

---

## 🌟 Star History

If you find this project useful, please consider giving it a star ⭐!

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/iot-health-monitoring&type=Date)](https://star-history.com/#yourusername/iot-health-monitoring&Date)

---

## 📊 Project Status

- ✅ Core features complete
- ✅ Documentation complete
- 🔄 Testing in progress
- 📋 Future enhancements planned

### Roadmap
- [ ] Add more ML models
- [ ] Support for real IoT sensors
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Multi-patient support
- [ ] Alerts via SMS/Email
- [ ] Integration with EHR systems

---

<div align="center">

**Built with ❤️ for Healthcare IoT**

[⬆ Back to Top](#-iot-health-monitoring-system)

</div>

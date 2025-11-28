import { useState, useEffect } from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AlertTriangle, Heart, Activity, Droplets, Clock, User, Download, Shield, Moon, Bell } from 'lucide-react';

// Firebase imports
import { initializeApp } from 'firebase/app';
import { getDatabase, ref, onValue, get, query, orderByKey, limitToLast, onChildAdded } from 'firebase/database';

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyAW18uoDRVqwBlHbINXB_-MW5G8xYFNRsw",
  authDomain: "iot-project-27.firebaseapp.com",
  databaseURL: "https://iot-project-27-default-rtdb.firebaseio.com",
  projectId: "iot-project-27",
  storageBucket: "iot-project-27.firebasestorage.app",
  messagingSenderId: "386019149130",
  appId: "1:386019149130:web:ae34ded7ddab55a5db6db3",
  measurementId: "G-T470J2MD26"
};

export default function Dashboard() {
  const [firebaseApp, setFirebaseApp] = useState(null);
  const [database, setDatabase] = useState(null);
  const [currentData, setCurrentData] = useState({
    HeartRate: 72,
    SpO2: 98,
    anomaly: false,
    arrhythmia: 0,
    bradycardia: 0,
    tachycardia: 0,
    prediction: "Normal",
    recommendation: "All vitals are within normal range.",
    timestamp: Date.now()
  });
  const [historicalData, setHistoricalData] = useState([]);
  const [view, setView] = useState('dashboard');
  const [chartData, setChartData] = useState([]);
  const [darkMode, setDarkMode] = useState(true);
  const [notificationCount, setNotificationCount] = useState(0);
  const [logsRange, setLogsRange] = useState({ start: null, end: null });

  // Initialize Firebase
  useEffect(() => {
    try {
      const app = initializeApp(firebaseConfig);
      setFirebaseApp(app);
      const db = getDatabase(app);
      setDatabase(db);
    } catch (error) {
      console.error("Error initializing Firebase:", error);
    }
  }, []);

  // Subscribe to real-time data
  useEffect(() => {
      if (!database) return;
      const realtimeRef = ref(database, 'realtime_data');
      const unsubRealtime = onValue(realtimeRef, (snap) => {
        const data = snap.val();
        if (data) handleRealtimeData(data);
      });
  
      initLogsListener();
  
      return () => {
        unsubRealtime();
      };
    }, [database]);
  
    const initLogsListener = async () => {
      if (!database) return;
      try {
        const logsQuery = query(ref(database, 'logs'), orderByKey(), limitToLast(100));
        const snap = await get(logsQuery);
        let base = [];
        if (snap.exists()) {
          const data = snap.val();
          base = Object.keys(data).map(key => {
            const entry = data[key] || {};
            const ts = entry.timestamp || entry.server_timestamp || entry.sensor_timestamp || null;
            const numeric = ts ? new Date(ts).getTime() : Date.now();
            return {
              id: key,
              rawTimestamp: ts,
              serverTimestamp: entry.server_timestamp || null,
              timestamp: numeric,
              HeartRate: entry.HeartRate,
              SpO2: entry.SpO2,
              anomaly: entry.anomaly,
              arrhythmia: entry.arrhythmia,
              bradycardia: entry.bradycardia,
              tachycardia: entry.tachycardia,
              prediction: entry.prediction,
              recommendation: entry.recommendation,
              scenario: entry.scenario || ''
            };
          });
          base.sort((a,b) => a.timestamp - b.timestamp);
        }
        setHistoricalData(base);
        updateLogsRange(base);
  
        const logsRef = query(ref(database, 'logs'), orderByKey());
        onChildAdded(logsRef, (snapItem) => {
          const key = snapItem.key;
          const entry = snapItem.val() || {};
          setHistoricalData(prev => {
            if (prev.some(r => r.id === key)) return prev;
            const ts = entry.timestamp || entry.server_timestamp || entry.sensor_timestamp || null;
            const numeric = ts ? new Date(ts).getTime() : Date.now();
            const newEntry = {
              id: key,
              rawTimestamp: ts,
              serverTimestamp: entry.server_timestamp || null,
              timestamp: numeric,
              HeartRate: entry.HeartRate,
              SpO2: entry.SpO2,
              anomaly: entry.anomaly,
              arrhythmia: entry.arrhythmia,
              bradycardia: entry.bradycardia,
              tachycardia: entry.tachycardia,
              prediction: entry.prediction,
              recommendation: entry.recommendation,
              scenario: entry.scenario || ''
            };
            const merged = [...prev, newEntry];
            const sliceStart = Math.max(0, merged.length - 100);
            const trimmed = merged.slice(sliceStart);
            updateLogsRange(trimmed);
            return trimmed;
          });
        });
      } catch (e) {
        console.error("initLogsListener failed", e);
      }
    };
  
    const updateLogsRange = (arr) => {
      if (!arr || arr.length === 0) {
        setLogsRange({ start: null, end: null });
        return;
      }
      setLogsRange({ start: new Date(arr[0].timestamp), end: new Date(arr[arr.length-1].timestamp) });
    };
  
    const handleRealtimeData = (data) => {
      const newData = {
        HeartRate: data.HeartRate || 72,
        SpO2: data.SpO2 || 98,
        anomaly: data.anomaly || false,
        arrhythmia: data.arrhythmia || 0,
        bradycardia: data.bradycardia || 0,
        tachycardia: data.tachycardia || 0,
        prediction: data.prediction || "Normal",
        recommendation: data.recommendation || "All vitals are within normal range.",
        timestamp: data.timestamp || new Date().toISOString()
      };
      setCurrentData(newData);
  
      setChartData(prev => {
        const nd = [...prev, {
          time: new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'}),
          HeartRate: newData.HeartRate,
          SpO2: newData.SpO2
        }];
        if (nd.length > 20) return nd.slice(nd.length-20);
        return nd;
      });
  
      if (newData.anomaly || newData.arrhythmia || newData.bradycardia || newData.tachycardia) {
        setNotificationCount(n => n + 1);
      }
    };
  
    const downloadCSV = () => {
      if (historicalData.length === 0) return;
      const headers = ['Timestamp','Heart Rate','SpO2','Anomaly','Arrhythmia','Bradycardia','Tachycardia','Scenario','Prediction','Recommendation'];
      const rows = historicalData.map(log => [
        log.rawTimestamp ? new Date(log.rawTimestamp).toISOString() : (log.serverTimestamp ? new Date(log.serverTimestamp).toISOString() : ''),
        log.HeartRate,
        log.SpO2,
        log.anomaly ? 'Yes' : 'No',
        log.arrhythmia,
        log.bradycardia,
        log.tachycardia,
        log.scenario || '',
        log.prediction || '',
        `"${(log.recommendation || '').replace(/"/g,'""')}"`
      ]);
      const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `health_logs_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    };

  // Get status color
  const getStatusColor = (value, type) => {
    if (type === 'heart') {
      if (value < 60 || value > 100) return "text-red-500";
      else if (value < 65 || value > 95) return "text-yellow-500";
      return "text-emerald-500";
    } else if (type === 'spo2') {
      if (value < 90) return "text-red-500";
      else if (value < 95) return "text-yellow-500";
      return "text-emerald-500";
    }
    return "text-emerald-500";
  };

  // Get prediction badge color
  const getPredictionColor = (prediction) => {
    if (!prediction) return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
    if (prediction.toLowerCase().includes('anomaly') || prediction.toLowerCase().includes('detected') || prediction.toLowerCase().includes('tachy') || prediction.toLowerCase().includes('brady')) {
      return "bg-red-500/20 text-red-400 border-red-500/30";
    }
    return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
  };

  // helper to format range text
  const formatRange = () => {
    if (!logsRange.start || !logsRange.end) return '-';
    return `${logsRange.start.toLocaleString()}  —  ${logsRange.end.toLocaleString()}`;
  };

  return (
    <div className={`min-h-screen ${darkMode ? 'bg-gradient-to-br from-slate-900 to-gray-900' : 'bg-gradient-to-br from-blue-50 to-indigo-50'} transition-all duration-300`}>
      {/* Header */}
      <header className="bg-gradient-to-r from-violet-600 to-indigo-700 py-4 px-6 shadow-xl">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold flex items-center">
            <Activity className="mr-2 text-emerald-300" size={28} /> 
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-white to-emerald-300">
              IoT Health Monitoring System
            </span>
          </h1>
          <div className="flex items-center space-x-4">
            <button onClick={() => setDarkMode(!darkMode)} className="p-2 rounded-full hover:bg-white/10 transition-all">
              <Moon size={20} className="text-white" />
            </button>
            <div className="relative">
              <button className="p-2 rounded-full hover:bg-white/10 transition-all">
                <Bell size={20} className="text-white" />
                {notificationCount > 0 && (
                  <span className="absolute top-0 right-0 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                    {notificationCount}
                  </span>
                )}
              </button>
            </div>
            <nav className="flex space-x-2">
              <button 
                className={`px-4 py-2 rounded-lg transition-all ${view === 'dashboard' ? 'bg-white/20 text-white shadow-lg' : 'hover:bg-white/10 text-white/80'}`}
                onClick={() => setView('dashboard')}
              >
                Dashboard
              </button>
              <button 
                className={`px-4 py-2 rounded-lg transition-all ${view === 'logs' ? 'bg-white/20 text-white shadow-lg' : 'hover:bg-white/10 text-white/80'}`}
                onClick={() => setView('logs')}
              >
                Logs
              </button>
            </nav>
          </div>
        </div>
      </header>

      <main className="container mx-auto p-6">
        {view === 'dashboard' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Patient Info */}
            <div className="col-span-12 bg-gradient-to-r from-indigo-600/10 to-purple-600/10 rounded-xl shadow-xl overflow-hidden border border-indigo-700/30 p-6 flex items-center justify-between">
              <div className="flex items-center">
                <div className="h-14 w-14 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center shadow-lg">
                  <User className="text-white" size={28} />
                </div>
                <div className="ml-4">
                  <h2 className={`font-bold text-xl ${darkMode ? 'text-white' : 'text-gray-800'}`}>Patient: John Doe</h2>
                  <p className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    Age: 65 • ID: IOT-2025-001 • Last Check: {new Date(currentData.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
              <div className={`px-3 py-1 rounded-full ${getPredictionColor(currentData.prediction)} text-sm font-medium border`}>
                {currentData.prediction}
              </div>
            </div>

            {/* Vitals Cards */}
            <div className="col-span-12 grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Heart Rate */}
              <div className={`${darkMode ? 'bg-gradient-to-br from-gray-800 to-gray-900' : 'bg-white'} rounded-xl shadow-xl overflow-hidden border ${darkMode ? 'border-gray-700' : 'border-gray-200'} p-6 hover:scale-105 transition-all duration-300`}>
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center">
                    <div className="p-2 bg-red-500/20 rounded-lg mr-3">
                      <Heart className="text-red-500" size={24} />
                    </div>
                    <h2 className={`text-lg font-medium ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>Heart Rate</h2>
                  </div>
                </div>
                <div className="flex items-baseline mt-6">
                  <h3 className={`text-4xl font-bold ${getStatusColor(currentData.HeartRate, 'heart')}`}>
                    {currentData.HeartRate}
                  </h3>
                  <span className={`ml-2 text-lg ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>BPM</span>
                </div>
                <p className={`text-xs mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Normal: 60-100 BPM</p>
              </div>

              {/* SpO2 */}
              <div className={`${darkMode ? 'bg-gradient-to-br from-gray-800 to-gray-900' : 'bg-white'} rounded-xl shadow-xl overflow-hidden border ${darkMode ? 'border-gray-700' : 'border-gray-200'} p-6 hover:scale-105 transition-all duration-300`}>
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center">
                    <div className="p-2 bg-blue-500/20 rounded-lg mr-3">
                      <Droplets className="text-blue-500" size={24} />
                    </div>
                    <h2 className={`text-lg font-medium ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>Blood Oxygen</h2>
                  </div>
                </div>
                <div className="flex items-baseline mt-6">
                  <h3 className={`text-4xl font-bold ${getStatusColor(currentData.SpO2, 'spo2')}`}>
                    {currentData.SpO2}
                  </h3>
                  <span className={`ml-2 text-lg ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>%</span>
                </div>
                <p className={`text-xs mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Normal: 95-100%</p>
              </div>

              {/* Predicted (new) */}
              <div className={`${darkMode ? 'bg-gradient-to-br from-gray-800 to-gray-900' : 'bg-white'} rounded-xl shadow-xl overflow-hidden border ${darkMode ? 'border-gray-700' : 'border-gray-200'} p-6 hover:scale-105 transition-all duration-300`}>
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center">
                    <div className="p-2 bg-indigo-500/20 rounded-lg mr-3">
                      <Shield className="text-indigo-500" size={24} />
                    </div>
                    <h2 className={`text-lg font-medium ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>Predicted</h2>
                  </div>
                </div>
                <div className="mt-6">
                  <div className={`px-3 py-2 rounded-md ${getPredictionColor(currentData.prediction)} font-semibold inline-block`}>
                    {currentData.prediction}
                  </div>
                </div>
                <p className={`text-xs mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Latest model prediction</p>
              </div>
            </div>

            {/* ML Predictions (existing grid) */}
            <div className="col-span-12 grid grid-cols-1 md:grid-cols-4 gap-6">
              {/* Anomaly */}
              <div className={`${darkMode ? 'bg-gradient-to-br from-gray-800 to-gray-900' : 'bg-white'} rounded-xl shadow-xl p-6 border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                <div className="flex items-center justify-between mb-2">
                  <AlertTriangle className={currentData.anomaly ? "text-red-500" : "text-emerald-500"} size={24} />
                  <span className={`text-xs px-2 py-1 rounded-full ${currentData.anomaly ? 'bg-red-500/20 text-red-500' : 'bg-emerald-500/20 text-emerald-500'}`}>
                    {currentData.anomaly ? 'Detected' : 'Normal'}
                  </span>
                </div>
                <h3 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-800'}`}>Anomaly</h3>
                <p className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Pattern detection</p>
              </div>

              {/* Arrhythmia */}
              <div className={`${darkMode ? 'bg-gradient-to-br from-gray-800 to-gray-900' : 'bg-white'} rounded-xl shadow-xl p-6 border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                <div className="flex items-center justify-between mb-2">
                  <Activity className={currentData.arrhythmia ? "text-red-500" : "text-emerald-500"} size={24} />
                  <span className={`text-xs px-2 py-1 rounded-full ${currentData.arrhythmia ? 'bg-red-500/20 text-red-500' : 'bg-emerald-500/20 text-emerald-500'}`}>
                    {currentData.arrhythmia ? 'Detected' : 'Normal'}
                  </span>
                </div>
                <h3 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-800'}`}>Arrhythmia</h3>
                <p className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Heart rhythm</p>
              </div>

              {/* Bradycardia */}
              <div className={`${darkMode ? 'bg-gradient-to-br from-gray-800 to-gray-900' : 'bg-white'} rounded-xl shadow-xl p-6 border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                <div className="flex items-center justify-between mb-2">
                  <Heart className={currentData.bradycardia ? "text-yellow-500" : "text-emerald-500"} size={24} />
                  <span className={`text-xs px-2 py-1 rounded-full ${currentData.bradycardia ? 'bg-yellow-500/20 text-yellow-500' : 'bg-emerald-500/20 text-emerald-500'}`}>
                    {currentData.bradycardia ? 'Detected' : 'Normal'}
                  </span>
                </div>
                <h3 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-800'}`}>Bradycardia</h3>
                <p className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Low heart rate</p>
              </div>

              {/* Tachycardia */}
              <div className={`${darkMode ? 'bg-gradient-to-br from-gray-800 to-gray-900' : 'bg-white'} rounded-xl shadow-xl p-6 border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                <div className="flex items-center justify-between mb-2">
                  <Heart className={currentData.tachycardia ? "text-orange-500" : "text-emerald-500"} size={24} />
                  <span className={`text-xs px-2 py-1 rounded-full ${currentData.tachycardia ? 'bg-orange-500/20 text-orange-500' : 'bg-emerald-500/20 text-emerald-500'}`}>
                    {currentData.tachycardia ? 'Detected' : 'Normal'}
                  </span>
                </div>
                <h3 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-800'}`}>Tachycardia</h3>
                <p className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>High heart rate</p>
              </div>
            </div>

            {/* Recommendation */}
            <div className="col-span-12">
              <div className={`${darkMode ? 'bg-gradient-to-br from-gray-800 to-gray-900' : 'bg-white'} rounded-xl shadow-xl p-6 border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                <h2 className={`text-xl font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-800'} flex items-center`}>
                  <Shield className="mr-2 text-indigo-500" size={24} />
                  Health Recommendation
                </h2>
                <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700/50' : 'bg-gray-100'}`}>
                  <p className={`${darkMode ? 'text-gray-200' : 'text-gray-700'} leading-relaxed`}>
                    {currentData.recommendation}
                  </p>
                </div>
              </div>
            </div>

            {/* Chart */}
            <div className="col-span-12">
              <div className={`${darkMode ? 'bg-gradient-to-br from-gray-800 to-gray-900' : 'bg-white'} rounded-xl shadow-xl p-6 border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                <h2 className={`text-xl font-semibold mb-6 ${darkMode ? 'text-white' : 'text-gray-800'}`}>
                  Real-Time Monitoring
                </h2>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#374151' : '#e5e7eb'} />
                      <XAxis dataKey="time" stroke={darkMode ? '#9ca3af' : '#6b7280'} />
                      <YAxis yAxisId="left" stroke={darkMode ? '#9ca3af' : '#6b7280'} domain={[40, 150]} />
                      <YAxis yAxisId="right" orientation="right" stroke={darkMode ? '#9ca3af' : '#6b7280'} domain={[85, 100]} />
                      <Tooltip contentStyle={{ backgroundColor: darkMode ? '#1f2937' : '#ffffff', borderColor: darkMode ? '#4b5563' : '#e5e7eb' }} />
                      <Legend />
                      <Line yAxisId="left" type="monotone" dataKey="HeartRate" stroke="#ef4444" strokeWidth={2} />
                      <Line yAxisId="right" type="monotone" dataKey="SpO2" stroke="#3b82f6" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        )}

        {view === 'logs' && (
          <div className="grid grid-cols-1 gap-6">
            <div className={`${darkMode ? 'bg-gradient-to-br from-gray-800 to-gray-900' : 'bg-white'} rounded-xl shadow-xl p-6 border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className={`text-xl font-semibold ${darkMode ? 'text-white' : 'text-gray-800'}`}>Health Data Logs</h2>
                  <p className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Showing {historicalData.length} records • Range: {formatRange()}</p>
                </div>
                <button onClick={downloadCSV} className="flex items-center px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white transition-all">
                  <Download size={18} className="mr-2" /> Download CSV
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-700">
                  <thead className={darkMode ? 'bg-gray-700/30' : 'bg-gray-50'}>
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Timestamp</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Scenario</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">HR</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">SpO2</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Anomaly</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Arrhythmia</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Brady</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Tachy</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Prediction</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Recommendation</th>
                    </tr>
                  </thead>
                  <tbody className={darkMode ? 'divide-y divide-gray-700' : 'divide-y divide-gray-200'}>
                    {historicalData.map((log, index) => (
                      <tr key={log.id || index} className={index % 2 === 0 ? (darkMode ? 'bg-gray-800/30' : 'bg-white') : (darkMode ? 'bg-gray-800/60' : 'bg-gray-50')}>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${darkMode ? 'text-gray-300' : 'text-gray-900'}`}>{log.rawTimestamp ? new Date(log.rawTimestamp).toLocaleString() : (log.serverTimestamp ? new Date(log.serverTimestamp).toLocaleString() : '')}</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${darkMode ? 'text-gray-300' : 'text-gray-900'}`}>{log.scenario || '-'}</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${getStatusColor(log.HeartRate, 'heart')}`}>{log.HeartRate}</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${getStatusColor(log.SpO2, 'spo2')}`}>{log.SpO2}%</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${log.anomaly ? 'text-red-500' : 'text-emerald-500'}`}>{log.anomaly ? 'Yes' : 'No'}</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${log.arrhythmia ? 'text-red-500' : 'text-emerald-500'}`}>{log.arrhythmia ? 'Yes' : 'No'}</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${log.bradycardia ? 'text-yellow-500' : 'text-emerald-500'}`}>{log.bradycardia ? 'Yes' : 'No'}</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${log.tachycardia ? 'text-orange-500' : 'text-emerald-500'}`}>{log.tachycardia ? 'Yes' : 'No'}</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>{log.prediction}</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>{log.recommendation}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

            </div>
          </div>
        )}
      </main>

      <footer className={`py-4 px-6 ${darkMode ? 'bg-gray-900 text-gray-400' : 'bg-gray-100 text-gray-600'}`}>
        <div className="container mx-auto flex justify-between items-center">
          <p className="text-sm">© 2025 IoT Health Monitoring System</p>
          <div className="flex items-center space-x-4 text-sm">
            <a href="#" className="hover:underline">Privacy Policy</a>
            <a href="#" className="hover:underline">Terms of Service</a>
            <a href="#" className="hover:underline">Contact Support</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

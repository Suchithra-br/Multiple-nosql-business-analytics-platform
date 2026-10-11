import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header.jsx';
import Sidebar from './components/Sidebar.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Analytics from './pages/Analytics.jsx';
import { api } from './services/api.js';

export default function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [apiStatus, setApiStatus] = useState('connected');
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Periodic and on-mount health check
  const checkHealth = useCallback(async () => {
    try {
      const res = await api.getHealth();
      if (res && res.status === 'healthy') {
        setApiStatus('connected');
      } else {
        setApiStatus('degraded');
      }
    } catch {
      setApiStatus('error');
    }
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    setRefreshTrigger((prev) => prev + 1);
    await checkHealth();
    setTimeout(() => {
      setIsRefreshing(false);
    }, 500);
  };

  return (
    <div className="app-container">
      <Sidebar currentTab={currentTab} onSelectTab={setCurrentTab} />

      <div className="main-layout">
        <Header
          apiStatus={apiStatus}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
        />

        <main className="content-area">
          {currentTab === 'dashboard' && <Dashboard refreshTrigger={refreshTrigger} />}
          {currentTab === 'analytics' && <Analytics />}
        </main>
      </div>
    </div>
  );
}

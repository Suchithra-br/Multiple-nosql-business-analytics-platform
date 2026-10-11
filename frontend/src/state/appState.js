import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { api } from '../services/api.js';

/**
 * Centralized Application State & Context.
 * Provides lightweight global state for tab navigation, API connectivity,
 * global refresh triggers, and active dashboard filter presets without
 * adding heavy state management dependencies.
 */

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [apiStatus, setApiStatus] = useState('connected');
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Global filters that can be shared between views if needed
  const [selectedYear, setSelectedYear] = useState('all');
  const [selectedRegion, setSelectedRegion] = useState('all');

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

  const triggerRefresh = useCallback(async () => {
    setIsRefreshing(true);
    setRefreshTrigger((prev) => prev + 1);
    await checkHealth();
    setTimeout(() => {
      setIsRefreshing(false);
    }, 500);
  }, [checkHealth]);

  const value = {
    currentTab,
    setCurrentTab,
    apiStatus,
    setApiStatus,
    refreshTrigger,
    isRefreshing,
    triggerRefresh,
    selectedYear,
    setSelectedYear,
    selectedRegion,
    setSelectedRegion,
    checkHealth,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppState() {
  const context = useContext(AppContext);
  if (!context) {
    // If used outside provider, return default standalone state handlers
    return {
      currentTab: 'dashboard',
      apiStatus: 'connected',
      refreshTrigger: 0,
      isRefreshing: false,
      selectedYear: 'all',
      selectedRegion: 'all',
    };
  }
  return context;
}

export default AppContext;

import React, { createContext, useState, useEffect, useContext } from 'react';
import * as SecureStore from 'expo-secure-store';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = await SecureStore.getItemAsync('access_token');
      if (token) {
        const res = await authAPI.getProfile();
        if (res.data.role === 'tenant') {
          setUser(res.data);
        } else {
          await SecureStore.deleteItemAsync('access_token');
          await SecureStore.deleteItemAsync('refresh_token');
        }
      }
    } catch (e) {
      console.warn('Auth check failed:', e.message);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const res = await authAPI.login(username, password);
      if (res.data.user.role !== 'tenant') {
        throw new Error('Access denied. Tenant accounts only.');
      }
      await SecureStore.setItemAsync('access_token', res.data.access);
      await SecureStore.setItemAsync('refresh_token', res.data.refresh);
      setUser(res.data.user);
      return res.data;
    } catch (e) {
      if (e.response?.data?.error) {
        throw new Error(e.response.data.error);
      }
      if (e.message === 'Network Error') {
        throw new Error('Cannot connect to server. Check your internet connection.');
      }
      throw e;
    }
  };

  const logout = async () => {
    await SecureStore.deleteItemAsync('access_token');
    await SecureStore.deleteItemAsync('refresh_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

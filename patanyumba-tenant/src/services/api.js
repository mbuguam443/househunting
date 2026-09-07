import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

const API_BASE = 'https://patanyumba.greatjourns.com/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = await SecureStore.getItemAsync('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE}/auth/refresh/`, {
            refresh: refreshToken,
          });
          await SecureStore.setItemAsync('access_token', res.data.access);
          if (res.data.refresh) {
            await SecureStore.setItemAsync('refresh_token', res.data.refresh);
          }
          originalRequest.headers.Authorization = `Bearer ${res.data.access}`;
          return api(originalRequest);
        } catch (refreshError) {
          await SecureStore.deleteItemAsync('access_token');
          await SecureStore.deleteItemAsync('refresh_token');
        }
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username, password) => api.post('/auth/login/', { username, password }),
  refresh: (refresh) => api.post('/auth/refresh/', { refresh }),
  getProfile: () => api.get('/auth/profile/'),
};

export const tenantAPI = {
  getDashboard: () => api.get('/tenant/dashboard/'),
  getPayments: (page = 1) => api.get(`/tenant/payments/?page=${page}`),
  getPayInfo: () => api.get('/tenant/pay/'),
  submitMaintenance: (data) => api.post('/tenant/maintenance/', data),
  getMaintenance: () => api.get('/tenant/maintenance/'),
  getLease: () => api.get('/tenant/lease/'),
  getUtilities: () => api.get('/tenant/utilities/'),
  initiateStk: (data) => api.post('/tenant/pay/stk/', data),
  checkStkStatus: (paymentId) => api.get(`/tenant/pay/status/?payment_id=${paymentId}`),
};

export default api;

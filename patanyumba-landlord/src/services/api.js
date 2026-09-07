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
  getProfile: () => api.get('/auth/profile/'),
};

export const landlordAPI = {
  getDashboard: () => api.get('/landlord/dashboard/'),
  updateProfile: (data) => api.patch('/landlord/profile/', data),

  getProperties: () => api.get('/landlord/properties/'),
  getProperty: (id) => api.get(`/landlord/properties/${id}/`),
  createProperty: (data) => api.post('/landlord/properties/', data),
  updateProperty: (id, data) => api.put(`/landlord/properties/${id}/`, data),
  deleteProperty: (id) => api.delete(`/landlord/properties/${id}/`),

  getUnits: (property = '') => api.get(`/landlord/units/?property=${property}`),
  getUnit: (id) => api.get(`/landlord/units/${id}/`),
  createUnit: (data) => api.post('/landlord/units/', data),
  updateUnit: (id, data) => api.put(`/landlord/units/${id}/`, data),
  deleteUnit: (id) => api.delete(`/landlord/units/${id}/`),

  getTenants: (search = '') => api.get(`/landlord/tenants/?search=${search}`),
  getTenancies: (status = '', property = '') =>
    api.get(`/landlord/tenancies/?status=${status}&property=${property}`),
  getTenancy: (id) => api.get(`/landlord/tenancies/${id}/`),
  createTenancy: (data) => api.post('/landlord/tenancies/create/', data),
  endTenancy: (id) => api.post(`/landlord/tenancies/${id}/end/`),

  getPayments: (status = '') => api.get(`/landlord/payments/?status=${status}`),
  initiateStk: (paymentId, data) =>
    api.post(`/landlord/payments/${paymentId}/stk/`, data),

  getUtilities: (status = '') => api.get(`/landlord/utilities/?status=${status}`),

  getMaintenance: (status = '') => api.get(`/landlord/maintenance/?status=${status}`),
  updateMaintenance: (id, data) => api.patch(`/landlord/maintenance/${id}/`, data),

  getHouseTypes: () => api.get('/house-types/'),
};

export default api;

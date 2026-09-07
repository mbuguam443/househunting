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

export const adminAPI = {
  getDashboard: () => api.get('/admin/dashboard/'),
  getLandlords: (search = '') => api.get(`/admin/landlords/?search=${search}`),
  getLandlord: (id) => api.get(`/admin/landlords/${id}/`),
  createLandlord: (data) => api.post('/admin/landlords/create/', data),
  assignSubscription: (landlordId, data) => api.post(`/admin/landlords/${landlordId}/subscription/`, data),
  setLandlordFee: (landlordId, data) => api.put(`/admin/landlords/${landlordId}/fee/`, data),
  setLandlordMpesa: (landlordId, data) => api.put(`/admin/landlords/${landlordId}/mpesa/`, data),
  getPlans: () => api.get('/admin/plans/'),
  createPlan: (data) => api.post('/admin/plans/', data),
  togglePlan: (id) => api.post(`/admin/plans/${id}/toggle/`),
  getRevenue: (status = '') => api.get(`/admin/revenue/?status=${status}`),
  updateFee: (data) => api.put('/admin/update-fee/', data),
  getListings: (search = '', status = '') =>
    api.get(`/admin/listings/?search=${search}&status=${status}`),
  getListing: (id) => api.get(`/admin/listings/${id}/`),
  createListing: (data) => api.post('/admin/listings/', data),
  updateListing: (id, data) => api.put(`/admin/listings/${id}/`, data),
  deleteListing: (id) => api.delete(`/admin/listings/${id}/`),
  getHouseTypes: () => api.get('/house-types/'),
};

export default api;

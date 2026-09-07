import React, { useState } from 'react';
import {
  View, Text, ScrollView, Alert, TouchableOpacity, ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { landlordAPI } from '../services/api';
import { ScreenHeader, Field } from '../components/UI';
import { useAuth } from '../contexts/AuthContext';

export default function ProfileScreen() {
  const { user, logout } = useAuth();
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    phone: user?.phone || '',
    mpesa_consumer_key: '',
    mpesa_consumer_secret: '',
    mpesa_passkey: '',
    mpesa_shortcode: '',
    c2b_shortcode: '',
    mpesa_callback_url: '',
  });

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {};
      Object.keys(form).forEach((k) => {
        if (form[k]) payload[k] = form[k];
      });
      await landlordAPI.updateProfile(payload);
      Alert.alert('Success', 'Profile and M-Pesa settings saved');
    } catch (e) {
      Alert.alert('Error', 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to logout?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Logout', style: 'destructive', onPress: logout },
    ]);
  };

  return (
    <ScrollView style={styles.container}>
      <ScreenHeader
        title="Profile"
        right={
          <TouchableOpacity onPress={handleLogout}>
            <Ionicons name="log-out-outline" size={24} color="#fff" />
          </TouchableOpacity>
        }
      />

      <View style={styles.card}>
        <Text style={styles.name}>{user?.user?.full_name || user?.username}</Text>
        <Text style={styles.username}>@{user?.user?.username}</Text>
        <InfoText label="Role" value="Landlord" />
        <InfoText label="Phone" value={user?.phone || '—'} />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>M-Pesa Settings (Daraja API)</Text>
        <Field label="Consumer Key" value={form.mpesa_consumer_key} onChangeText={(v) => setForm({ ...form, mpesa_consumer_key: v })} placeholder="Your Daraja Consumer Key" />
        <Field label="Consumer Secret" value={form.mpesa_consumer_secret} onChangeText={(v) => setForm({ ...form, mpesa_consumer_secret: v })} placeholder="Your Daraja Consumer Secret" secureTextEntry />
        <Field label="Passkey" value={form.mpesa_passkey} onChangeText={(v) => setForm({ ...form, mpesa_passkey: v })} placeholder="Your M-Pesa Passkey" secureTextEntry />
        <Field label="STK Push Shortcode (Paybill)" value={form.mpesa_shortcode} onChangeText={(v) => setForm({ ...form, mpesa_shortcode: v })} placeholder="e.g. 174379" />
        <Field label="C2B Shortcode (for receiving)" value={form.c2b_shortcode} onChangeText={(v) => setForm({ ...form, c2b_shortcode: v })} placeholder="Your C2B Paybill" />
        <Field label="Callback URL" value={form.mpesa_callback_url} onChangeText={(v) => setForm({ ...form, mpesa_callback_url: v })} placeholder="https://yourdomain.com" />

        <TouchableOpacity style={[styles.saveBtn, saving && { opacity: 0.5 }]} onPress={handleSave} disabled={saving}>
          {saving ? <ActivityIndicator color="#fff" /> : <Text style={styles.saveBtnText}>Save Settings</Text>}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

function InfoText({ label, value }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16,
    margin: 12, marginBottom: 0, elevation: 2,
  },
  name: { fontSize: 20, fontWeight: 'bold', color: '#333' },
  username: { fontSize: 14, color: '#888', marginTop: 2, marginBottom: 12 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 12, color: '#333' },
  infoRow: {
    flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6,
  },
  infoLabel: { fontSize: 14, color: '#888' },
  infoValue: { fontSize: 14, fontWeight: '600', color: '#333' },
  saveBtn: {
    backgroundColor: '#E65100', borderRadius: 8, padding: 14, alignItems: 'center', marginTop: 6,
  },
  saveBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});

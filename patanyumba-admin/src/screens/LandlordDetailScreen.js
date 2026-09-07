import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, StyleSheet, Alert, TextInput, TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { adminAPI } from '../services/api';

export default function LandlordDetailScreen({ route, navigation }) {
  const { id } = route.params;
  const [landlord, setLandlord] = useState(null);
  const [plans, setPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [unitCount, setUnitCount] = useState('');
  const [fee, setFee] = useState('');
  const [assigning, setAssigning] = useState(false);
  const [mpesa, setMpesa] = useState({
    mpesa_consumer_key: '',
    mpesa_consumer_secret: '',
    mpesa_passkey: '',
    mpesa_shortcode: '',
    c2b_shortcode: '',
    mpesa_callback_url: '',
  });
  const [savingMpesa, setSavingMpesa] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [landlordRes, plansRes] = await Promise.all([
        adminAPI.getLandlord(id),
        adminAPI.getPlans(),
      ]);
      setLandlord(landlordRes.data);
      setPlans(plansRes.data.results || plansRes.data);
      setFee(landlord.fee_per_unit?.toString() || '50');
    } catch (e) {
      console.error(e);
    }
  };

  const handleAssignSub = async () => {
    if (!selectedPlan || !unitCount) {
      Alert.alert('Error', 'Select a plan and enter unit count');
      return;
    }
    setAssigning(true);
    try {
      await adminAPI.assignSubscription(id, {
        plan_id: selectedPlan,
        unit_count: parseInt(unitCount),
      });
      Alert.alert('Success', 'Subscription assigned');
      await fetchData();
    } catch (e) {
      Alert.alert('Error', e.response?.data?.error || 'Failed');
    } finally {
      setAssigning(false);
    }
  };

  const handleSetFee = async () => {
    try {
      await adminAPI.setLandlordFee(id, { fee_per_unit: parseFloat(fee) });
      Alert.alert('Success', 'Fee updated');
      await fetchData();
    } catch (e) {
      Alert.alert('Error', 'Failed to update fee');
    }
  };

  const handleSaveMpesa = async () => {
    const payload = {};
    Object.keys(mpesa).forEach((k) => {
      if (mpesa[k]) payload[k] = mpesa[k];
    });
    if (Object.keys(payload).length === 0) {
      Alert.alert('Error', 'Fill at least one M-Pesa field');
      return;
    }
    setSavingMpesa(true);
    try {
      await adminAPI.setLandlordMpesa(id, payload);
      Alert.alert('Success', 'M-Pesa credentials saved');
      setMpesa({
        mpesa_consumer_key: '', mpesa_consumer_secret: '', mpesa_passkey: '',
        mpesa_shortcode: '', c2b_shortcode: '', mpesa_callback_url: '',
      });
    } catch (e) {
      Alert.alert('Error', 'Failed to save M-Pesa credentials');
    } finally {
      setSavingMpesa(false);
    }
  };

  if (!landlord) {
    return <View style={styles.center}><Text>Loading...</Text></View>;
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{landlord.user.full_name}</Text>
      </View>

      <View style={styles.card}>
        <InfoRow label="Username" value={landlord.user.username} />
        <InfoRow label="Phone" value={landlord.phone || 'N/A'} />
        <InfoRow label="Properties" value={landlord.properties_count.toString()} />
        <InfoRow label="Units" value={landlord.units_count.toString()} />
        <InfoRow label="Tenants" value={landlord.tenants_count.toString()} />
        <InfoRow label="Sub Status" value={landlord.subscription_status.status} />
        {landlord.subscription_status.plan && (
          <InfoRow label="Plan" value={landlord.subscription_status.plan} />
        )}
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Set Per-Unit Fee (KES)</Text>
        <View style={styles.row}>
          <TextInput
            style={[styles.input, { flex: 1 }]}
            value={fee}
            onChangeText={setFee}
            keyboardType="numeric"
            placeholder="50"
          />
          <TouchableOpacity style={styles.smallBtn} onPress={handleSetFee}>
            <Text style={styles.smallBtnText}>Update</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>M-Pesa Settings (Daraja)</Text>
        <TextInput style={styles.input} placeholder="Consumer Key" placeholderTextColor="#999" value={mpesa.mpesa_consumer_key} onChangeText={(v) => setMpesa({ ...mpesa, mpesa_consumer_key: v })} />
        <TextInput style={styles.input} placeholder="Consumer Secret" placeholderTextColor="#999" value={mpesa.mpesa_consumer_secret} onChangeText={(v) => setMpesa({ ...mpesa, mpesa_consumer_secret: v })} secureTextEntry />
        <TextInput style={styles.input} placeholder="Passkey" placeholderTextColor="#999" value={mpesa.mpesa_passkey} onChangeText={(v) => setMpesa({ ...mpesa, mpesa_passkey: v })} secureTextEntry />
        <TextInput style={styles.input} placeholder="STK Shortcode (e.g. 174379)" placeholderTextColor="#999" value={mpesa.mpesa_shortcode} onChangeText={(v) => setMpesa({ ...mpesa, mpesa_shortcode: v })} />
        <TextInput style={styles.input} placeholder="C2B Shortcode" placeholderTextColor="#999" value={mpesa.c2b_shortcode} onChangeText={(v) => setMpesa({ ...mpesa, c2b_shortcode: v })} />
        <TextInput style={styles.input} placeholder="Callback URL" placeholderTextColor="#999" value={mpesa.mpesa_callback_url} onChangeText={(v) => setMpesa({ ...mpesa, mpesa_callback_url: v })} />
        <TouchableOpacity
          style={[styles.assignBtn, savingMpesa && { opacity: 0.5 }]}
          onPress={handleSaveMpesa}
          disabled={savingMpesa}
        >
          <Text style={styles.assignBtnText}>{savingMpesa ? 'Saving...' : 'Save M-Pesa Credentials'}</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Assign Subscription</Text>
        {plans.filter((p) => p.is_active).map((plan) => (
          <TouchableOpacity
            key={plan.id}
            style={[styles.planItem, selectedPlan === plan.id && styles.planActive]}
            onPress={() => setSelectedPlan(plan.id)}
          >
            <Text style={styles.planName}>{plan.name}</Text>
            <Text style={styles.planDetail}>KES {plan.amount} | {plan.duration_days} days</Text>
          </TouchableOpacity>
        ))}
        <TextInput
          style={styles.input}
          placeholder="Unit count"
          value={unitCount}
          onChangeText={setUnitCount}
          keyboardType="numeric"
        />
        <TouchableOpacity
          style={[styles.assignBtn, assigning && { opacity: 0.5 }]}
          onPress={handleAssignSub}
          disabled={assigning}
        >
          <Text style={styles.assignBtnText}>
            {assigning ? 'Assigning...' : 'Assign Subscription'}
          </Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

function InfoRow({ label, value }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: {
    backgroundColor: '#0D47A1', padding: 20, paddingTop: 16,
    flexDirection: 'row', alignItems: 'center',
  },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#fff', marginLeft: 16 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16,
    margin: 12, marginBottom: 0, elevation: 2,
  },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 12, color: '#333' },
  infoRow: {
    flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8,
    borderBottomWidth: 1, borderBottomColor: '#F0F0F0',
  },
  infoLabel: { fontSize: 14, color: '#888' },
  infoValue: { fontSize: 14, fontWeight: '600', color: '#333' },
  row: { flexDirection: 'row', alignItems: 'center' },
  input: {
    backgroundColor: '#F5F5F5', borderRadius: 8, padding: 12,
    fontSize: 16, marginBottom: 12, color: '#333', marginHorizontal: 0,
  },
  smallBtn: {
    backgroundColor: '#0D47A1', borderRadius: 8, paddingHorizontal: 16, padding: 12,
    marginLeft: 8, marginBottom: 12,
  },
  smallBtnText: { color: '#fff', fontWeight: 'bold' },
  planItem: {
    borderWidth: 1, borderColor: '#ddd', borderRadius: 8, padding: 12,
    marginBottom: 8,
  },
  planActive: { borderColor: '#0D47A1', backgroundColor: '#E3F2FD' },
  planName: { fontSize: 14, fontWeight: 'bold', color: '#333' },
  planDetail: { fontSize: 12, color: '#888', marginTop: 2 },
  assignBtn: {
    backgroundColor: '#1B5E20', borderRadius: 8, padding: 14, alignItems: 'center',
  },
  assignBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});

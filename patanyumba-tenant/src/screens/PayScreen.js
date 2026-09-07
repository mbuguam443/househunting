import React, { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TextInput, TouchableOpacity,
  StyleSheet, Alert, ActivityIndicator, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { tenantAPI } from '../services/api';

export default function PayScreen() {
  const [data, setData] = useState(null);
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await tenantAPI.getPayInfo();
      setData(res.data);
      if (res.data.phone) setPhone(res.data.phone);
    } catch (e) {
      console.error(e);
    }
  }, []);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await tenantAPI.getPayInfo();
        if (mounted) {
          setData(res.data);
          if (res.data.phone) setPhone(res.data.phone);
        }
      } catch (e) {
        console.error(e);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const handlePay = async (paymentId, amount) => {
    if (!phone) {
      Alert.alert('Error', 'Please enter your M-Pesa phone number');
      return;
    }
    setLoading(true);
    try {
      const res = await tenantAPI.initiateStk({ amount, phone });
      const paymentIdCreated = res.data.payment_id;
      Alert.alert(
        'M-Pesa Prompt Sent',
        `Enter your M-Pesa PIN on ${phone} to complete payment of KES ${amount}.`,
        [
          {
            text: 'OK',
            onPress: () => pollStatus(paymentIdCreated, amount),
          },
        ]
      );
    } catch (e) {
      Alert.alert('Error', e.response?.data?.error || 'Failed to initiate payment');
    } finally {
      setLoading(false);
    }
  };

  const pollStatus = (paymentId, amount) => {
    let attempts = 0;
    let cleared = false;
    const timer = setInterval(async () => {
      if (cleared) { clearInterval(timer); return; }
      attempts++;
      try {
        const res = await tenantAPI.checkStkStatus(paymentId);
        const { payment_status, mpesa_status } = res.data;
        if (mpesa_status === 'completed' || payment_status === 'paid') {
          cleared = true;
          clearInterval(timer);
          Alert.alert('Success', `Payment of KES ${amount} received. Ref: ${res.data.receipt || ''}`);
          fetchData();
          return;
        }
        if (mpesa_status === 'failed' || mpesa_status === 'cancelled' || attempts >= 40) {
          cleared = true;
          clearInterval(timer);
          Alert.alert('Payment Pending/Failed', 'Please check your payment status later or retry.');
        }
      } catch (e) {
        cleared = true;
        clearInterval(timer);
      }
    }, 3000);
  };

  if (!data) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1B5E20" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Pay Rent</Text>
      </View>

      <View style={styles.balanceCard}>
        <Text style={styles.balanceLabel}>Total Outstanding</Text>
        <Text style={styles.balanceAmount}>KES {data.balance}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>M-Pesa Phone Number</Text>
        <TextInput
          style={styles.input}
          placeholder="0712345678"
          placeholderTextColor="#999"
          value={phone}
          onChangeText={setPhone}
          keyboardType="phone-pad"
        />
      </View>

      {data.pending.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Pending Invoices</Text>
          {data.pending.map((p) => (
            <View key={p.id} style={styles.invoiceRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.invoiceTitle}>Rent - {p.unit_number}</Text>
                <Text style={styles.invoiceSub}>Due: {p.due_date}</Text>
              </View>
              <Text style={styles.invoiceAmount}>KES {p.amount}</Text>
              <TouchableOpacity
                style={[styles.payBtn, loading && { opacity: 0.5 }]}
                onPress={() => handlePay(p.id, p.amount)}
                disabled={loading}
              >
                <Ionicons name="card-outline" size={16} color="#fff" />
                <Text style={styles.payBtnText}>Pay</Text>
              </TouchableOpacity>
            </View>
          ))}
        </View>
      )}

      {data.pending.length === 0 && (
        <View style={styles.emptyCard}>
          <Ionicons name="checkmark-circle-outline" size={48} color="#4CAF50" />
          <Text style={styles.emptyText}>All payments up to date!</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { backgroundColor: '#1B5E20', padding: 20, paddingTop: 16 },
  headerTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  balanceCard: {
    backgroundColor: '#D32F2F', borderRadius: 12, padding: 20,
    margin: 16, alignItems: 'center',
  },
  balanceLabel: { fontSize: 14, color: '#FFCDD2' },
  balanceAmount: { fontSize: 28, fontWeight: 'bold', color: '#fff', marginTop: 4 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16,
    marginHorizontal: 16, marginBottom: 12, elevation: 2,
  },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 12, color: '#333' },
  input: {
    backgroundColor: '#F5F5F5', borderRadius: 8, padding: 12,
    fontSize: 16, color: '#333',
  },
  invoiceRow: {
    flexDirection: 'row', alignItems: 'center', paddingVertical: 10,
    borderBottomWidth: 1, borderBottomColor: '#eee',
  },
  invoiceTitle: { fontSize: 14, fontWeight: '600', color: '#333' },
  invoiceSub: { fontSize: 12, color: '#888', marginTop: 2 },
  invoiceAmount: { fontSize: 14, fontWeight: 'bold', color: '#333', marginRight: 12 },
  payBtn: {
    flexDirection: 'row', backgroundColor: '#FF6F00', borderRadius: 8,
    paddingHorizontal: 12, paddingVertical: 8, alignItems: 'center',
  },
  payBtnText: { color: '#fff', fontSize: 13, fontWeight: 'bold', marginLeft: 4 },
  emptyCard: {
    backgroundColor: '#fff', borderRadius: 12, padding: 32,
    margin: 16, alignItems: 'center', elevation: 2,
  },
  emptyText: { fontSize: 16, color: '#4CAF50', marginTop: 12, fontWeight: '600' },
});

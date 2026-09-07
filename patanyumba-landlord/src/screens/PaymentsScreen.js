import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  RefreshControl, Alert, TextInput,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { landlordAPI } from '../services/api';
import { ScreenHeader } from '../components/UI';

const STATUS_COLORS = {
  pending: '#FF9800',
  paid: '#4CAF50',
  overdue: '#D32F2F',
  late: '#E65100',
};

export default function PaymentsScreen() {
  const [payments, setPayments] = useState([]);
  const [filter, setFilter] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [phoneModalId, setPhoneModalId] = useState(null);
  const [phone, setPhone] = useState('');
  const [stkLoading, setStkLoading] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await landlordAPI.getPayments(filter);
      setPayments(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  }, [filter]);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await landlordAPI.getPayments(filter);
        if (mounted) setPayments(res.data.results || res.data);
      } catch (e) {
        console.error(e);
      }
    })();
    return () => { mounted = false; };
  }, [filter]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const initiateStk = async () => {
    if (!phone) {
      Alert.alert('Error', 'Enter tenant phone number');
      return;
    }
    setStkLoading(true);
    try {
      await landlordAPI.initiateStk(phoneModalId, { phone });
      setPhoneModalId(null);
      setPhone('');
      Alert.alert('Success', 'STK push sent to tenant phone');
    } catch (e) {
      Alert.alert('Error', e.response?.data?.error || 'Failed to send STK push');
    } finally {
      setStkLoading(false);
    }
  };

  const openStk = (item) => {
    setPhoneModalId(item.id);
    setPhone('');
  };

  const isUnpaid = (s) => s === 'pending' || s === 'overdue' || s === 'late';

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.cardRow}>
        <View style={{ flex: 1 }}>
          <Text style={styles.cardTitle}>{item.tenant_name}</Text>
          <Text style={styles.cardSub}>Unit {item.unit_number}</Text>
          <Text style={styles.cardSub}>Due: {item.due_date}</Text>
          {item.reference ? <Text style={styles.cardSub}>Ref: {item.reference}</Text> : null}
        </View>
        <View style={{ alignItems: 'flex-end' }}>
          <Text style={styles.amount}>KES {item.amount}</Text>
          <View style={[styles.badge, { backgroundColor: (STATUS_COLORS[item.status] || '#999') + '20' }]}>
            <Text style={[styles.badgeText, { color: STATUS_COLORS[item.status] || '#999' }]}>
              {item.status.toUpperCase()}
            </Text>
          </View>
        </View>
      </View>
      {isUnpaid(item.status) && (
        <TouchableOpacity style={styles.stkBtn} onPress={() => openStk(item)}>
          <Ionicons name="phone-portrait-outline" size={16} color="#fff" />
          <Text style={styles.stkBtnText}>Send M-Pesa STK Push</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  const filters = [
    { label: 'All', value: '' },
    { label: 'Pending', value: 'pending' },
    { label: 'Paid', value: 'paid' },
    { label: 'Overdue', value: 'overdue' },
  ];

  return (
    <View style={styles.container}>
      <ScreenHeader title="Payments" />
      <View style={styles.filterRow}>
        {filters.map((f) => (
          <TouchableOpacity
            key={f.value}
            style={[styles.filterBtn, filter === f.value && styles.filterActive]}
            onPress={() => setFilter(f.value)}
          >
            <Text style={[styles.filterText, filter === f.value && styles.filterTextActive]}>{f.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <FlatList
        data={payments}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="card-outline" size={48} color="#ccc" />
            <Text style={styles.emptyText}>No payments found</Text>
          </View>
        }
      />

      {phoneModalId !== null && (
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Send M-Pesa STK Push</Text>
            <Text style={styles.modalSub}>Enter the tenant's M-Pesa phone number</Text>
            <TextInput
              style={styles.input}
              placeholder="0712345678"
              placeholderTextColor="#999"
              value={phone}
              onChangeText={setPhone}
              keyboardType="phone-pad"
            />
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setPhoneModalId(null)}>
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.submitBtn, stkLoading && { opacity: 0.5 }]} onPress={initiateStk} disabled={stkLoading}>
                <Text style={styles.submitText}>{stkLoading ? 'Sending...' : 'Send'}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  filterRow: { flexDirection: 'row', paddingHorizontal: 12, paddingVertical: 8 },
  filterBtn: {
    paddingHorizontal: 14, paddingVertical: 7, borderRadius: 18,
    borderWidth: 1, borderColor: '#ddd', marginRight: 8,
  },
  filterActive: { backgroundColor: '#E65100', borderColor: '#E65100' },
  filterText: { fontSize: 12, color: '#666' },
  filterTextActive: { color: '#fff' },
  list: { padding: 12 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 10, elevation: 2,
  },
  cardRow: { flexDirection: 'row', justifyContent: 'space-between' },
  cardTitle: { fontSize: 16, fontWeight: 'bold', color: '#333' },
  cardSub: { fontSize: 12, color: '#888', marginTop: 2 },
  amount: { fontSize: 16, fontWeight: 'bold', color: '#333' },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8, marginTop: 4 },
  badgeText: { fontSize: 10, fontWeight: 'bold' },
  stkBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    backgroundColor: '#0D47A1', borderRadius: 8, padding: 12, marginTop: 12,
  },
  stkBtnText: { color: '#fff', fontSize: 14, fontWeight: 'bold', marginLeft: 6 },
  empty: { alignItems: 'center', marginTop: 60 },
  emptyText: { fontSize: 16, color: '#999', marginTop: 12 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContent: {
    backgroundColor: '#fff', borderTopLeftRadius: 20, borderTopRightRadius: 20,
    padding: 24,
  },
  modalTitle: { fontSize: 20, fontWeight: 'bold', marginBottom: 6, color: '#333' },
  modalSub: { fontSize: 13, color: '#888', marginBottom: 14 },
  input: {
    backgroundColor: '#F5F5F5', borderRadius: 8, padding: 12, fontSize: 16, color: '#333',
  },
  modalActions: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: 16 },
  cancelBtn: { padding: 12, marginRight: 12 },
  cancelText: { fontSize: 16, color: '#666' },
  submitBtn: {
    backgroundColor: '#E65100', borderRadius: 8, paddingHorizontal: 24, padding: 12,
  },
  submitText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});

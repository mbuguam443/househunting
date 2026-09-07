import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { tenantAPI } from '../services/api';

const STATUS_COLORS = {
  pending: '#FF9800',
  paid: '#4CAF50',
  overdue: '#D32F2F',
  late: '#E65100',
};

export default function PaymentsScreen() {
  const [payments, setPayments] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await tenantAPI.getPayments();
      setPayments(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await tenantAPI.getPayments();
        if (mounted) setPayments(res.data.results || res.data);
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

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.cardRow}>
        <View>
          <Text style={styles.cardTitle}>Rent Payment</Text>
          <Text style={styles.cardSub}>Due: {item.due_date}</Text>
          {item.paid_date && (
            <Text style={styles.cardSub}>Paid: {item.paid_date}</Text>
          )}
        </View>
        <View style={styles.rightSection}>
          <Text style={styles.amount}>KES {item.amount}</Text>
          <View style={[styles.badge, { backgroundColor: STATUS_COLORS[item.status] + '20' }]}>
            <Text style={[styles.badgeText, { color: STATUS_COLORS[item.status] }]}>
              {item.status.toUpperCase()}
            </Text>
          </View>
        </View>
      </View>
      {item.reference && (
        <Text style={styles.ref}>Ref: {item.reference}</Text>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Payment History</Text>
      </View>
      <FlatList
        data={payments}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="receipt-outline" size={48} color="#ccc" />
            <Text style={styles.emptyText}>No payments yet</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  header: { backgroundColor: '#1B5E20', padding: 20, paddingTop: 16 },
  headerTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  list: { padding: 16 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16,
    marginBottom: 12, elevation: 2,
  },
  cardRow: { flexDirection: 'row', justifyContent: 'space-between' },
  cardTitle: { fontSize: 16, fontWeight: 'bold', color: '#333' },
  cardSub: { fontSize: 13, color: '#888', marginTop: 4 },
  rightSection: { alignItems: 'flex-end' },
  amount: { fontSize: 16, fontWeight: 'bold', color: '#333' },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8, marginTop: 4 },
  badgeText: { fontSize: 11, fontWeight: 'bold' },
  ref: { fontSize: 12, color: '#999', marginTop: 8 },
  empty: { alignItems: 'center', marginTop: 60 },
  emptyText: { fontSize: 16, color: '#999', marginTop: 12 },
});

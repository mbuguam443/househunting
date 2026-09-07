import React, { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, RefreshControl, TouchableOpacity, TextInput, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { adminAPI } from '../services/api';

export default function RevenueScreen() {
  const [data, setData] = useState(null);
  const [filter, setFilter] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [fee, setFee] = useState('');
  const [savingFee, setSavingFee] = useState(false);

  const handleUpdateFee = async () => {
    if (!fee) {
      Alert.alert('Error', 'Enter a fee amount');
      return;
    }
    setSavingFee(true);
    try {
      await adminAPI.updateFee({ fee_per_unit: parseFloat(fee) });
      Alert.alert('Success', 'Global per-unit fee updated');
      setFee('');
    } catch (e) {
      Alert.alert('Error', 'Failed to update fee');
    } finally {
      setSavingFee(false);
    }
  };

  const fetchData = useCallback(async () => {
    try {
      const res = await adminAPI.getRevenue(filter);
      setData(res.data);
    } catch (e) {
      console.error(e);
    }
  }, [filter]);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await adminAPI.getRevenue(filter);
        if (mounted) setData(res.data);
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

  const filters = [
    { label: 'All', value: '' },
    { label: 'Active', value: 'active' },
    { label: 'Expired', value: 'expired' },
  ];

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Revenue</Text>
      </View>

      {data && (
        <>
          <View style={styles.statsRow}>
            <View style={styles.statCard}>
              <Text style={styles.statLabel}>Total Revenue</Text>
              <Text style={styles.statValue}>KES {data.total_revenue}</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statLabel}>Active Revenue</Text>
              <Text style={[styles.statValue, { color: '#4CAF50' }]}>KES {data.active_revenue}</Text>
            </View>
          </View>

          <View style={styles.feeCard}>
            <Text style={styles.sectionTitle}>Global Per-Unit Fee (KES)</Text>
            <Text style={styles.feeSub}>Applies as the default charge per unit across the platform.</Text>
            <View style={styles.feeRow}>
              <TextInput
                style={[styles.feeInput, { flex: 1 }]}
                placeholder="e.g. 50"
                placeholderTextColor="#999"
                value={fee}
                onChangeText={setFee}
                keyboardType="numeric"
              />
              <TouchableOpacity
                style={[styles.feeBtn, savingFee && { opacity: 0.5 }]}
                onPress={handleUpdateFee}
                disabled={savingFee}
              >
                <Text style={styles.feeBtnText}>{savingFee ? 'Saving...' : 'Update Fee'}</Text>
              </TouchableOpacity>
            </View>
          </View>

          <View style={styles.filterRow}>
            {filters.map((f) => (
              <TouchableOpacity
                key={f.value}
                style={[styles.filterBtn, filter === f.value && styles.filterActive]}
                onPress={() => setFilter(f.value)}
              >
                <Text style={[styles.filterText, filter === f.value && styles.filterTextActive]}>
                  {f.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Subscriptions</Text>
            {data.subscriptions.map((sub) => (
              <View key={sub.id} style={styles.subItem}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.subName}>{sub.landlord_username}</Text>
                  <Text style={styles.subDetail}>{sub.plan_name || 'Custom'} | {sub.unit_count} units</Text>
                </View>
                <View style={{ alignItems: 'flex-end' }}>
                  <Text style={styles.subAmount}>KES {sub.amount}</Text>
                  <View style={[styles.badge, sub.status === 'active' ? styles.activeBadge : styles.inactiveBadge]}>
                    <Text style={[styles.badgeText, sub.status === 'active' ? styles.activeText : styles.inactiveText]}>
                      {sub.status.toUpperCase()}
                    </Text>
                  </View>
                </View>
              </View>
            ))}
            {data.subscriptions.length === 0 && (
              <Text style={styles.emptyText}>No subscriptions found</Text>
            )}
          </View>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  header: { backgroundColor: '#0D47A1', padding: 20, paddingTop: 16 },
  headerTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  statsRow: { flexDirection: 'row', padding: 12, justifyContent: 'space-between' },
  statCard: {
    width: '48%', backgroundColor: '#fff', borderRadius: 12, padding: 16, elevation: 2,
  },
  statLabel: { fontSize: 13, color: '#888' },
  statValue: { fontSize: 22, fontWeight: 'bold', color: '#333', marginTop: 4 },
  feeCard: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16, margin: 12, elevation: 2,
  },
  feeSub: { fontSize: 12, color: '#888', marginBottom: 12 },
  feeRow: { flexDirection: 'row', alignItems: 'center' },
  feeInput: {
    backgroundColor: '#F5F5F5', borderRadius: 8, padding: 12,
    fontSize: 16, color: '#333',
  },
  feeBtn: { backgroundColor: '#0D47A1', borderRadius: 8, paddingHorizontal: 20, padding: 12, marginLeft: 8 },
  feeBtnText: { color: '#fff', fontWeight: 'bold' },
  filterRow: { flexDirection: 'row', paddingHorizontal: 12, marginBottom: 8 },
  filterBtn: {
    paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20,
    borderWidth: 1, borderColor: '#ddd', marginRight: 8,
  },
  filterActive: { backgroundColor: '#0D47A1', borderColor: '#0D47A1' },
  filterText: { fontSize: 13, color: '#666' },
  filterTextActive: { color: '#fff' },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16,
    margin: 12, elevation: 2,
  },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 12, color: '#333' },
  subItem: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#F0F0F0',
  },
  subName: { fontSize: 14, fontWeight: 'bold', color: '#333' },
  subDetail: { fontSize: 12, color: '#888', marginTop: 2 },
  subAmount: { fontSize: 14, fontWeight: 'bold', color: '#333' },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8, marginTop: 4, alignSelf: 'flex-end' },
  activeBadge: { backgroundColor: '#E8F5E9' },
  inactiveBadge: { backgroundColor: '#FFF3E0' },
  badgeText: { fontSize: 10, fontWeight: 'bold' },
  activeText: { color: '#2E7D32' },
  inactiveText: { color: '#E65100' },
  emptyText: { fontSize: 14, color: '#999', textAlign: 'center', padding: 20 },
});

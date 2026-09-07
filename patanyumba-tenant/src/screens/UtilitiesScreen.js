import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { tenantAPI } from '../services/api';

const UTILITY_ICONS = {
  water: 'water',
  electricity: 'flash',
  trash: 'trash',
};

export default function UtilitiesScreen() {
  const [bills, setBills] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await tenantAPI.getUtilities();
      setBills(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await tenantAPI.getUtilities();
        if (mounted) setBills(res.data.results || res.data);
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
        <View style={styles.iconContainer}>
          <Ionicons
            name={UTILITY_ICONS[item.utility_type] || 'help-circle'}
            size={24}
            color="#1B5E20"
          />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.cardTitle}>{item.utility_type_display}</Text>
          <Text style={styles.cardSub}>
            {item.period_start} to {item.period_end}
          </Text>
          {item.units_consumed && (
            <Text style={styles.cardSub}>
              {item.units_consumed} units @ KES {item.rate_per_unit}/unit
            </Text>
          )}
        </View>
        <View style={styles.rightSection}>
          <Text style={styles.amount}>KES {item.amount}</Text>
          <View style={[styles.badge, item.status === 'paid' ? styles.paidBadge : styles.pendingBadge]}>
            <Text style={[styles.badgeText, item.status === 'paid' ? styles.paidText : styles.pendingText]}>
              {item.status.toUpperCase()}
            </Text>
          </View>
        </View>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Utility Bills</Text>
      </View>
      <FlatList
        data={bills}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="flash-outline" size={48} color="#ccc" />
            <Text style={styles.emptyText}>No utility bills</Text>
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
  cardRow: { flexDirection: 'row', alignItems: 'center' },
  iconContainer: {
    width: 44, height: 44, borderRadius: 22, backgroundColor: '#E8F5E9',
    justifyContent: 'center', alignItems: 'center', marginRight: 12,
  },
  cardTitle: { fontSize: 16, fontWeight: 'bold', color: '#333' },
  cardSub: { fontSize: 12, color: '#888', marginTop: 2 },
  rightSection: { alignItems: 'flex-end' },
  amount: { fontSize: 15, fontWeight: 'bold', color: '#333' },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8, marginTop: 4 },
  paidBadge: { backgroundColor: '#E8F5E9' },
  pendingBadge: { backgroundColor: '#FFF3E0' },
  badgeText: { fontSize: 10, fontWeight: 'bold' },
  paidText: { color: '#2E7D32' },
  pendingText: { color: '#E65100' },
  empty: { alignItems: 'center', marginTop: 60 },
  emptyText: { fontSize: 16, color: '#999', marginTop: 12 },
});

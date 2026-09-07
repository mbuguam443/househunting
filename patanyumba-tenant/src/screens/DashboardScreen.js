import React, { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, RefreshControl, TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { tenantAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

export default function DashboardScreen({ navigation }) {
  const { logout } = useAuth();
  const [data, setData] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await tenantAPI.getDashboard();
      setData(res.data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await tenantAPI.getDashboard();
        if (mounted) setData(res.data);
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

  if (!data) {
    return (
      <View style={styles.center}>
        <Text>Loading...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Dashboard</Text>
        <TouchableOpacity onPress={logout} style={styles.logoutBtn}>
          <Ionicons name="log-out-outline" size={22} color="#fff" />
        </TouchableOpacity>
      </View>

      {data.tenancy ? (
        <>
          <View style={styles.card}>
            <Text style={styles.cardLabel}>Unit</Text>
            <Text style={styles.cardValue}>
              {data.tenancy.property_name} - {data.tenancy.unit_number}
            </Text>
            <Text style={styles.cardSub}>
              KES {data.tenancy.monthly_rent}/month
            </Text>
          </View>

          <TouchableOpacity
            style={styles.leaseButton}
            onPress={() => navigation.navigate('Lease')}
          >
            <Ionicons name="document-text-outline" size={20} color="#1B5E20" />
            <Text style={styles.leaseButtonText}>View Lease Agreement</Text>
          </TouchableOpacity>

          <View style={[styles.card, styles.balanceCard]}>
            <Ionicons name="wallet-outline" size={28} color="#D32F2F" />
            <View style={{ marginLeft: 12 }}>
              <Text style={styles.cardLabel}>Outstanding Balance</Text>
              <Text style={[styles.cardValue, { color: '#D32F2F' }]}>
                KES {data.balance}
              </Text>
            </View>
          </View>

          {data.pending_payments.length > 0 && (
            <View style={styles.card}>
              <Text style={styles.sectionTitle}>Pending Payments</Text>
              {data.pending_payments.map((p) => (
                <View key={p.id} style={styles.listItem}>
                  <View>
                    <Text style={styles.listItemTitle}>Rent - {p.unit_number}</Text>
                    <Text style={styles.listItemSub}>Due: {p.due_date}</Text>
                  </View>
                  <Text style={[styles.badge, p.status === 'overdue' ? styles.badgeDanger : styles.badgeWarning]}>
                    KES {p.amount}
                  </Text>
                </View>
              ))}
            </View>
          )}

          <TouchableOpacity
            style={styles.payButton}
            onPress={() => navigation.navigate('Pay')}
          >
            <Ionicons name="card-outline" size={20} color="#fff" />
            <Text style={styles.payButtonText}>Pay Now</Text>
          </TouchableOpacity>
        </>
      ) : (
        <View style={styles.emptyCard}>
          <Ionicons name="home-outline" size={48} color="#999" />
          <Text style={styles.emptyText}>No active tenancy</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { backgroundColor: '#1B5E20', padding: 20, paddingTop: 16, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  headerTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  logoutBtn: { padding: 4 },
  leaseButton: {
    flexDirection: 'row', borderWidth: 1, borderColor: '#1B5E20', borderRadius: 12,
    padding: 14, marginHorizontal: 16, marginTop: 12, alignItems: 'center', justifyContent: 'center',
  },
  leaseButtonText: { color: '#1B5E20', fontSize: 15, fontWeight: '600', marginLeft: 8 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16,
    marginHorizontal: 16, marginTop: 12, elevation: 2,
    shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 4,
  },
  balanceCard: { flexDirection: 'row', alignItems: 'center' },
  cardLabel: { fontSize: 13, color: '#666', marginBottom: 4 },
  cardValue: { fontSize: 18, fontWeight: 'bold', color: '#333' },
  cardSub: { fontSize: 14, color: '#888', marginTop: 4 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 8, color: '#333' },
  listItem: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', paddingVertical: 8,
    borderBottomWidth: 1, borderBottomColor: '#eee',
  },
  listItemTitle: { fontSize: 14, fontWeight: '600', color: '#333' },
  listItemSub: { fontSize: 12, color: '#888', marginTop: 2 },
  badge: {
    paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12, fontSize: 12, fontWeight: 'bold',
  },
  badgeWarning: { backgroundColor: '#FFF3E0', color: '#E65100' },
  badgeDanger: { backgroundColor: '#FFEBEE', color: '#D32F2F' },
  payButton: {
    flexDirection: 'row', backgroundColor: '#FF6F00', borderRadius: 12,
    padding: 16, margin: 16, alignItems: 'center', justifyContent: 'center',
  },
  payButtonText: { color: '#fff', fontSize: 16, fontWeight: 'bold', marginLeft: 8 },
  emptyCard: {
    backgroundColor: '#fff', borderRadius: 12, padding: 32,
    margin: 16, alignItems: 'center', elevation: 2,
  },
  emptyText: { fontSize: 16, color: '#999', marginTop: 12 },
});

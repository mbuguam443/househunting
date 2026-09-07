import React, { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, RefreshControl, TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { adminAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

export default function DashboardScreen() {
  const { logout } = useAuth();
  const [data, setData] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await adminAPI.getDashboard();
      setData(res.data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await adminAPI.getDashboard();
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
        <Text style={styles.headerTitle}>Admin Dashboard</Text>
        <TouchableOpacity onPress={logout} style={styles.logoutBtn}>
          <Ionicons name="log-out-outline" size={22} color="#fff" />
        </TouchableOpacity>
      </View>

      <View style={styles.statsGrid}>
        <StatCard icon="people" label="Landlords" value={data.landlords} color="#1B5E20" />
        <StatCard icon="person" label="Tenants" value={data.tenants} color="#0D47A1" />
        <StatCard icon="home" label="Properties" value={data.properties} color="#E65100" />
        <StatCard icon="layers" label="Units" value={data.units} color="#6A1B9A" />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Subscriptions</Text>
        <View style={styles.subRow}>
          <Text style={styles.subLabel}>Active</Text>
          <Text style={[styles.subValue, { color: '#4CAF50' }]}>{data.active_subscriptions}</Text>
        </View>
        <View style={styles.subRow}>
          <Text style={styles.subLabel}>Expired</Text>
          <Text style={[styles.subValue, { color: '#D32F2F' }]}>{data.expired_subscriptions}</Text>
        </View>
        <View style={styles.subRow}>
          <Text style={styles.subLabel}>Total Revenue</Text>
          <Text style={[styles.subValue, { color: '#1B5E20' }]}>KES {data.total_revenue}</Text>
        </View>
      </View>

      {data.recent_inquiries.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Recent Inquiries</Text>
          {data.recent_inquiries.map((inq) => (
            <View key={inq.id} style={styles.inquiryItem}>
              <View>
                <Text style={styles.inquiryName}>{inq.name}</Text>
                <Text style={styles.inquiryMsg} numberOfLines={1}>{inq.message}</Text>
              </View>
              <Text style={styles.inquiryDate}>
                {new Date(inq.created_at).toLocaleDateString()}
              </Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

function StatCard({ icon, label, value, color }) {
  return (
    <View style={[styles.statCard, { borderLeftColor: color }]}>
      <Ionicons name={icon} size={24} color={color} />
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { backgroundColor: '#0D47A1', padding: 20, paddingTop: 16, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  headerTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  logoutBtn: { padding: 4 },
  statsGrid: {
    flexDirection: 'row', flexWrap: 'wrap', padding: 12, justifyContent: 'space-between',
  },
  statCard: {
    width: '47%', backgroundColor: '#fff', borderRadius: 12, padding: 16,
    marginBottom: 8, elevation: 2, borderLeftWidth: 4,
  },
  statValue: { fontSize: 28, fontWeight: 'bold', color: '#333', marginTop: 8 },
  statLabel: { fontSize: 13, color: '#888', marginTop: 4 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16,
    marginHorizontal: 12, marginBottom: 12, elevation: 2,
  },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 12, color: '#333' },
  subRow: {
    flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8,
    borderBottomWidth: 1, borderBottomColor: '#F0F0F0',
  },
  subLabel: { fontSize: 14, color: '#666' },
  subValue: { fontSize: 16, fontWeight: 'bold' },
  inquiryItem: {
    flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8,
    borderBottomWidth: 1, borderBottomColor: '#F0F0F0',
  },
  inquiryName: { fontSize: 14, fontWeight: '600', color: '#333' },
  inquiryMsg: { fontSize: 12, color: '#888', marginTop: 2, maxWidth: 200 },
  inquiryDate: { fontSize: 12, color: '#999' },
});

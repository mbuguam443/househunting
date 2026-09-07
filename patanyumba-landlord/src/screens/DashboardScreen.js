import React, { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, RefreshControl, TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { landlordAPI } from '../services/api';
import { StatsCard } from '../components/UI';
import { useAuth } from '../contexts/AuthContext';

export default function DashboardScreen() {
  const [data, setData] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const { user, logout } = useAuth();

  const fetchData = useCallback(async () => {
    try {
      const res = await landlordAPI.getDashboard();
      setData(res.data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await landlordAPI.getDashboard();
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

  const handleLogout = () => {
    logout();
  };

  if (!data) {
    return <View style={styles.center}><Text>Loading...</Text></View>;
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <Text style={styles.headerTitle}>Dashboard</Text>
          <Text style={styles.headerSub}>Welcome, {user?.user?.full_name || user?.username || 'Landlord'}</Text>
        </View>
        <TouchableOpacity onPress={handleLogout} style={styles.logoutBtn}>
          <Ionicons name="log-out-outline" size={22} color="#fff" />
        </TouchableOpacity>
      </View>

      <View style={styles.banner}>
        <Text style={styles.bannerText}>
          Subscription: {data.subscription_status.toUpperCase()}
        </Text>
        {data.trial_info && (
          <Text style={styles.bannerSub}>
            Trial ends in {data.trial_info.remaining_days} days
          </Text>
        )}
      </View>

      <View style={styles.statsGrid}>
        <StatsCard icon="business" label="Properties" value={data.properties} color="#0D47A1" />
        <StatsCard icon="layers" label="Units" value={data.units} color="#6A1B9A" />
        <StatsCard icon="checkmark" label="Occupied" value={data.occupied_units} color="#2E7D32" />
        <StatsCard icon="remove" label="Vacant" value={data.vacant_units} color="#E65100" />
        <StatsCard icon="people" label="Tenants" value={data.tenants} color="#1565C0" />
        <StatsCard icon="receipt" label="Active Tenancies" value={data.active_tenancies} color="#00838F" />
        <StatsCard icon="build" label="Open Maintenance" value={data.pending_maintenance} color="#D32F2F" />
        <StatsCard icon="wallet" label="Outstanding Rent" value={`KES ${data.outstanding_rent}`} color="#C62828" />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>This Month Collected</Text>
        <Text style={styles.revenue}>KES {data.monthly_collected}</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: {
    backgroundColor: '#E65100', padding: 20, paddingTop: 16,
    flexDirection: 'row', alignItems: 'center',
  },
  headerTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  headerSub: { fontSize: 13, color: '#FFE0B2', marginTop: 4 },
  logoutBtn: { padding: 8 },
  banner: {
    backgroundColor: '#0D47A1', margin: 12, borderRadius: 10, padding: 14,
  },
  bannerText: { color: '#fff', fontSize: 15, fontWeight: 'bold' },
  bannerSub: { color: '#BBDEFB', fontSize: 12, marginTop: 4 },
  statsGrid: {
    flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 12, justifyContent: 'space-between',
  },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16,
    margin: 12, elevation: 2,
  },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 8, color: '#333' },
  revenue: { fontSize: 28, fontWeight: 'bold', color: '#E65100' },
});

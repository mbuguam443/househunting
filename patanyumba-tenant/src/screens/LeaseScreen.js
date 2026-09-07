import React, { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { tenantAPI } from '../services/api';

export default function LeaseScreen() {
  const [lease, setLease] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await tenantAPI.getLease();
      setLease(res.data.lease);
    } catch (e) {
      console.error(e);
    }
  }, []);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await tenantAPI.getLease();
        if (mounted) setLease(res.data.lease);
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

  if (!lease) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Lease Agreement</Text>
        </View>
        <View style={styles.empty}>
          <Ionicons name="document-text-outline" size={48} color="#ccc" />
          <Text style={styles.emptyText}>No lease agreement found</Text>
        </View>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Lease Agreement</Text>
      </View>

      <View style={styles.card}>
        <View style={[styles.statusBadge, lease.status === 'active' ? styles.activeBadge : styles.inactiveBadge]}>
          <Text style={[styles.statusText, lease.status === 'active' ? styles.activeText : styles.inactiveText]}>
            {lease.status.toUpperCase()}
          </Text>
        </View>

        <InfoRow label="Unit" value={lease.unit_number} />
        <InfoRow label="Start Date" value={lease.start_date} />
        <InfoRow label="End Date" value={lease.end_date} />
        <InfoRow label="Monthly Rent" value={`KES ${lease.monthly_rent}`} />
        <InfoRow label="Deposit" value={`KES ${lease.deposit_amount}`} />
        <InfoRow label="Payment Due Day" value={`${lease.payment_due_day} of each month`} />
        <InfoRow label="Late Fee" value={`KES ${lease.late_fee}`} />
        <InfoRow label="Notice Period" value={`${lease.notice_period_days} days`} />
      </View>

      {lease.terms && (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Terms & Conditions</Text>
          <Text style={styles.terms}>{lease.terms}</Text>
        </View>
      )}

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Acceptance</Text>
        <InfoRow
          label="Landlord"
          value={lease.landlord_accepted ? `Accepted on ${new Date(lease.landlord_accepted_at).toLocaleDateString()}` : 'Pending'}
        />
        <InfoRow
          label="Tenant"
          value={lease.tenant_accepted ? `Accepted on ${new Date(lease.tenant_accepted_at).toLocaleDateString()}` : 'Pending'}
        />
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
  header: { backgroundColor: '#1B5E20', padding: 20, paddingTop: 16 },
  headerTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16,
    margin: 16, marginBottom: 0, elevation: 2,
  },
  statusBadge: {
    alignSelf: 'flex-start', paddingHorizontal: 12, paddingVertical: 6,
    borderRadius: 12, marginBottom: 16,
  },
  activeBadge: { backgroundColor: '#E8F5E9' },
  inactiveBadge: { backgroundColor: '#FFF3E0' },
  statusText: { fontSize: 12, fontWeight: 'bold' },
  activeText: { color: '#2E7D32' },
  inactiveText: { color: '#E65100' },
  infoRow: {
    flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 10,
    borderBottomWidth: 1, borderBottomColor: '#F0F0F0',
  },
  infoLabel: { fontSize: 14, color: '#888' },
  infoValue: { fontSize: 14, fontWeight: '600', color: '#333' },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 12, color: '#333' },
  terms: { fontSize: 14, color: '#555', lineHeight: 22 },
  empty: { flex: 1, justifyContent: 'center', alignItems: 'center', marginTop: 100 },
  emptyText: { fontSize: 16, color: '#999', marginTop: 12 },
});

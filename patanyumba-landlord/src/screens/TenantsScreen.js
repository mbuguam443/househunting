import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TextInput, TouchableOpacity, StyleSheet,
  RefreshControl, Alert, ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { landlordAPI } from '../services/api';
import { ScreenHeader, BottomModal, Field, SubmitBar } from '../components/UI';

export default function TenantsScreen() {
  const [tenants, setTenants] = useState([]);
  const [search, setSearch] = useState('');
  const [refresh, setRefresh] = useState(false);
  const [assignVisible, setAssignVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Assign flow state
  const [assignTenant, setAssignTenant] = useState(null);
  const [properties, setProperties] = useState([]);
  const [units, setUnits] = useState([]);
  const [unitOptions, setUnitOptions] = useState([]);
  const [selProp, setSelProp] = useState('');
  const [selUnit, setSelUnit] = useState('');
  const [startDate, setStartDate] = useState('');
  const [deposit, setDeposit] = useState('');

  const fetchData = useCallback(async () => {
    try {
      const res = await landlordAPI.getTenants(search);
      const props = await landlordAPI.getProperties();
      setTenants(res.data.results || res.data);
      setProperties(props.data.results || props.data);
    } catch (e) {
      console.error(e);
    }
  }, [search]);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await landlordAPI.getTenants(search);
        const props = await landlordAPI.getProperties();
        if (mounted) {
          setTenants(res.data.results || res.data);
          setProperties(props.data.results || props.data);
        }
      } catch (e) {
        console.error(e);
      }
    })();
    return () => { mounted = false; };
  }, [search]);

  const loadUnits = async (propId) => {
    setSelProp(propId);
    setSelUnit('');
    setUnitOptions([]);
    try {
      const res = await landlordAPI.getUnits(propId);
      setUnitOptions(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const openAssign = (tenant) => {
    setAssignTenant(tenant);
    setSelProp('');
    setSelUnit('');
    setStartDate('');
    setDeposit('');
    setUnitOptions([]);
    setAssignVisible(true);
  };

  const handleAssign = async () => {
    if (!assignTenant || !selUnit || !startDate) {
      Alert.alert('Error', 'Select a unit and enter start date');
      return;
    }
    setSubmitting(true);
    try {
      await landlordAPI.createTenancy({
        unit: parseInt(selUnit),
        tenant: assignTenant.user.id,
        start_date: startDate,
        deposit: deposit ? parseFloat(deposit) : 0,
      });
      setAssignVisible(false);
      await fetchData();
      Alert.alert('Success', `${assignTenant.user.full_name} assigned to unit`);
    } catch (e) {
      Alert.alert('Error', e.response?.data?.error || 'Failed to assign');
    } finally {
      setSubmitting(false);
    }
  };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.cardTop}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {item.user.first_name ? item.user.first_name[0] : item.user.username[0]}
          </Text>
        </View>
        <View style={{ flex: 1, marginLeft: 12 }}>
          <Text style={styles.cardTitle}>{item.user.full_name}</Text>
          <Text style={styles.cardSub}>@{item.user.username}</Text>
          <Text style={styles.cardSub}>{item.phone || 'No phone'}</Text>
        </View>
      </View>
      <TouchableOpacity style={styles.assignBtn} onPress={() => openAssign(item)}>
        <Ionicons name="add-circle-outline" size={16} color="#0D47A1" />
        <Text style={styles.assignBtnText}>Assign to Unit</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      <ScreenHeader title="Tenants" />

      <View style={styles.searchBar}>
        <Ionicons name="search" size={20} color="#999" />
        <TextInput
          style={styles.searchInput}
          placeholder="Search tenants..."
          placeholderTextColor="#999"
          value={search}
          onChangeText={setSearch}
        />
      </View>

      <FlatList
        data={tenants}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refresh} onRefresh={async () => { setRefresh(true); await fetchData(); setRefresh(false); }} />}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="people-outline" size={48} color="#ccc" />
            <Text style={styles.emptyText}>No tenants found</Text>
          </View>
        }
      />

      <BottomModal visible={assignVisible} onClose={() => setAssignVisible(false)} title={`Assign ${assignTenant?.user?.full_name || ''}`}>
        <ScrollView>
          <Text style={styles.label}>Property</Text>
          <View style={styles.chipRow}>
            {properties.map((p) => (
              <TouchableOpacity
                key={p.id}
                style={[styles.chip, selProp === String(p.id) && styles.chipActive]}
                onPress={() => loadUnits(String(p.id))}
              >
                <Text style={[styles.chipText, selProp === String(p.id) && styles.chipTextActive]}>{p.name}</Text>
              </TouchableOpacity>
            ))}
          </View>

          {selProp ? (
            <>
              <Text style={styles.label}>Vacant Unit</Text>
              <View style={styles.chipRow}>
                {unitOptions.filter((u) => u.status === 'vacant').map((u) => (
                  <TouchableOpacity
                    key={u.id}
                    style={[styles.chip, selUnit === String(u.id) && styles.chipActive]}
                    onPress={() => setSelUnit(String(u.id))}
                  >
                    <Text style={[styles.chipText, selUnit === String(u.id) && styles.chipTextActive]}>
                      {u.unit_number} · KES {u.monthly_rent}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </>
          ) : null}

          <Field label="Start Date (YYYY-MM-DD) *" value={startDate} onChangeText={setStartDate} placeholder="2026-09-01" />
          <Field label="Deposit Paid (KES)" value={deposit} onChangeText={setDeposit} keyboardType="numeric" />
          <SubmitBar onCancel={() => setAssignVisible(false)} onSubmit={handleAssign} submitting={submitting} submitLabel="Assign" />
        </ScrollView>
      </BottomModal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  searchBar: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff',
    margin: 12, marginBottom: 0, paddingHorizontal: 12, borderRadius: 8, elevation: 1,
  },
  searchInput: { flex: 1, padding: 10, fontSize: 16, color: '#333' },
  list: { padding: 12 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 10, elevation: 2,
  },
  cardTop: { flexDirection: 'row', alignItems: 'center' },
  avatar: {
    width: 44, height: 44, borderRadius: 22, backgroundColor: '#E65100',
    justifyContent: 'center', alignItems: 'center',
  },
  avatarText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  cardTitle: { fontSize: 16, fontWeight: 'bold', color: '#333' },
  cardSub: { fontSize: 12, color: '#888', marginTop: 2 },
  assignBtn: {
    flexDirection: 'row', alignItems: 'center', marginTop: 12,
    borderWidth: 1, borderColor: '#0D47A1', borderRadius: 8, padding: 10, justifyContent: 'center',
  },
  assignBtnText: { color: '#0D47A1', fontWeight: 'bold', marginLeft: 6 },
  empty: { alignItems: 'center', marginTop: 60 },
  emptyText: { fontSize: 16, color: '#999', marginTop: 12 },
  label: { fontSize: 14, fontWeight: '600', marginBottom: 8, color: '#333' },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 16 },
  chip: {
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8,
    borderWidth: 1, borderColor: '#ddd', marginRight: 8, marginBottom: 8,
  },
  chipActive: { backgroundColor: '#E65100', borderColor: '#E65100' },
  chipText: { fontSize: 13, color: '#666' },
  chipTextActive: { color: '#fff' },
});

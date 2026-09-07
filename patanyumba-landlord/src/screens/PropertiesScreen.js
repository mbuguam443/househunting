import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  RefreshControl, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { landlordAPI } from '../services/api';
import { ScreenHeader, BottomModal, Field, SubmitBar } from '../components/UI';

const EMPTY_FORM = {
  name: '', description: '', county: '', town: '', estate: '',
  address: '', latitude: '', longitude: '',
  water_rate: '', electricity_rate: '', trash_rate: '',
};

export default function PropertiesScreen({ navigation }) {
  const [properties, setProperties] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await landlordAPI.getProperties();
      setProperties(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await landlordAPI.getProperties();
        if (mounted) setProperties(res.data.results || res.data);
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

  const handleCreate = async () => {
    if (!form.name || !form.county || !form.town) {
      Alert.alert('Error', 'Name, county, and town are required');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        latitude: form.latitude ? parseFloat(form.latitude) : null,
        longitude: form.longitude ? parseFloat(form.longitude) : null,
        water_rate: parseFloat(form.water_rate || 0),
        electricity_rate: parseFloat(form.electricity_rate || 0),
        trash_rate: parseFloat(form.trash_rate || 0),
      };
      await landlordAPI.createProperty(payload);
      setModalVisible(false);
      setForm(EMPTY_FORM);
      await fetchData();
      Alert.alert('Success', 'Property created');
    } catch (e) {
      Alert.alert('Error', e.response?.data?.error || 'Failed to create property');
    } finally {
      setSubmitting(false);
    }
  };

  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate('PropertyDetail', { id: item.id })}
    >
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{item.name}</Text>
        <Ionicons name="chevron-forward" size={20} color="#999" />
      </View>
      <Text style={styles.cardLoc}>
        {item.county}, {item.town}{item.estate ? ` - ${item.estate}` : ''}
      </Text>
      <View style={styles.statsRow}>
        <Text style={styles.statItem}>{item.total_units} units</Text>
        <Text style={styles.statItemGreen}>{item.vacant_units} vacant</Text>
        <Text style={styles.statItemOrange}>{item.occupied_units} occupied</Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <ScreenHeader
        title="Properties"
        right={
          <TouchableOpacity style={styles.addBtn} onPress={() => setModalVisible(true)}>
            <Ionicons name="add-circle-outline" size={24} color="#fff" />
          </TouchableOpacity>
        }
      />
      <FlatList
        data={properties}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="business-outline" size={48} color="#ccc" />
            <Text style={styles.emptyText}>No properties yet</Text>
          </View>
        }
      />

      <BottomModal visible={modalVisible} onClose={() => setModalVisible(false)} title="Add Property">
        <Field label="Name *" value={form.name} onChangeText={(v) => setForm({ ...form, name: v })} placeholder="e.g. Greenview Apartments" />
        <Field label="County *" value={form.county} onChangeText={(v) => setForm({ ...form, county: v })} placeholder="e.g. Nairobi" />
        <Field label="Town *" value={form.town} onChangeText={(v) => setForm({ ...form, town: v })} placeholder="e.g. Kilimani" />
        <Field label="Estate" value={form.estate} onChangeText={(v) => setForm({ ...form, estate: v })} />
        <Field label="Address" value={form.address} onChangeText={(v) => setForm({ ...form, address: v })} />
        <Field label="Description" value={form.description} onChangeText={(v) => setForm({ ...form, description: v })} multiline numberOfLines={3} />
        <Field label="Water Rate (KES/unit)" value={form.water_rate} onChangeText={(v) => setForm({ ...form, water_rate: v })} keyboardType="numeric" />
        <Field label="Electricity Rate (KES/unit)" value={form.electricity_rate} onChangeText={(v) => setForm({ ...form, electricity_rate: v })} keyboardType="numeric" />
        <Field label="Trash Rate (KES)" value={form.trash_rate} onChangeText={(v) => setForm({ ...form, trash_rate: v })} keyboardType="numeric" />
        <SubmitBar onCancel={() => setModalVisible(false)} onSubmit={handleCreate} submitting={submitting} submitLabel="Create" />
      </BottomModal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  addBtn: { padding: 4 },
  list: { padding: 12 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 10, elevation: 2,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { fontSize: 17, fontWeight: 'bold', color: '#333' },
  cardLoc: { fontSize: 13, color: '#888', marginTop: 6 },
  statsRow: { flexDirection: 'row', marginTop: 10 },
  statItem: { fontSize: 12, color: '#666', marginRight: 14 },
  statItemGreen: { fontSize: 12, color: '#2E7D32', marginRight: 14 },
  statItemOrange: { fontSize: 12, color: '#E65100' },
  empty: { alignItems: 'center', marginTop: 60 },
  emptyText: { fontSize: 16, color: '#999', marginTop: 12 },
});

import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  RefreshControl, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { landlordAPI } from '../services/api';
import { ScreenHeader, BottomModal, Field, SubmitBar } from '../components/UI';

const EMPTY_FORM = {
  property: '', unit_number: '', house_type: '', bedrooms: '1', bathrooms: '1',
  monthly_rent: '', deposit: '', floor: '1', description: '', status: 'vacant',
};

export default function UnitsScreen({ navigation }) {
  const [units, setUnits] = useState([]);
  const [properties, setProperties] = useState([]);
  const [houseTypes, setHouseTypes] = useState([]);
  const [filterProp, setFilterProp] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [unitsRes, propsRes, typesRes] = await Promise.all([
        landlordAPI.getUnits(filterProp),
        landlordAPI.getProperties(),
        landlordAPI.getHouseTypes(),
      ]);
      setUnits(unitsRes.data.results || unitsRes.data);
      setProperties(propsRes.data.results || propsRes.data);
      setHouseTypes(typesRes.data.results || typesRes.data);
    } catch (e) {
      console.error(e);
    }
  }, [filterProp]);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [unitsRes, propsRes, typesRes] = await Promise.all([
          landlordAPI.getUnits(filterProp),
          landlordAPI.getProperties(),
          landlordAPI.getHouseTypes(),
        ]);
        if (mounted) {
          setUnits(unitsRes.data.results || unitsRes.data);
          setProperties(propsRes.data.results || propsRes.data);
          setHouseTypes(typesRes.data.results || typesRes.data);
        }
      } catch (e) {
        console.error(e);
      }
    })();
    return () => { mounted = false; };
  }, [filterProp]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const handleCreate = async () => {
    if (!form.property || !form.unit_number || !form.house_type || !form.monthly_rent) {
      Alert.alert('Error', 'Property, unit number, house type, and rent are required');
      return;
    }
    setSubmitting(true);
    try {
      await landlordAPI.createUnit({
        ...form,
        property: parseInt(form.property),
        house_type: parseInt(form.house_type),
        bedrooms: parseInt(form.bedrooms),
        bathrooms: parseInt(form.bathrooms),
        floor: parseInt(form.floor),
        monthly_rent: parseFloat(form.monthly_rent),
        deposit: form.deposit ? parseFloat(form.deposit) : null,
      });
      setModalVisible(false);
      setForm(EMPTY_FORM);
      await fetchData();
      Alert.alert('Success', 'Unit created');
    } catch (e) {
      Alert.alert('Error', e.response?.data?.detail || e.response?.data?.error || 'Failed to create unit');
    } finally {
      setSubmitting(false);
    }
  };

  const propName = (id) => {
    const p = properties.find((x) => x.id === id);
    return p ? p.name : '';
  };

  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate('UnitDetail', { id: item.id })}
    >
      <View style={styles.cardTop}>
        <View style={{ flex: 1 }}>
          <Text style={styles.cardTitle}>{item.unit_number} · {propName(item.property)}</Text>
          <Text style={styles.cardSub}>
            {item.house_type_name} · {item.bedrooms}BR · {item.bathrooms}BA
          </Text>
          <Text style={styles.cardRent}>KES {item.monthly_rent}/mo</Text>
        </View>
        <View style={[styles.statusBadge, item.status === 'vacant' ? styles.vacantBadge : styles.occupiedBadge]}>
          <Text style={[styles.statusText, item.status === 'vacant' ? styles.vacantText : styles.occupiedText]}>
            {item.status.toUpperCase()}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <ScreenHeader
        title="Units"
        right={
          <TouchableOpacity style={styles.addBtn} onPress={() => setModalVisible(true)}>
            <Ionicons name="add-circle-outline" size={24} color="#fff" />
          </TouchableOpacity>
        }
      />

      {properties.length > 0 && (
        <View style={styles.filterRow}>
          {[{ id: '', name: 'All' }, ...properties].map((p) => (
            <TouchableOpacity
              key={p.id || 'all'}
              style={[styles.filterBtn, filterProp === p.id && styles.filterActive]}
              onPress={() => setFilterProp(p.id)}
            >
              <Text style={[styles.filterText, filterProp === p.id && styles.filterTextActive]}>
                {p.name}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <FlatList
        data={units}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="layers-outline" size={48} color="#ccc" />
            <Text style={styles.emptyText}>No units found</Text>
          </View>
        }
      />

      <BottomModal visible={modalVisible} onClose={() => setModalVisible(false)} title="Add Unit">
        <Text style={styles.label}>Property *</Text>
        <View style={styles.chipRow}>
          {properties.map((p) => (
            <TouchableOpacity
              key={p.id}
              style={[styles.chip, form.property === String(p.id) && styles.chipActive]}
              onPress={() => setForm({ ...form, property: String(p.id) })}
            >
              <Text style={[styles.chipText, form.property === String(p.id) && styles.chipTextActive]}>{p.name}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <Field label="Unit Number *" value={form.unit_number} onChangeText={(v) => setForm({ ...form, unit_number: v })} placeholder="e.g. B2-01" />

        <Text style={styles.label}>House Type *</Text>
        <View style={styles.chipRow}>
          {houseTypes.map((ht) => (
            <TouchableOpacity
              key={ht.id}
              style={[styles.chip, form.house_type === String(ht.id) && styles.chipActive]}
              onPress={() => setForm({ ...form, house_type: String(ht.id) })}
            >
              <Text style={[styles.chipText, form.house_type === String(ht.id) && styles.chipTextActive]}>{ht.name}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <Field label="Monthly Rent (KES) *" value={form.monthly_rent} onChangeText={(v) => setForm({ ...form, monthly_rent: v })} keyboardType="numeric" />
        <Field label="Deposit (KES)" value={form.deposit} onChangeText={(v) => setForm({ ...form, deposit: v })} keyboardType="numeric" />
        <Field label="Bedrooms" value={form.bedrooms} onChangeText={(v) => setForm({ ...form, bedrooms: v })} keyboardType="numeric" />
        <Field label="Bathrooms" value={form.bathrooms} onChangeText={(v) => setForm({ ...form, bathrooms: v })} keyboardType="numeric" />
        <Field label="Floor" value={form.floor} onChangeText={(v) => setForm({ ...form, floor: v })} keyboardType="numeric" />
        <Field label="Description" value={form.description} onChangeText={(v) => setForm({ ...form, description: v })} multiline numberOfLines={3} />
        <SubmitBar onCancel={() => setModalVisible(false)} onSubmit={handleCreate} submitting={submitting} submitLabel="Create" />
      </BottomModal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  addBtn: { padding: 4 },
  filterRow: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 12, paddingVertical: 8 },
  filterBtn: {
    paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16,
    borderWidth: 1, borderColor: '#ddd', marginRight: 8, marginBottom: 6,
  },
  filterActive: { backgroundColor: '#E65100', borderColor: '#E65100' },
  filterText: { fontSize: 12, color: '#666' },
  filterTextActive: { color: '#fff' },
  list: { padding: 12 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 10, elevation: 2,
  },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { fontSize: 16, fontWeight: 'bold', color: '#333' },
  cardSub: { fontSize: 13, color: '#888', marginTop: 4 },
  cardRent: { fontSize: 14, fontWeight: '600', color: '#E65100', marginTop: 4 },
  statusBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  vacantBadge: { backgroundColor: '#FFF3E0' },
  occupiedBadge: { backgroundColor: '#E8F5E9' },
  statusText: { fontSize: 10, fontWeight: 'bold' },
  vacantText: { color: '#E65100' },
  occupiedText: { color: '#2E7D32' },
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

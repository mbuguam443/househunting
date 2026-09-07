import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, StyleSheet, Alert, TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { landlordAPI } from '../services/api';
import { ScreenHeader, BottomModal, Field, SubmitBar } from '../components/UI';

export default function UnitDetailScreen({ route, navigation }) {
  const { id } = route.params;
  const [unit, setUnit] = useState(null);
  const [houseTypes, setHouseTypes] = useState([]);
  const [editVisible, setEditVisible] = useState(false);
  const [form, setForm] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    try {
      const [unitRes, typesRes] = await Promise.all([
        landlordAPI.getUnit(id),
        landlordAPI.getHouseTypes(),
      ]);
      setUnit(unitRes.data);
      setHouseTypes(typesRes.data.results || typesRes.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => { fetchData(); }, [id]);

  const openEdit = () => {
    setForm({
      unit_number: unit.unit_number,
      house_type: String(unit.house_type),
      monthly_rent: String(unit.monthly_rent),
      deposit: unit.deposit ? String(unit.deposit) : '',
      bedrooms: String(unit.bedrooms),
      bathrooms: String(unit.bathrooms),
      floor: String(unit.floor),
      description: unit.description || '',
    });
    setEditVisible(true);
  };

  const handleUpdate = async () => {
    setSubmitting(true);
    try {
      await landlordAPI.updateUnit(id, {
        ...form,
        house_type: parseInt(form.house_type),
        bedrooms: parseInt(form.bedrooms),
        bathrooms: parseInt(form.bathrooms),
        floor: parseInt(form.floor),
        monthly_rent: parseFloat(form.monthly_rent),
        deposit: form.deposit ? parseFloat(form.deposit) : null,
      });
      setEditVisible(false);
      await fetchData();
      Alert.alert('Success', 'Unit updated');
    } catch (e) {
      Alert.alert('Error', 'Failed to update');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = () => {
    Alert.alert('Delete Unit', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete', style: 'destructive',
        onPress: async () => {
          try {
            await landlordAPI.deleteUnit(id);
            navigation.goBack();
          } catch (e) {
            Alert.alert('Error', 'Failed to delete');
          }
        },
      },
    ]);
  };

  if (!unit) {
    return <View style={styles.center}><Text>Loading...</Text></View>;
  }

  return (
    <>
      <ScrollView style={styles.container}>
        <ScreenHeader
          title={unit.unit_number}
          onBack={() => navigation.goBack()}
          right={
            <>
              <TouchableOpacity onPress={openEdit}>
                <Ionicons name="create-outline" size={22} color="#fff" />
              </TouchableOpacity>
              <TouchableOpacity onPress={handleDelete} style={{ marginLeft: 14 }}>
                <Ionicons name="trash-outline" size={22} color="#fff" />
              </TouchableOpacity>
            </>
          }
        />

        <View style={styles.badgeWrap}>
          <View style={[styles.statusBadge, unit.status === 'vacant' ? styles.vacantBadge : styles.occupiedBadge]}>
            <Text style={[styles.statusText, unit.status === 'vacant' ? styles.vacantText : styles.occupiedText]}>
              {unit.status.toUpperCase()}
            </Text>
          </View>
        </View>

        <View style={styles.card}>
          <InfoRow label="Property" value={unit.property_name} />
          <InfoRow label="House Type" value={unit.house_type_name} />
          <InfoRow label="Bedrooms" value={String(unit.bedrooms)} />
          <InfoRow label="Bathrooms" value={String(unit.bathrooms)} />
          <InfoRow label="Floor" value={String(unit.floor)} />
          <InfoRow label="Monthly Rent" value={`KES ${unit.monthly_rent}`} />
          <InfoRow label="Deposit" value={unit.deposit ? `KES ${unit.deposit}` : '—'} />
        </View>

        {unit.description ? (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Description</Text>
            <Text style={styles.desc}>{unit.description}</Text>
          </View>
        ) : null}

        {unit.amenities && (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Amenities</Text>
            <View style={styles.amenityRow}>
              {Object.entries(unit.amenities).filter(([k, v]) => v).map(([k]) => (
                <View key={k} style={styles.amenityTag}>
                  <Ionicons name="checkmark-circle" size={14} color="#2E7D32" />
                  <Text style={styles.amenityText}>{k.charAt(0).toUpperCase() + k.slice(1)}</Text>
                </View>
              ))}
            </View>
          </View>
        )}
      </ScrollView>

      <BottomModal visible={editVisible} onClose={() => setEditVisible(false)} title="Edit Unit">
        <Field label="Unit Number" value={form.unit_number} onChangeText={(v) => setForm({ ...form, unit_number: v })} />
        <Text style={styles.formLabel}>House Type</Text>
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
        <Field label="Monthly Rent (KES)" value={form.monthly_rent} onChangeText={(v) => setForm({ ...form, monthly_rent: v })} keyboardType="numeric" />
        <Field label="Deposit (KES)" value={form.deposit} onChangeText={(v) => setForm({ ...form, deposit: v })} keyboardType="numeric" />
        <Field label="Bedrooms" value={form.bedrooms} onChangeText={(v) => setForm({ ...form, bedrooms: v })} keyboardType="numeric" />
        <Field label="Bathrooms" value={form.bathrooms} onChangeText={(v) => setForm({ ...form, bathrooms: v })} keyboardType="numeric" />
        <Field label="Floor" value={form.floor} onChangeText={(v) => setForm({ ...form, floor: v })} keyboardType="numeric" />
        <Field label="Description" value={form.description} onChangeText={(v) => setForm({ ...form, description: v })} multiline />
        <SubmitBar onCancel={() => setEditVisible(false)} onSubmit={handleUpdate} submitting={submitting} submitLabel="Save" />
      </BottomModal>
    </>
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
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  badgeWrap: { padding: 12, paddingBottom: 0 },
  statusBadge: { alignSelf: 'flex-start', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 10 },
  vacantBadge: { backgroundColor: '#FFF3E0' },
  occupiedBadge: { backgroundColor: '#E8F5E9' },
  statusText: { fontSize: 11, fontWeight: 'bold' },
  vacantText: { color: '#E65100' },
  occupiedText: { color: '#2E7D32' },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16,
    margin: 12, marginBottom: 0, elevation: 2,
  },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 12, color: '#333' },
  infoRow: {
    flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8,
    borderBottomWidth: 1, borderBottomColor: '#F0F0F0',
  },
  infoLabel: { fontSize: 14, color: '#888' },
  infoValue: { fontSize: 14, fontWeight: '600', color: '#333' },
  desc: { fontSize: 14, color: '#555', lineHeight: 22 },
  amenityRow: { flexDirection: 'row', flexWrap: 'wrap' },
  amenityTag: { flexDirection: 'row', alignItems: 'center', marginRight: 14, marginBottom: 8 },
  amenityText: { fontSize: 13, color: '#333', marginLeft: 4 },
  formLabel: { fontSize: 14, fontWeight: '600', marginBottom: 8, color: '#333' },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 16 },
  chip: {
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8,
    borderWidth: 1, borderColor: '#ddd', marginRight: 8, marginBottom: 8,
  },
  chipActive: { backgroundColor: '#E65100', borderColor: '#E65100' },
  chipText: { fontSize: 13, color: '#666' },
  chipTextActive: { color: '#fff' },
});

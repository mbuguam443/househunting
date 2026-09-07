import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, StyleSheet, Alert, TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { landlordAPI } from '../services/api';
import { ScreenHeader, BottomModal, Field, SubmitBar } from '../components/UI';

export default function PropertyDetailScreen({ route, navigation }) {
  const { id } = route.params;
  const [property, setProperty] = useState(null);
  const [units, setUnits] = useState([]);
  const [editVisible, setEditVisible] = useState(false);
  const [form, setForm] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    try {
      const [propRes, unitsRes] = await Promise.all([
        landlordAPI.getProperty(id),
        landlordAPI.getUnits(id),
      ]);
      setProperty(propRes.data);
      setUnits(unitsRes.data.results || unitsRes.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => { fetchData(); }, [id]);

  const openEdit = () => {
    setForm({
      name: property.name, description: property.description,
      county: property.county, town: property.town, estate: property.estate,
      address: property.address, water_rate: String(property.water_rate),
      electricity_rate: String(property.electricity_rate), trash_rate: String(property.trash_rate),
    });
    setEditVisible(true);
  };

  const handleUpdate = async () => {
    setSubmitting(true);
    try {
      await landlordAPI.updateProperty(id, form);
      setEditVisible(false);
      await fetchData();
      Alert.alert('Success', 'Property updated');
    } catch (e) {
      Alert.alert('Error', 'Failed to update');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = () => {
    Alert.alert('Delete Property', 'Are you sure? This will delete all units.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete', style: 'destructive',
        onPress: async () => {
          try {
            await landlordAPI.deleteProperty(id);
            navigation.goBack();
          } catch (e) {
            Alert.alert('Error', 'Failed to delete');
          }
        },
      },
    ]);
  };

  if (!property) {
    return <View style={styles.center}><Text>Loading...</Text></View>;
  }

  return (
    <>
      <ScrollView style={styles.container}>
        <ScreenHeader
          title={property.name}
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

        <View style={styles.card}>
          <InfoRow label="County" value={property.county} />
          <InfoRow label="Town" value={property.town} />
          <InfoRow label="Estate" value={property.estate || '—'} />
          <InfoRow label="Units" value={`${property.total_units} (${property.vacant_units} vacant)`} />
        </View>

        {property.description ? (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Description</Text>
            <Text style={styles.desc}>{property.description}</Text>
          </View>
        ) : null}

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Units ({units.length})</Text>
          {units.length === 0 ? (
            <Text style={styles.emptyText}>No units yet. Add units from the Properties list.</Text>
          ) : (
            units.map((u) => (
              <TouchableOpacity key={u.id} style={styles.unitItem} onPress={() => navigation.navigate('UnitDetail', { id: u.id })}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.unitTitle}>
                    {u.unit_number} · {u.bedrooms}BR · {u.house_type_name}
                  </Text>
                  <Text style={styles.unitSub}>KES {u.monthly_rent}/mo</Text>
                </View>
                <View style={[styles.statusBadge, u.status === 'vacant' ? styles.vacantBadge : styles.occupiedBadge]}>
                  <Text style={[styles.statusText, u.status === 'vacant' ? styles.vacantText : styles.occupiedText]}>
                    {u.status.toUpperCase()}
                  </Text>
                </View>
              </TouchableOpacity>
            ))
          )}
        </View>
      </ScrollView>

      <BottomModal visible={editVisible} onClose={() => setEditVisible(false)} title="Edit Property">
        <Field label="Name *" value={form.name} onChangeText={(v) => setForm({ ...form, name: v })} />
        <Field label="County *" value={form.county} onChangeText={(v) => setForm({ ...form, county: v })} />
        <Field label="Town *" value={form.town} onChangeText={(v) => setForm({ ...form, town: v })} />
        <Field label="Estate" value={form.estate} onChangeText={(v) => setForm({ ...form, estate: v })} />
        <Field label="Address" value={form.address} onChangeText={(v) => setForm({ ...form, address: v })} />
        <Field label="Description" value={form.description} onChangeText={(v) => setForm({ ...form, description: v })} multiline />
        <Field label="Water Rate" value={form.water_rate} onChangeText={(v) => setForm({ ...form, water_rate: v })} keyboardType="numeric" />
        <Field label="Electricity Rate" value={form.electricity_rate} onChangeText={(v) => setForm({ ...form, electricity_rate: v })} keyboardType="numeric" />
        <Field label="Trash Rate" value={form.trash_rate} onChangeText={(v) => setForm({ ...form, trash_rate: v })} keyboardType="numeric" />
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
  emptyText: { fontSize: 14, color: '#999', textAlign: 'center', padding: 10 },
  unitItem: {
    flexDirection: 'row', alignItems: 'center', paddingVertical: 10,
    borderBottomWidth: 1, borderBottomColor: '#F0F0F0',
  },
  unitTitle: { fontSize: 15, fontWeight: '600', color: '#333' },
  unitSub: { fontSize: 13, color: '#888', marginTop: 2 },
  statusBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  vacantBadge: { backgroundColor: '#FFF3E0' },
  occupiedBadge: { backgroundColor: '#E8F5E9' },
  statusText: { fontSize: 10, fontWeight: 'bold' },
  vacantText: { color: '#E65100' },
  occupiedText: { color: '#2E7D32' },
});

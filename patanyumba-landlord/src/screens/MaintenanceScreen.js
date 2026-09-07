import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  RefreshControl, Alert, TextInput,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { landlordAPI } from '../services/api';
import { ScreenHeader, BottomModal } from '../components/UI';

const STATUS_COLORS = {
  submitted: '#FF9800',
  in_progress: '#2196F3',
  resolved: '#4CAF50',
  closed: '#999',
};

const STATUS_SELECT = ['submitted', 'in_progress', 'resolved', 'closed'];

export default function MaintenanceScreen() {
  const [requests, setRequests] = useState([]);
  const [filter, setFilter] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [editId, setEditId] = useState(null);
  const [editStatus, setEditStatus] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await landlordAPI.getMaintenance(filter);
      setRequests(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  }, [filter]);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await landlordAPI.getMaintenance(filter);
        if (mounted) setRequests(res.data.results || res.data);
      } catch (e) {
        console.error(e);
      }
    })();
    return () => { mounted = false; };
  }, [filter]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const openEdit = (item) => {
    setEditId(item.id);
    setEditStatus(item.status);
    setNotes(item.landlord_notes || '');
  };

  const handleUpdate = async () => {
    setSubmitting(true);
    try {
      const payload = { status: editStatus };
      if (notes) payload.landlord_notes = notes;
      await landlordAPI.updateMaintenance(editId, payload);
      setEditId(null);
      await fetchData();
      Alert.alert('Success', 'Request updated');
    } catch (e) {
      Alert.alert('Error', 'Failed to update');
    } finally {
      setSubmitting(false);
    }
  };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{item.title}</Text>
        <View style={[styles.badge, { backgroundColor: (STATUS_COLORS[item.status] || '#999') + '20' }]}>
          <Text style={[styles.badgeText, { color: STATUS_COLORS[item.status] || '#999' }]}>
            {item.status.replace('_', ' ').toUpperCase()}
          </Text>
        </View>
      </View>
      <Text style={styles.cardDesc}>{item.description}</Text>
      <View style={styles.cardMeta}>
        <Text style={styles.metaText}>{item.tenant_name}</Text>
        <Text style={styles.metaText}>Unit {item.unit_number}</Text>
        <Text style={styles.metaText}>Pri: {item.priority}</Text>
      </View>
      {item.landlord_notes ? <Text style={styles.notes}>Notes: {item.landlord_notes}</Text> : null}
      <TouchableOpacity style={styles.updateBtn} onPress={() => openEdit(item)}>
        <Ionicons name="create-outline" size={16} color="#0D47A1" />
        <Text style={styles.updateBtnText}>Update</Text>
      </TouchableOpacity>
    </View>
  );

  const filters = [
    { label: 'All', value: '' },
    { label: 'Open', value: 'submitted' },
    { label: 'In Progress', value: 'in_progress' },
    { label: 'Resolved', value: 'resolved' },
  ];

  return (
    <View style={styles.container}>
      <ScreenHeader title="Maintenance" />
      <View style={styles.filterRow}>
        {filters.map((f) => (
          <TouchableOpacity
            key={f.value}
            style={[styles.filterBtn, filter === f.value && styles.filterActive]}
            onPress={() => setFilter(f.value)}
          >
            <Text style={[styles.filterText, filter === f.value && styles.filterTextActive]}>{f.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <FlatList
        data={requests}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="build-outline" size={48} color="#ccc" />
            <Text style={styles.emptyText}>No maintenance requests</Text>
          </View>
        }
      />

      <BottomModal visible={editId !== null} onClose={() => setEditId(null)} title="Update Request">
        <Text style={styles.label}>Status</Text>
        <View style={styles.statusRow}>
          {STATUS_SELECT.map((s) => (
            <TouchableOpacity
              key={s}
              style={[styles.statusBtn, editStatus === s && styles.statusBtnActive]}
              onPress={() => setEditStatus(s)}
            >
              <Text style={[styles.statusBtnText, editStatus === s && styles.statusBtnTextActive]}>
                {s.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
        <Text style={styles.label}>Landlord Notes</Text>
        <TextInput
          style={styles.notesInput}
          placeholder="Add response/notes for the tenant..."
          placeholderTextColor="#999"
          value={notes}
          onChangeText={setNotes}
          multiline
          numberOfLines={3}
        />
        <TouchableOpacity
          style={[styles.bigBtn, submitting && { opacity: 0.5 }]}
          onPress={handleUpdate}
          disabled={submitting}
        >
          <Text style={styles.bigBtnText}>{submitting ? 'Saving...' : 'Save Updates'}</Text>
        </TouchableOpacity>
      </BottomModal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  filterRow: { flexDirection: 'row', paddingHorizontal: 12, paddingVertical: 8 },
  filterBtn: {
    paddingHorizontal: 14, paddingVertical: 7, borderRadius: 18,
    borderWidth: 1, borderColor: '#ddd', marginRight: 8,
  },
  filterActive: { backgroundColor: '#E65100', borderColor: '#E65100' },
  filterText: { fontSize: 12, color: '#666' },
  filterTextActive: { color: '#fff' },
  list: { padding: 12 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 10, elevation: 2,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { fontSize: 16, fontWeight: 'bold', color: '#333', flex: 1 },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8, marginLeft: 8 },
  badgeText: { fontSize: 10, fontWeight: 'bold' },
  cardDesc: { fontSize: 14, color: '#666', marginTop: 8 },
  cardMeta: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 8 },
  metaText: { fontSize: 12, color: '#888', backgroundColor: '#F0F0F0', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3, marginRight: 8, marginTop: 4 },
  notes: { fontSize: 13, color: '#0D47A1', marginTop: 8, fontStyle: 'italic' },
  updateBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: '#0D47A1', borderRadius: 8, padding: 10, marginTop: 12,
  },
  updateBtnText: { color: '#0D47A1', fontWeight: 'bold', marginLeft: 6 },
  empty: { alignItems: 'center', marginTop: 60 },
  emptyText: { fontSize: 16, color: '#999', marginTop: 12 },
  label: { fontSize: 14, fontWeight: '600', marginBottom: 8, color: '#333' },
  statusRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 16 },
  statusBtn: {
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8,
    borderWidth: 1, borderColor: '#ddd', marginRight: 8, marginBottom: 8,
  },
  statusBtnActive: { backgroundColor: '#E65100', borderColor: '#E65100' },
  statusBtnText: { fontSize: 13, color: '#666' },
  statusBtnTextActive: { color: '#fff' },
  bigBtn: { backgroundColor: '#E65100', borderRadius: 8, padding: 14, alignItems: 'center' },
  bigBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  notesInput: {
    backgroundColor: '#F5F5F5', borderRadius: 8, padding: 12,
    fontSize: 16, color: '#333', marginBottom: 16, height: 80, textAlignVertical: 'top',
  },
});
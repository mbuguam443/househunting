import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TextInput, TouchableOpacity,
  StyleSheet, Alert, RefreshControl, Modal, KeyboardAvoidingView, Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { tenantAPI } from '../services/api';

const PRIORITY_OPTIONS = ['low', 'medium', 'high', 'urgent'];
const STATUS_COLORS = {
  submitted: '#FF9800',
  in_progress: '#2196F3',
  resolved: '#4CAF50',
  closed: '#999',
};

export default function MaintenanceScreen() {
  const [requests, setRequests] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  const [submitting, setSubmitting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await tenantAPI.getMaintenance();
      setRequests(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await tenantAPI.getMaintenance();
        if (mounted) setRequests(res.data.results || res.data);
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

  const handleSubmit = async () => {
    if (!title || !description) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }
    setSubmitting(true);
    try {
      await tenantAPI.submitMaintenance({ title, description, priority });
      setModalVisible(false);
      setTitle('');
      setDescription('');
      setPriority('medium');
      await fetchData();
      Alert.alert('Success', 'Maintenance request submitted');
    } catch (e) {
      Alert.alert('Error', e.response?.data?.error || 'Failed to submit');
    } finally {
      setSubmitting(false);
    }
  };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{item.title}</Text>
        <View style={[styles.badge, { backgroundColor: STATUS_COLORS[item.status] + '20' }]}>
          <Text style={[styles.badgeText, { color: STATUS_COLORS[item.status] }]}>
            {item.status.replace('_', ' ').toUpperCase()}
          </Text>
        </View>
      </View>
      <Text style={styles.cardDesc}>{item.description}</Text>
      <View style={styles.cardFooter}>
        <Text style={styles.priority}>Priority: {item.priority}</Text>
        <Text style={styles.date}>{new Date(item.created_at).toLocaleDateString()}</Text>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Maintenance</Text>
        <TouchableOpacity style={styles.addBtn} onPress={() => setModalVisible(true)}>
          <Ionicons name="add-circle-outline" size={24} color="#fff" />
          <Text style={styles.addBtnText}>New</Text>
        </TouchableOpacity>
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

      <Modal visible={modalVisible} animationType="slide" transparent>
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>New Request</Text>
            <TextInput
              style={styles.input}
              placeholder="Title"
              placeholderTextColor="#999"
              value={title}
              onChangeText={setTitle}
            />
            <TextInput
              style={[styles.input, styles.textArea]}
              placeholder="Description"
              placeholderTextColor="#999"
              value={description}
              onChangeText={setDescription}
              multiline
              numberOfLines={4}
            />
            <Text style={styles.label}>Priority</Text>
            <View style={styles.priorityRow}>
              {PRIORITY_OPTIONS.map((p) => (
                <TouchableOpacity
                  key={p}
                  style={[styles.priorityBtn, priority === p && styles.priorityBtnActive]}
                  onPress={() => setPriority(p)}
                >
                  <Text style={[styles.priorityBtnText, priority === p && styles.priorityBtnTextActive]}>
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setModalVisible(false)}>
                <Text style={styles.cancelBtnText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.submitBtn, submitting && { opacity: 0.5 }]}
                onPress={handleSubmit}
                disabled={submitting}
              >
                <Text style={styles.submitBtnText}>
                  {submitting ? 'Submitting...' : 'Submit'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  header: {
    backgroundColor: '#1B5E20', padding: 20, paddingTop: 16,
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
  },
  headerTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  addBtn: { flexDirection: 'row', alignItems: 'center' },
  addBtnText: { color: '#fff', fontSize: 16, marginLeft: 4 },
  list: { padding: 16 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16,
    marginBottom: 12, elevation: 2,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { fontSize: 16, fontWeight: 'bold', color: '#333', flex: 1 },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8, marginLeft: 8 },
  badgeText: { fontSize: 10, fontWeight: 'bold' },
  cardDesc: { fontSize: 14, color: '#666', marginTop: 8, lineHeight: 20 },
  cardFooter: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 12 },
  priority: { fontSize: 12, color: '#888' },
  date: { fontSize: 12, color: '#888' },
  empty: { alignItems: 'center', marginTop: 60 },
  emptyText: { fontSize: 16, color: '#999', marginTop: 12 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContent: {
    backgroundColor: '#fff', borderTopLeftRadius: 20, borderTopRightRadius: 20,
    padding: 24, maxHeight: '80%',
  },
  modalTitle: { fontSize: 20, fontWeight: 'bold', marginBottom: 16, color: '#333' },
  input: {
    backgroundColor: '#F5F5F5', borderRadius: 8, padding: 12,
    fontSize: 16, marginBottom: 12, color: '#333',
  },
  textArea: { height: 100, textAlignVertical: 'top' },
  label: { fontSize: 14, fontWeight: '600', marginBottom: 8, color: '#333' },
  priorityRow: { flexDirection: 'row', marginBottom: 16 },
  priorityBtn: {
    flex: 1, padding: 10, borderRadius: 8, borderWidth: 1,
    borderColor: '#ddd', alignItems: 'center', marginRight: 8,
  },
  priorityBtnActive: { backgroundColor: '#1B5E20', borderColor: '#1B5E20' },
  priorityBtnText: { fontSize: 13, color: '#666' },
  priorityBtnTextActive: { color: '#fff' },
  modalActions: { flexDirection: 'row', justifyContent: 'flex-end' },
  cancelBtn: { padding: 12, marginRight: 12 },
  cancelBtnText: { fontSize: 16, color: '#666' },
  submitBtn: { backgroundColor: '#1B5E20', borderRadius: 8, paddingHorizontal: 24, padding: 12 },
  submitBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});

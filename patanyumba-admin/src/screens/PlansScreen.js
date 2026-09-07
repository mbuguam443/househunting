import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  RefreshControl, Alert, Modal, TextInput, KeyboardAvoidingView, Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { adminAPI } from '../services/api';

export default function PlansScreen() {
  const [plans, setPlans] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form, setForm] = useState({ name: '', amount: '', duration_days: '', description: '' });
  const [submitting, setSubmitting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await adminAPI.getPlans();
      setPlans(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await adminAPI.getPlans();
        if (mounted) setPlans(res.data.results || res.data);
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
    if (!form.name || !form.amount || !form.duration_days) {
      Alert.alert('Error', 'Name, amount, and duration required');
      return;
    }
    setSubmitting(true);
    try {
      await adminAPI.createPlan({
        name: form.name,
        amount: parseFloat(form.amount),
        duration_days: parseInt(form.duration_days),
        description: form.description,
      });
      setModalVisible(false);
      setForm({ name: '', amount: '', duration_days: '', description: '' });
      await fetchData();
    } catch (e) {
      Alert.alert('Error', 'Failed to create plan');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggle = async (id) => {
    try {
      await adminAPI.togglePlan(id);
      await fetchData();
    } catch (e) {
      Alert.alert('Error', 'Failed to toggle');
    }
  };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{item.name}</Text>
        <View style={[styles.badge, item.is_active ? styles.activeBadge : styles.inactiveBadge]}>
          <Text style={[styles.badgeText, item.is_active ? styles.activeText : styles.inactiveText]}>
            {item.is_active ? 'ACTIVE' : 'INACTIVE'}
          </Text>
        </View>
      </View>
      <Text style={styles.cardDetail}>KES {item.amount} | {item.duration_days} days</Text>
      {item.description ? <Text style={styles.cardDesc}>{item.description}</Text> : null}
      <TouchableOpacity style={styles.toggleBtn} onPress={() => handleToggle(item.id)}>
        <Text style={styles.toggleBtnText}>{item.is_active ? 'Deactivate' : 'Activate'}</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Subscription Plans</Text>
        <TouchableOpacity style={styles.addBtn} onPress={() => setModalVisible(true)}>
          <Ionicons name="add-circle-outline" size={24} color="#fff" />
          <Text style={styles.addBtnText}>Add</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={plans}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="card-outline" size={48} color="#ccc" />
            <Text style={styles.emptyText}>No plans yet</Text>
          </View>
        }
      />

      <Modal visible={modalVisible} animationType="slide" transparent>
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Create Plan</Text>
            <TextInput style={styles.input} placeholder="Plan Name" placeholderTextColor="#999" value={form.name} onChangeText={(v) => setForm({ ...form, name: v })} />
            <TextInput style={styles.input} placeholder="Amount (KES)" placeholderTextColor="#999" value={form.amount} onChangeText={(v) => setForm({ ...form, amount: v })} keyboardType="numeric" />
            <TextInput style={styles.input} placeholder="Duration (days)" placeholderTextColor="#999" value={form.duration_days} onChangeText={(v) => setForm({ ...form, duration_days: v })} keyboardType="numeric" />
            <TextInput style={styles.input} placeholder="Description (optional)" placeholderTextColor="#999" value={form.description} onChangeText={(v) => setForm({ ...form, description: v })} />
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setModalVisible(false)}>
                <Text style={styles.cancelBtnText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.submitBtn, submitting && { opacity: 0.5 }]} onPress={handleCreate} disabled={submitting}>
                <Text style={styles.submitBtnText}>{submitting ? 'Creating...' : 'Create'}</Text>
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
    backgroundColor: '#0D47A1', padding: 20, paddingTop: 16,
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
  },
  headerTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  addBtn: { flexDirection: 'row', alignItems: 'center' },
  addBtnText: { color: '#fff', fontSize: 16, marginLeft: 4 },
  list: { padding: 12 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16,
    marginBottom: 10, elevation: 2,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { fontSize: 18, fontWeight: 'bold', color: '#333' },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8 },
  activeBadge: { backgroundColor: '#E8F5E9' },
  inactiveBadge: { backgroundColor: '#FFF3E0' },
  badgeText: { fontSize: 10, fontWeight: 'bold' },
  activeText: { color: '#2E7D32' },
  inactiveText: { color: '#E65100' },
  cardDetail: { fontSize: 14, color: '#666', marginTop: 8 },
  cardDesc: { fontSize: 13, color: '#888', marginTop: 4 },
  toggleBtn: {
    marginTop: 12, borderWidth: 1, borderColor: '#0D47A1', borderRadius: 8,
    padding: 10, alignItems: 'center',
  },
  toggleBtnText: { color: '#0D47A1', fontWeight: 'bold' },
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
  modalActions: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: 8 },
  cancelBtn: { padding: 12, marginRight: 12 },
  cancelBtnText: { fontSize: 16, color: '#666' },
  submitBtn: { backgroundColor: '#0D47A1', borderRadius: 8, paddingHorizontal: 24, padding: 12 },
  submitBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});

import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TextInput, TouchableOpacity,
  StyleSheet, RefreshControl, Alert, Modal, KeyboardAvoidingView, Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { adminAPI } from '../services/api';

export default function LandlordsScreen({ navigation }) {
  const [landlords, setLandlords] = useState([]);
  const [search, setSearch] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form, setForm] = useState({ username: '', email: '', password: '', first_name: '', last_name: '', phone: '' });
  const [submitting, setSubmitting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await adminAPI.getLandlords(search);
      setLandlords(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  }, [search]);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await adminAPI.getLandlords(search);
        if (mounted) setLandlords(res.data.results || res.data);
      } catch (e) {
        console.error(e);
      }
    })();
    return () => { mounted = false; };
  }, [search]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const handleCreate = async () => {
    if (!form.username || !form.password) {
      Alert.alert('Error', 'Username and password required');
      return;
    }
    setSubmitting(true);
    try {
      await adminAPI.createLandlord(form);
      setModalVisible(false);
      setForm({ username: '', email: '', password: '', first_name: '', last_name: '', phone: '' });
      await fetchData();
      Alert.alert('Success', 'Landlord created');
    } catch (e) {
      Alert.alert('Error', e.response?.data?.error || 'Failed');
    } finally {
      setSubmitting(false);
    }
  };

  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate('LandlordDetail', { id: item.user.id })}
    >
      <View style={styles.cardRow}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {item.user.first_name ? item.user.first_name[0] : item.user.username[0]}
          </Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.cardTitle}>{item.user.full_name}</Text>
          <Text style={styles.cardSub}>@{item.user.username}</Text>
          <Text style={styles.cardSub}>{item.properties_count} properties | {item.units_count} units</Text>
        </View>
        <View style={styles.rightSection}>
          <View style={[styles.badge, item.subscription_status.status === 'active' ? styles.activeBadge : styles.inactiveBadge]}>
            <Text style={[styles.badgeText, item.subscription_status.status === 'active' ? styles.activeText : styles.inactiveText]}>
              {item.subscription_status.status.toUpperCase()}
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#999" />
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Landlords</Text>
        <TouchableOpacity style={styles.addBtn} onPress={() => setModalVisible(true)}>
          <Ionicons name="add-circle-outline" size={24} color="#fff" />
          <Text style={styles.addBtnText}>Add</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.searchBar}>
        <Ionicons name="search" size={20} color="#999" />
        <TextInput
          style={styles.searchInput}
          placeholder="Search landlords..."
          placeholderTextColor="#999"
          value={search}
          onChangeText={setSearch}
        />
      </View>

      <FlatList
        data={landlords}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="people-outline" size={48} color="#ccc" />
            <Text style={styles.emptyText}>No landlords found</Text>
          </View>
        }
      />

      <Modal visible={modalVisible} animationType="slide" transparent>
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Create Landlord</Text>
            {['username', 'email', 'password', 'first_name', 'last_name', 'phone'].map((field) => (
              <TextInput
                key={field}
                style={styles.input}
                placeholder={field.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                placeholderTextColor="#999"
                value={form[field]}
                onChangeText={(v) => setForm({ ...form, [field]: v })}
                secureTextEntry={field === 'password'}
                keyboardType={field === 'email' ? 'email-address' : field === 'phone' ? 'phone-pad' : 'default'}
              />
            ))}
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setModalVisible(false)}>
                <Text style={styles.cancelBtnText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.submitBtn, submitting && { opacity: 0.5 }]}
                onPress={handleCreate}
                disabled={submitting}
              >
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
  searchBar: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff',
    margin: 12, paddingHorizontal: 12, borderRadius: 8, elevation: 1,
  },
  searchInput: { flex: 1, padding: 10, fontSize: 16, color: '#333' },
  list: { padding: 12 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16,
    marginBottom: 10, elevation: 2,
  },
  cardRow: { flexDirection: 'row', alignItems: 'center' },
  avatar: {
    width: 44, height: 44, borderRadius: 22, backgroundColor: '#0D47A1',
    justifyContent: 'center', alignItems: 'center', marginRight: 12,
  },
  avatarText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  cardTitle: { fontSize: 16, fontWeight: 'bold', color: '#333' },
  cardSub: { fontSize: 12, color: '#888', marginTop: 2 },
  rightSection: { alignItems: 'flex-end' },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8 },
  activeBadge: { backgroundColor: '#E8F5E9' },
  inactiveBadge: { backgroundColor: '#FFF3E0' },
  badgeText: { fontSize: 10, fontWeight: 'bold' },
  activeText: { color: '#2E7D32' },
  inactiveText: { color: '#E65100' },
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

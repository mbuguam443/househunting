import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TextInput, TouchableOpacity,
  StyleSheet, RefreshControl, Alert, Modal, KeyboardAvoidingView, Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { adminAPI } from '../services/api';

const STATUS_OPTIONS = ['available', 'rented', 'withdrawn'];

export default function ListingsScreen() {
  const [listings, setListings] = useState([]);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form, setForm] = useState({
    title: '', description: '', county: '', town: '', estate: '',
    bedrooms: '1', bathrooms: '1', rent: '', contact_name: '', contact_phone: '',
    status: 'available', house_type: '',
  });
  const [houseTypes, setHouseTypes] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [listingsRes, typesRes] = await Promise.all([
        adminAPI.getListings(search, filter),
        adminAPI.getHouseTypes(),
      ]);
      setListings(listingsRes.data.results || listingsRes.data);
      setHouseTypes(typesRes.data.results || typesRes.data);
    } catch (e) {
      console.error(e);
    }
  }, [search, filter]);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [listingsRes, typesRes] = await Promise.all([
          adminAPI.getListings(search, filter),
          adminAPI.getHouseTypes(),
        ]);
        if (mounted) {
          setListings(listingsRes.data.results || listingsRes.data);
          setHouseTypes(typesRes.data.results || typesRes.data);
        }
      } catch (e) {
        console.error(e);
      }
    })();
    return () => { mounted = false; };
  }, [search, filter]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const openCreate = () => {
    setEditingId(null);
    setForm({
      title: '', description: '', county: '', town: '', estate: '',
      bedrooms: '1', bathrooms: '1', rent: '', contact_name: '', contact_phone: '',
      status: 'available', house_type: '',
    });
    setModalVisible(true);
  };

  const openEdit = (item) => {
    setEditingId(item.id);
    setForm({
      title: item.title, description: item.description || '',
      county: item.county, town: item.town, estate: item.estate || '',
      bedrooms: String(item.bedrooms), bathrooms: String(item.bathrooms),
      rent: String(item.rent), contact_name: item.contact_name || '',
      contact_phone: item.contact_phone || '',
      status: item.status, house_type: String(item.house_type),
    });
    setModalVisible(true);
  };

  const handleSave = async () => {
    if (!form.title || !form.county || !form.town || !form.rent || !form.house_type) {
      Alert.alert('Error', 'Title, county, town, rent, and house type are required');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        bedrooms: parseInt(form.bedrooms),
        bathrooms: parseInt(form.bathrooms),
        rent: parseFloat(form.rent),
        house_type: parseInt(form.house_type),
      };
      if (editingId) {
        await adminAPI.updateListing(editingId, payload);
      } else {
        await adminAPI.createListing(payload);
      }
      setModalVisible(false);
      setEditingId(null);
      await fetchData();
    } catch (e) {
      Alert.alert('Error', 'Failed to save listing');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = (id) => {
    Alert.alert('Delete Listing', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete', style: 'destructive',
        onPress: async () => {
          try {
            await adminAPI.deleteListing(id);
            await fetchData();
          } catch (e) {
            Alert.alert('Error', 'Failed to delete');
          }
        },
      },
    ]);
  };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle} numberOfLines={1}>{item.title}</Text>
        <View style={[styles.badge, item.status === 'available' ? styles.availableBadge : styles.otherBadge]}>
          <Text style={[styles.badgeText, item.status === 'available' ? styles.availableText : styles.otherText]}>
            {item.status.toUpperCase()}
          </Text>
        </View>
      </View>
      <Text style={styles.cardLocation}>{item.county}, {item.town}</Text>
      <Text style={styles.cardDetail}>
        {item.bedrooms}BR | {item.bathrooms}BA | KES {item.rent}/mo
      </Text>
      <Text style={styles.cardType}>{item.house_type_name}</Text>
      <View style={styles.cardActions}>
        <TouchableOpacity style={styles.editBtn} onPress={() => openEdit(item)}>
          <Ionicons name="create-outline" size={16} color="#0D47A1" />
          <Text style={styles.editBtnText}>Edit</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.deleteBtn} onPress={() => handleDelete(item.id)}>
          <Ionicons name="trash-outline" size={16} color="#D32F2F" />
          <Text style={styles.deleteBtnText}>Delete</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Listings</Text>
        <TouchableOpacity style={styles.addBtn} onPress={openCreate}>
          <Ionicons name="add-circle-outline" size={24} color="#fff" />
          <Text style={styles.addBtnText}>Add</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.searchBar}>
        <Ionicons name="search" size={20} color="#999" />
        <TextInput
          style={styles.searchInput}
          placeholder="Search listings..."
          placeholderTextColor="#999"
          value={search}
          onChangeText={setSearch}
        />
      </View>

      <View style={styles.filterRow}>
        {['', 'available', 'rented', 'withdrawn'].map((f) => (
          <TouchableOpacity
            key={f}
            style={[styles.filterBtn, filter === f && styles.filterActive]}
            onPress={() => setFilter(f)}
          >
            <Text style={[styles.filterText, filter === f && styles.filterTextActive]}>
              {f || 'All'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={listings}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="home-outline" size={48} color="#ccc" />
            <Text style={styles.emptyText}>No listings found</Text>
          </View>
        }
      />

      <Modal visible={modalVisible} animationType="slide" transparent>
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>{editingId ? 'Edit Listing' : 'Create Listing'}</Text>
            <TextInput style={styles.input} placeholder="Title *" placeholderTextColor="#999" value={form.title} onChangeText={(v) => setForm({ ...form, title: v })} />
            <TextInput style={styles.input} placeholder="Description" placeholderTextColor="#999" value={form.description} onChangeText={(v) => setForm({ ...form, description: v })} multiline />
            <TextInput style={styles.input} placeholder="County *" placeholderTextColor="#999" value={form.county} onChangeText={(v) => setForm({ ...form, county: v })} />
            <TextInput style={styles.input} placeholder="Town *" placeholderTextColor="#999" value={form.town} onChangeText={(v) => setForm({ ...form, town: v })} />
            <TextInput style={styles.input} placeholder="Estate" placeholderTextColor="#999" value={form.estate} onChangeText={(v) => setForm({ ...form, estate: v })} />
            <TextInput style={styles.input} placeholder="Rent (KES) *" placeholderTextColor="#999" value={form.rent} onChangeText={(v) => setForm({ ...form, rent: v })} keyboardType="numeric" />
            <TextInput style={styles.input} placeholder="Bedrooms" placeholderTextColor="#999" value={form.bedrooms} onChangeText={(v) => setForm({ ...form, bedrooms: v })} keyboardType="numeric" />
            <TextInput style={styles.input} placeholder="Bathrooms" placeholderTextColor="#999" value={form.bathrooms} onChangeText={(v) => setForm({ ...form, bathrooms: v })} keyboardType="numeric" />
            <TextInput style={styles.input} placeholder="Contact Name" placeholderTextColor="#999" value={form.contact_name} onChangeText={(v) => setForm({ ...form, contact_name: v })} />
            <TextInput style={styles.input} placeholder="Contact Phone" placeholderTextColor="#999" value={form.contact_phone} onChangeText={(v) => setForm({ ...form, contact_phone: v })} keyboardType="phone-pad" />

            <Text style={styles.label}>House Type *</Text>
            <View style={styles.typeRow}>
              {houseTypes.map((ht) => (
                <TouchableOpacity
                  key={ht.id}
                  style={[styles.typeBtn, form.house_type === ht.id.toString() && styles.typeActive]}
                  onPress={() => setForm({ ...form, house_type: ht.id.toString() })}
                >
                  <Text style={[styles.typeText, form.house_type === ht.id.toString() && styles.typeTextActive]}>
                    {ht.name}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.statusRow}>
              {STATUS_OPTIONS.map((s) => (
                <TouchableOpacity
                  key={s}
                  style={[styles.typeBtn, form.status === s && styles.typeActive]}
                  onPress={() => setForm({ ...form, status: s })}
                >
                  <Text style={[styles.typeText, form.status === s && styles.typeTextActive]}>
                    {s.toUpperCase()}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => { setModalVisible(false); setEditingId(null); }}>
                <Text style={styles.cancelBtnText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.submitBtn, submitting && { opacity: 0.5 }]} onPress={handleSave} disabled={submitting}>
                <Text style={styles.submitBtnText}>{submitting ? 'Saving...' : editingId ? 'Save Changes' : 'Create'}</Text>
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
    margin: 12, marginBottom: 0, paddingHorizontal: 12, borderRadius: 8, elevation: 1,
  },
  searchInput: { flex: 1, padding: 10, fontSize: 16, color: '#333' },
  filterRow: { flexDirection: 'row', paddingHorizontal: 12, paddingVertical: 8 },
  filterBtn: {
    paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16,
    borderWidth: 1, borderColor: '#ddd', marginRight: 8,
  },
  filterActive: { backgroundColor: '#0D47A1', borderColor: '#0D47A1' },
  filterText: { fontSize: 12, color: '#666' },
  filterTextActive: { color: '#fff' },
  list: { padding: 12 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 10, elevation: 2,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { fontSize: 16, fontWeight: 'bold', color: '#333', flex: 1 },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8, marginLeft: 8 },
  availableBadge: { backgroundColor: '#E8F5E9' },
  otherBadge: { backgroundColor: '#FFF3E0' },
  badgeText: { fontSize: 10, fontWeight: 'bold' },
  availableText: { color: '#2E7D32' },
  otherText: { color: '#E65100' },
  cardLocation: { fontSize: 13, color: '#666', marginTop: 4 },
  cardDetail: { fontSize: 13, color: '#888', marginTop: 2 },
  cardType: { fontSize: 12, color: '#0D47A1', marginTop: 4 },
  cardActions: { flexDirection: 'row', marginTop: 12 },
  deleteBtn: { flexDirection: 'row', alignItems: 'center', marginLeft: 16 },
  deleteBtnText: { color: '#D32F2F', fontSize: 13, marginLeft: 4 },
  editBtn: { flexDirection: 'row', alignItems: 'center' },
  editBtnText: { color: '#0D47A1', fontSize: 13, marginLeft: 4 },
  statusRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 16 },
  empty: { alignItems: 'center', marginTop: 60 },
  emptyText: { fontSize: 16, color: '#999', marginTop: 12 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContent: {
    backgroundColor: '#fff', borderTopLeftRadius: 20, borderTopRightRadius: 20,
    padding: 24, maxHeight: '85%',
  },
  modalTitle: { fontSize: 20, fontWeight: 'bold', marginBottom: 16, color: '#333' },
  input: {
    backgroundColor: '#F5F5F5', borderRadius: 8, padding: 12,
    fontSize: 16, marginBottom: 12, color: '#333',
  },
  label: { fontSize: 14, fontWeight: '600', marginBottom: 8, color: '#333' },
  typeRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 16 },
  typeBtn: {
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8,
    borderWidth: 1, borderColor: '#ddd', marginRight: 8, marginBottom: 8,
  },
  typeActive: { backgroundColor: '#0D47A1', borderColor: '#0D47A1' },
  typeText: { fontSize: 13, color: '#666' },
  typeTextActive: { color: '#fff' },
  modalActions: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: 8 },
  cancelBtn: { padding: 12, marginRight: 12 },
  cancelBtnText: { fontSize: 16, color: '#666' },
  submitBtn: { backgroundColor: '#0D47A1', borderRadius: 8, paddingHorizontal: 24, padding: 12 },
  submitBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});

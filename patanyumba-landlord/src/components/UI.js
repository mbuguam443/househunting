import React from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Modal, ScrollView, KeyboardAvoidingView, Platform, ActivityIndicator } from 'react-native';

export function Field({ label, value, onChangeText, placeholder, keyboardType, secureTextEntry, multiline, numberOfLines }) {
  return (
    <View style={styles.field}>
      {label ? <Text style={styles.label}>{label}</Text> : null}
      <TextInput
        style={[styles.input, multiline && styles.textArea]}
        placeholder={placeholder}
        placeholderTextColor="#999"
        value={value}
        onChangeText={onChangeText}
        keyboardType={keyboardType}
        secureTextEntry={secureTextEntry}
        multiline={multiline}
        numberOfLines={numberOfLines}
      />
    </View>
  );
}

export function BottomModal({ visible, onClose, title, children }) {
  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <KeyboardAvoidingView
        style={styles.modalOverlay}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>{title}</Text>
          <ScrollView showsVerticalScrollIndicator={false}>
            {children}
          </ScrollView>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

export function SubmitBar({ onCancel, onSubmit, submitting, submitLabel, cancelLabel }) {
  return (
    <View style={styles.actions}>
      {onCancel ? (
        <TouchableOpacity style={styles.cancelBtn} onPress={onCancel}>
          <Text style={styles.cancelText}>{cancelLabel || 'Cancel'}</Text>
        </TouchableOpacity>
      ) : null}
      <TouchableOpacity style={[styles.submitBtn, submitting && { opacity: 0.5 }]} onPress={onSubmit} disabled={submitting}>
        {submitting ? <ActivityIndicator color="#fff" /> : <Text style={styles.submitText}>{submitLabel || 'Save'}</Text>}
      </TouchableOpacity>
    </View>
  );
}

export function StatsCard({ icon, label, value, color }) {
  return (
    <View style={[styles.statCard, { borderLeftColor: color }]}>
      <Text style={[styles.statValue, { color }]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

export function ScreenHeader({ title, right, left, onBack }) {
  return (
    <View style={styles.header}>
      {onBack ? (
        <TouchableOpacity onPress={onBack}>
          <Text style={styles.backBtn}>‹</Text>
        </TouchableOpacity>
      ) : null}
      <Text style={styles.headerTitle}>{title}</Text>
      <View style={{ flexDirection: 'row' }}>{right}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  field: { marginBottom: 12 },
  label: { fontSize: 14, fontWeight: '600', marginBottom: 6, color: '#333' },
  input: {
    backgroundColor: '#F5F5F5', borderRadius: 8, padding: 12,
    fontSize: 16, color: '#333',
  },
  textArea: { height: 90, textAlignVertical: 'top' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContent: {
    backgroundColor: '#fff', borderTopLeftRadius: 20, borderTopRightRadius: 20,
    padding: 24, maxHeight: '85%',
  },
  modalTitle: { fontSize: 20, fontWeight: 'bold', marginBottom: 16, color: '#333' },
  actions: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: 12 },
  cancelBtn: { padding: 12, marginRight: 12 },
  cancelText: { fontSize: 16, color: '#666' },
  submitBtn: {
    backgroundColor: '#E65100', borderRadius: 8, paddingHorizontal: 24, padding: 12,
    minWidth: 90, alignItems: 'center',
  },
  submitText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  statCard: {
    width: '47%', backgroundColor: '#fff', borderRadius: 12, padding: 16,
    marginBottom: 8, elevation: 2, borderLeftWidth: 4,
  },
  statValue: { fontSize: 22, fontWeight: 'bold', marginTop: 4 },
  statLabel: { fontSize: 13, color: '#888', marginTop: 4 },
  header: {
    backgroundColor: '#E65100', padding: 20, paddingTop: 16,
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
  },
  headerTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff', flex: 1 },
  backBtn: { fontSize: 32, color: '#fff', marginRight: 12, lineHeight: 32 },
});

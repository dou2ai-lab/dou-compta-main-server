import React from 'react';
import { View, Text, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function MoreScreen({ navigation }: any) {
  const items = [
    { title: 'Dossiers Clients', icon: 'folder-outline', color: '#8B5CF6' },
    { title: 'Fiscalite', icon: 'document-text-outline', color: '#EF4444' },
    { title: 'Analyse Financiere', icon: 'bar-chart-outline', color: '#10B981' },
    { title: 'Factures', icon: 'receipt-outline', color: '#F59E0B' },
    { title: 'Paie & Social', icon: 'people-outline', color: '#3B82F6' },
    { title: 'Documents', icon: 'cloud-upload-outline', color: '#6366F1' },
    { title: 'Agents', icon: 'hardware-chip-outline', color: '#EC4899' },
    { title: 'Notifications', icon: 'notifications-outline', color: '#F97316', onPress: () => navigation.navigate('Notifications') },
    { title: 'Parametres', icon: 'settings-outline', color: '#6B7280' },
  ];

  return (
    <ScrollView style={s.container}>
      <Text style={s.sectionTitle}>Modules</Text>
      {items.map((item, i) => (
        <TouchableOpacity key={i} style={s.item} onPress={item.onPress}>
          <View style={[s.icon, { backgroundColor: item.color + '15' }]}>
            <Ionicons name={item.icon as any} size={22} color={item.color} />
          </View>
          <Text style={s.itemTitle}>{item.title}</Text>
          <Ionicons name="chevron-forward" size={18} color="#D1D5DB" />
        </TouchableOpacity>
      ))}
      <Text style={s.version}>DouCompta V4.0 Mobile</Text>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  sectionTitle: { fontSize: 13, fontWeight: '600', color: '#6B7280', textTransform: 'uppercase', marginHorizontal: 16, marginTop: 20, marginBottom: 8 },
  item: { backgroundColor: '#fff', marginHorizontal: 16, marginBottom: 1, paddingVertical: 14, paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center', gap: 12, borderBottomWidth: 1, borderBottomColor: '#F3F4F6' },
  icon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  itemTitle: { flex: 1, fontSize: 15, color: '#1F2937' },
  version: { textAlign: 'center', color: '#9CA3AF', fontSize: 12, marginVertical: 20 },
});

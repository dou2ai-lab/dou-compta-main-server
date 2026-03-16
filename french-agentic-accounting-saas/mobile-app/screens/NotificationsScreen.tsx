import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { notificationAPI } from '../lib/api';

const priorityColor = { urgent: '#EF4444', high: '#F97316', normal: '#3B82F6', low: '#9CA3AF' };

export default function NotificationsScreen() {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { load(); }, []);

  async function load() {
    setLoading(true);
    try { const res = await notificationAPI.list({ page_size: 50 }); setNotifications(res.data || []); } catch {}
    finally { setLoading(false); }
  }

  async function markRead(id: string) {
    try { await notificationAPI.markRead(id); load(); } catch {}
  }

  return (
    <View style={s.container}>
      <FlatList
        data={notifications}
        keyExtractor={(item) => item.id}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
        ListEmptyComponent={<View style={s.emptyContainer}><Ionicons name="notifications-off-outline" size={48} color="#D1D5DB" /><Text style={s.empty}>Aucune notification</Text></View>}
        renderItem={({ item }) => (
          <TouchableOpacity style={[s.card, item.status === 'unread' && s.unread]} onPress={() => item.status === 'unread' && markRead(item.id)}>
            <View style={[s.indicator, { backgroundColor: (priorityColor as any)[item.priority] || '#3B82F6' }]} />
            <View style={{ flex: 1 }}>
              <Text style={[s.title, item.status === 'unread' && { fontWeight: '700' }]}>{item.title}</Text>
              {item.body && <Text style={s.body} numberOfLines={2}>{item.body}</Text>}
              <Text style={s.time}>{new Date(item.created_at).toLocaleString('fr-FR')}</Text>
            </View>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  card: { backgroundColor: '#fff', marginHorizontal: 16, marginTop: 8, borderRadius: 10, padding: 14, flexDirection: 'row', gap: 12, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 4, elevation: 1 },
  unread: { backgroundColor: '#EFF6FF' },
  indicator: { width: 4, borderRadius: 2, marginVertical: 2 },
  title: { fontSize: 14, color: '#1F2937' },
  body: { fontSize: 12, color: '#6B7280', marginTop: 2 },
  time: { fontSize: 11, color: '#9CA3AF', marginTop: 4 },
  emptyContainer: { alignItems: 'center', padding: 60 },
  empty: { color: '#9CA3AF', marginTop: 8 },
});

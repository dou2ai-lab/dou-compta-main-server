import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { notificationAPI } from '../lib/api';

export default function DashboardScreen({ navigation }: any) {
  const [unreadCount, setUnreadCount] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    try { const res = await notificationAPI.getUnreadCount(); setUnreadCount(res.unread_count || 0); } catch {}
  }

  async function onRefresh() { setRefreshing(true); await loadData(); setRefreshing(false); }

  const cards = [
    { title: 'Depenses', icon: 'receipt-outline', color: '#3B82F6', screen: 'Depenses' },
    { title: 'Comptabilite', icon: 'calculator-outline', color: '#8B5CF6', screen: 'Compta' },
    { title: 'Banque', icon: 'card-outline', color: '#10B981', screen: 'Banque' },
    { title: 'Notifications', icon: 'notifications-outline', color: '#F59E0B', screen: 'Notifications', badge: unreadCount },
  ];

  return (
    <ScrollView style={s.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
      <View style={s.header}>
        <Text style={s.greeting}>Bonjour!</Text>
        <Text style={s.subtitle}>DouCompta V4.0</Text>
      </View>
      <View style={s.grid}>
        {cards.map((card, i) => (
          <TouchableOpacity key={i} style={[s.card, { borderLeftColor: card.color }]}
            onPress={() => navigation.navigate(card.screen)}>
            <View style={s.cardContent}>
              <Ionicons name={card.icon as any} size={28} color={card.color} />
              <Text style={s.cardTitle}>{card.title}</Text>
              {card.badge ? <View style={s.badge}><Text style={s.badgeText}>{card.badge}</Text></View> : null}
            </View>
          </TouchableOpacity>
        ))}
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  header: { padding: 20, backgroundColor: '#4F46E5', paddingTop: 60 },
  greeting: { fontSize: 24, fontWeight: 'bold', color: '#fff' },
  subtitle: { fontSize: 14, color: '#C7D2FE', marginTop: 4 },
  grid: { padding: 16, gap: 12 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16, borderLeftWidth: 4, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 4, elevation: 2 },
  cardContent: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  cardTitle: { fontSize: 16, fontWeight: '600', flex: 1, color: '#1F2937' },
  badge: { backgroundColor: '#EF4444', borderRadius: 10, minWidth: 20, height: 20, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 6 },
  badgeText: { color: '#fff', fontSize: 11, fontWeight: 'bold' },
});

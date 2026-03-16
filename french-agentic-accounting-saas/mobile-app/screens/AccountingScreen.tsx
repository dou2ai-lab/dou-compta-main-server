import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl } from 'react-native';
import { accountingAPI } from '../lib/api';

export default function AccountingScreen() {
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { load(); }, []);

  async function load() {
    setLoading(true);
    try { const res = await accountingAPI.listEntries({ page: 1, page_size: 50 }); setEntries(res.data || []); } catch {}
    finally { setLoading(false); }
  }

  const fmt = (n: number) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n);
  const statusColor = (s: string) => s === 'validated' ? '#10B981' : s === 'posted' ? '#3B82F6' : '#F59E0B';

  return (
    <View style={s.container}>
      <FlatList
        data={entries}
        keyExtractor={(item) => item.id}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
        ListEmptyComponent={<Text style={s.empty}>Aucune ecriture</Text>}
        renderItem={({ item }) => (
          <View style={s.card}>
            <View style={s.row}>
              <View style={[s.badge, { backgroundColor: '#EEF2FF' }]}><Text style={s.badgeText}>{item.journal_code}</Text></View>
              <Text style={s.number}>{item.entry_number}</Text>
            </View>
            <Text style={s.desc} numberOfLines={1}>{item.description}</Text>
            <View style={s.row}>
              <Text style={s.date}>{new Date(item.entry_date).toLocaleDateString('fr-FR')}</Text>
              <View style={{ flex: 1 }} />
              <Text style={s.debit}>D: {fmt(item.total_debit)}</Text>
              <Text style={s.credit}>C: {fmt(item.total_credit)}</Text>
            </View>
            <View style={[s.statusDot, { backgroundColor: statusColor(item.status) }]} />
          </View>
        )}
      />
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  card: { backgroundColor: '#fff', marginHorizontal: 16, marginTop: 8, borderRadius: 10, padding: 14, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 4, elevation: 1 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  badge: { borderRadius: 6, paddingHorizontal: 8, paddingVertical: 2 },
  badgeText: { fontSize: 11, fontWeight: '700', color: '#4F46E5' },
  number: { fontSize: 14, fontWeight: '600', color: '#1F2937' },
  desc: { fontSize: 13, color: '#6B7280', marginVertical: 4 },
  date: { fontSize: 12, color: '#9CA3AF' },
  debit: { fontSize: 12, color: '#10B981', marginRight: 8 },
  credit: { fontSize: 12, color: '#3B82F6' },
  statusDot: { position: 'absolute', top: 14, right: 14, width: 8, height: 8, borderRadius: 4 },
  empty: { textAlign: 'center', padding: 40, color: '#9CA3AF' },
});

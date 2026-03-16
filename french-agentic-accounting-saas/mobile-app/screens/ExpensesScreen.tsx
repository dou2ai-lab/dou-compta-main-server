import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl } from 'react-native';
import { expensesAPI } from '../lib/api';

export default function ExpensesScreen() {
  const [expenses, setExpenses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { load(); }, []);

  async function load() {
    setLoading(true);
    try { const res = await expensesAPI.list({ page: 1, page_size: 50 }); setExpenses(res.data || []); } catch (e) { console.log(e); }
    finally { setLoading(false); }
  }

  const fmt = (n: number) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n);

  const statusColor = (s: string) => s === 'approved' ? '#10B981' : s === 'submitted' ? '#F59E0B' : s === 'rejected' ? '#EF4444' : '#6B7280';

  return (
    <View style={s.container}>
      <FlatList
        data={expenses}
        keyExtractor={(item) => item.id}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
        ListEmptyComponent={<Text style={s.empty}>Aucune depense</Text>}
        renderItem={({ item }) => (
          <View style={s.card}>
            <View style={s.row}>
              <View style={{ flex: 1 }}>
                <Text style={s.merchant}>{item.merchant_name || 'Sans marchand'}</Text>
                <Text style={s.desc}>{item.description || item.category}</Text>
                <Text style={s.date}>{new Date(item.expense_date).toLocaleDateString('fr-FR')}</Text>
              </View>
              <View style={{ alignItems: 'flex-end' }}>
                <Text style={s.amount}>{fmt(item.amount)}</Text>
                <View style={[s.statusBadge, { backgroundColor: statusColor(item.status) + '20' }]}>
                  <Text style={[s.statusText, { color: statusColor(item.status) }]}>{item.status}</Text>
                </View>
              </View>
            </View>
          </View>
        )}
      />
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  card: { backgroundColor: '#fff', marginHorizontal: 16, marginTop: 8, borderRadius: 10, padding: 14, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 4, elevation: 1 },
  row: { flexDirection: 'row', alignItems: 'center' },
  merchant: { fontSize: 15, fontWeight: '600', color: '#1F2937' },
  desc: { fontSize: 13, color: '#6B7280', marginTop: 2 },
  date: { fontSize: 12, color: '#9CA3AF', marginTop: 2 },
  amount: { fontSize: 16, fontWeight: 'bold', color: '#1F2937' },
  statusBadge: { borderRadius: 8, paddingHorizontal: 8, paddingVertical: 2, marginTop: 4 },
  statusText: { fontSize: 11, fontWeight: '600' },
  empty: { textAlign: 'center', padding: 40, color: '#9CA3AF' },
});

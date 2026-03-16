import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { bankingAPI } from '../lib/api';

export default function BankingScreen() {
  const [accounts, setAccounts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { load(); }, []);

  async function load() {
    setLoading(true);
    try { const res = await bankingAPI.listAccounts(); setAccounts(res.data || []); } catch {}
    finally { setLoading(false); }
  }

  const fmt = (n: number) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n);

  return (
    <View style={s.container}>
      <FlatList
        data={accounts}
        keyExtractor={(item) => item.id}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
        ListHeaderComponent={
          <View style={s.totalCard}>
            <Text style={s.totalLabel}>Solde total</Text>
            <Text style={s.totalAmount}>{fmt(accounts.reduce((sum, a) => sum + Number(a.balance || 0), 0))}</Text>
          </View>
        }
        ListEmptyComponent={<Text style={s.empty}>Aucun compte bancaire</Text>}
        renderItem={({ item }) => (
          <View style={s.card}>
            <View style={s.row}>
              <View style={s.icon}><Ionicons name="business-outline" size={20} color="#4F46E5" /></View>
              <View style={{ flex: 1 }}>
                <Text style={s.name}>{item.account_name}</Text>
                {item.bank_name && <Text style={s.bank}>{item.bank_name}</Text>}
              </View>
              <Text style={s.balance}>{fmt(item.balance)}</Text>
            </View>
            {item.iban && <Text style={s.iban}>{item.iban}</Text>}
          </View>
        )}
      />
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  totalCard: { margin: 16, backgroundColor: '#4F46E5', borderRadius: 16, padding: 20, alignItems: 'center' },
  totalLabel: { color: '#C7D2FE', fontSize: 14 },
  totalAmount: { color: '#fff', fontSize: 28, fontWeight: 'bold', marginTop: 4 },
  card: { backgroundColor: '#fff', marginHorizontal: 16, marginTop: 8, borderRadius: 10, padding: 14, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 4, elevation: 1 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  icon: { width: 40, height: 40, borderRadius: 10, backgroundColor: '#EEF2FF', justifyContent: 'center', alignItems: 'center' },
  name: { fontSize: 15, fontWeight: '600', color: '#1F2937' },
  bank: { fontSize: 12, color: '#6B7280' },
  balance: { fontSize: 18, fontWeight: 'bold', color: '#1F2937' },
  iban: { fontSize: 11, color: '#9CA3AF', marginTop: 6, fontFamily: 'monospace' },
  empty: { textAlign: 'center', padding: 40, color: '#9CA3AF' },
});

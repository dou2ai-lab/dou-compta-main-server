import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { authAPI, setAuthToken } from '../lib/api';

export default function LoginScreen({ navigation }: any) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    if (!email || !password) { Alert.alert('Erreur', 'Email et mot de passe requis'); return; }
    setLoading(true);
    try {
      const res = await authAPI.login(email, password);
      if (res.access_token) { setAuthToken(res.access_token); navigation.replace('Main'); }
      else { Alert.alert('Erreur', 'Identifiants invalides'); }
    } catch (err: any) { Alert.alert('Erreur', err?.response?.data?.detail || 'Connexion echouee'); }
    finally { setLoading(false); }
  }

  return (
    <View style={s.container}>
      <View style={s.header}><Text style={s.logo}>DouCompta</Text><Text style={s.subtitle}>Comptabilite intelligente</Text></View>
      <View style={s.form}>
        <TextInput style={s.input} placeholder="Email" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" />
        <TextInput style={s.input} placeholder="Mot de passe" value={password} onChangeText={setPassword} secureTextEntry />
        <TouchableOpacity style={s.button} onPress={handleLogin} disabled={loading}>
          <Text style={s.buttonText}>{loading ? 'Connexion...' : 'Se connecter'}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#4F46E5', justifyContent: 'center', padding: 24 },
  header: { alignItems: 'center', marginBottom: 40 },
  logo: { fontSize: 32, fontWeight: 'bold', color: '#fff' },
  subtitle: { fontSize: 14, color: '#C7D2FE', marginTop: 4 },
  form: { backgroundColor: '#fff', borderRadius: 16, padding: 24, gap: 12 },
  input: { borderWidth: 1, borderColor: '#E5E7EB', borderRadius: 10, padding: 14, fontSize: 15 },
  button: { backgroundColor: '#4F46E5', borderRadius: 10, padding: 16, alignItems: 'center', marginTop: 8 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
});

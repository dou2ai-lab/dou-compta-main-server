import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import { StatusBar } from 'expo-status-bar';

import DashboardScreen from './screens/DashboardScreen';
import ExpensesScreen from './screens/ExpensesScreen';
import AccountingScreen from './screens/AccountingScreen';
import BankingScreen from './screens/BankingScreen';
import MoreScreen from './screens/MoreScreen';
import NotificationsScreen from './screens/NotificationsScreen';
import LoginScreen from './screens/LoginScreen';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap = 'home';
          if (route.name === 'Accueil') iconName = focused ? 'home' : 'home-outline';
          else if (route.name === 'Depenses') iconName = focused ? 'receipt' : 'receipt-outline';
          else if (route.name === 'Compta') iconName = focused ? 'calculator' : 'calculator-outline';
          else if (route.name === 'Banque') iconName = focused ? 'card' : 'card-outline';
          else if (route.name === 'Plus') iconName = focused ? 'menu' : 'menu-outline';
          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#4F46E5',
        tabBarInactiveTintColor: 'gray',
        headerStyle: { backgroundColor: '#4F46E5' },
        headerTintColor: '#fff',
        headerRight: () => null,
      })}
    >
      <Tab.Screen name="Accueil" component={DashboardScreen} />
      <Tab.Screen name="Depenses" component={ExpensesScreen} />
      <Tab.Screen name="Compta" component={AccountingScreen} />
      <Tab.Screen name="Banque" component={BankingScreen} />
      <Tab.Screen name="Plus" component={MoreScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Main" component={MainTabs} />
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Notifications" component={NotificationsScreen} options={{ headerShown: true, title: 'Notifications', headerStyle: { backgroundColor: '#4F46E5' }, headerTintColor: '#fff' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

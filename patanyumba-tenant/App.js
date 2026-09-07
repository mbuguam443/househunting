import React, { useCallback } from 'react';
import { ActivityIndicator, View, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import * as SplashScreen from 'expo-splash-screen';

import { AuthProvider, useAuth } from './src/contexts/AuthContext';

SplashScreen.preventAutoHideAsync();
import LoginScreen from './src/screens/LoginScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import PaymentsScreen from './src/screens/PaymentsScreen';
import PayScreen from './src/screens/PayScreen';
import MaintenanceScreen from './src/screens/MaintenanceScreen';
import LeaseScreen from './src/screens/LeaseScreen';
import UtilitiesScreen from './src/screens/UtilitiesScreen';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          const icons = {
            Dashboard: focused ? 'home' : 'home-outline',
            Pay: focused ? 'card' : 'card-outline',
            Payments: focused ? 'receipt' : 'receipt-outline',
            Maintenance: focused ? 'build' : 'build-outline',
            Utilities: focused ? 'flash' : 'flash-outline',
          };
          return <Ionicons name={icons[route.name]} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#1B5E20',
        tabBarInactiveTintColor: '#999',
        headerShown: false,
      })}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen} />
      <Tab.Screen name="Pay" component={PayScreen} options={{ tabBarLabel: 'Pay' }} />
      <Tab.Screen name="Payments" component={PaymentsScreen} />
      <Tab.Screen name="Maintenance" component={MaintenanceScreen} />
      <Tab.Screen name="Utilities" component={UtilitiesScreen} />
    </Tab.Navigator>
  );
}

function RootNavigator() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color="#1B5E20" />
      </View>
    );
  }

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {user ? (
        <>
          <Stack.Screen name="Main" component={TabNavigator} />
          <Stack.Screen name="Lease" component={LeaseScreen} />
        </>
      ) : (
        <Stack.Screen name="Login" component={LoginScreen} />
      )}
    </Stack.Navigator>
  );
}

export default function App() {
  const onLayoutRootView = useCallback(async () => {
    // Hide splash screen once app is ready
  }, []);

  return (
    <View style={{ flex: 1 }} onLayout={onLayoutRootView}>
      <AuthProvider>
        <NavigationContainer
          onReady={() => {
            SplashScreen.hideAsync();
          }}
        >
          <RootNavigator />
        </NavigationContainer>
      </AuthProvider>
    </View>
  );
}

const styles = StyleSheet.create({
  loading: { flex: 1, justifyContent: 'center', alignItems: 'center' },
});

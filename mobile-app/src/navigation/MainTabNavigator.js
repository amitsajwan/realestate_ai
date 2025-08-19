import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useBranding } from '../contexts/BrandingContext';

// Screens
import DashboardScreen from '../screens/DashboardScreen';
import PropertiesScreen from '../screens/PropertiesScreen';
import LeadsScreen from '../screens/LeadsScreen';
import ClientsScreen from '../screens/ClientsScreen';
import AIAssistantScreen from '../screens/AIAssistantScreen';

const Tab = createBottomTabNavigator();

export default function MainTabNavigator() {
  const theme = useTheme();
  const { branding } = useBranding();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;

          if (route.name === 'Dashboard') {
            iconName = focused ? 'view-dashboard' : 'view-dashboard-outline';
          } else if (route.name === 'Properties') {
            iconName = focused ? 'home' : 'home-outline';
          } else if (route.name === 'Leads') {
            iconName = focused ? 'account-multiple' : 'account-multiple-outline';
          } else if (route.name === 'Clients') {
            iconName = focused ? 'account-heart' : 'account-heart-outline';
          } else if (route.name === 'AI Assistant') {
            iconName = focused ? 'robot' : 'robot-outline';
          }

          return <MaterialCommunityIcons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: branding.primaryColor,
        tabBarInactiveTintColor: '#9CA3AF',
        tabBarStyle: {
          backgroundColor: branding.backgroundColor,
          borderTopColor: branding.borderColor,
          paddingBottom: 5,
          height: 65,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '500',
        },
        headerStyle: {
          backgroundColor: branding.primaryColor,
        },
        headerTintColor: 'white',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      })}
    >
      <Tab.Screen 
        name="Dashboard" 
        component={DashboardScreen}
        options={{
          title: 'Dashboard',
        }}
      />
      <Tab.Screen 
        name="Properties" 
        component={PropertiesScreen}
        options={{
          title: 'Properties',
        }}
      />
      <Tab.Screen 
        name="Leads" 
        component={LeadsScreen}
        options={{
          title: 'Leads',
        }}
      />
      <Tab.Screen 
        name="Clients" 
        component={ClientsScreen}
        options={{
          title: 'Clients',
        }}
      />
      <Tab.Screen 
        name="AI Assistant" 
        component={AIAssistantScreen}
        options={{
          title: 'AI Assistant',
        }}
      />
    </Tab.Navigator>
  );
}
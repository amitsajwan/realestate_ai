import React, { useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import {
  Text,
  Button,
  Card,
  Switch,
  Chip,
  List,
  Divider,
} from 'react-native-paper';
import { useBranding } from '../../contexts/BrandingContext';

const NOTIFICATION_PREFERENCES = [
  {
    id: 'new_leads',
    title: 'New Leads',
    description: 'Get notified when new leads come in',
    icon: 'account-plus',
    enabled: true,
  },
  {
    id: 'client_messages',
    title: 'Client Messages',
    description: 'Notifications for client communications',
    icon: 'message-text',
    enabled: true,
  },
  {
    id: 'property_updates',
    title: 'Property Updates',
    description: 'Updates on your listed properties',
    icon: 'home-alert',
    enabled: true,
  },
  {
    id: 'market_insights',
    title: 'Market Insights',
    description: 'Weekly market analysis and trends',
    icon: 'chart-timeline-variant',
    enabled: false,
  },
  {
    id: 'system_updates',
    title: 'System Updates',
    description: 'App updates and new features',
    icon: 'update',
    enabled: false,
  },
];

const WORK_PREFERENCES = [
  {
    id: 'working_hours',
    title: 'Working Hours',
    options: ['9 AM - 5 PM', '8 AM - 6 PM', '10 AM - 8 PM', '24/7 Available'],
    selected: '9 AM - 5 PM',
  },
  {
    id: 'preferred_contact',
    title: 'Preferred Contact Method',
    options: ['Phone', 'Email', 'Text Message', 'App Notifications'],
    selected: 'Phone',
  },
  {
    id: 'lead_follow_up',
    title: 'Lead Follow-up Frequency',
    options: ['Immediate', 'Within 1 Hour', 'Same Day', 'Next Business Day'],
    selected: 'Within 1 Hour',
  },
];

export default function PreferencesStep({ formData, onNext, isLoading }) {
  const [notifications, setNotifications] = useState(
    formData.notifications || NOTIFICATION_PREFERENCES
  );
  const [workPreferences, setWorkPreferences] = useState(
    formData.workPreferences || WORK_PREFERENCES
  );
  const [autoSync, setAutoSync] = useState(formData.autoSync !== false);
  const [dataBackup, setDataBackup] = useState(formData.dataBackup !== false);
  const [offlineMode, setOfflineMode] = useState(formData.offlineMode || false);

  const { branding } = useBranding();

  const handleNext = () => {
    onNext({
      notifications,
      workPreferences,
      autoSync,
      dataBackup,
      offlineMode,
      preferencesCompleted: true,
    });
  };

  const toggleNotification = (notificationId) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === notificationId 
          ? { ...notification, enabled: !notification.enabled }
          : notification
      )
    );
  };

  const updateWorkPreference = (preferenceId, value) => {
    setWorkPreferences(prev => 
      prev.map(preference => 
        preference.id === preferenceId 
          ? { ...preference, selected: value }
          : preference
      )
    );
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <Text style={styles.title}>Set Your Preferences</Text>
      <Text style={styles.subtitle}>
        Customize your experience and workflow
      </Text>

      <View style={styles.form}>
        {/* Notification Preferences */}
        <Text style={styles.sectionTitle}>Notifications</Text>
        <Card style={styles.card}>
          {notifications.map((notification, index) => (
            <View key={notification.id}>
              <List.Item
                title={notification.title}
                description={notification.description}
                left={(props) => <List.Icon {...props} icon={notification.icon} />}
                right={() => (
                  <Switch
                    value={notification.enabled}
                    onValueChange={() => toggleNotification(notification.id)}
                    color={branding.primaryColor}
                  />
                )}
              />
              {index < notifications.length - 1 && <Divider />}
            </View>
          ))}
        </Card>

        {/* Work Preferences */}
        <Text style={styles.sectionTitle}>Work Preferences</Text>
        {workPreferences.map((preference) => (
          <Card key={preference.id} style={styles.card}>
            <View style={styles.preferenceHeader}>
              <Text style={styles.preferenceTitle}>{preference.title}</Text>
            </View>
            <View style={styles.optionsContainer}>
              {preference.options.map((option) => (
                <Chip
                  key={option}
                  selected={preference.selected === option}
                  onPress={() => updateWorkPreference(preference.id, option)}
                  style={[
                    styles.optionChip,
                    preference.selected === option && {
                      backgroundColor: branding.primaryColor,
                    }
                  ]}
                  textStyle={[
                    preference.selected === option && { color: 'white' }
                  ]}
                >
                  {option}
                </Chip>
              ))}
            </View>
          </Card>
        ))}

        {/* System Preferences */}
        <Text style={styles.sectionTitle}>System Settings</Text>
        <Card style={styles.card}>
          <List.Item
            title="Auto-sync Data"
            description="Automatically sync your data across devices"
            left={(props) => <List.Icon {...props} icon="sync" />}
            right={() => (
              <Switch
                value={autoSync}
                onValueChange={setAutoSync}
                color={branding.primaryColor}
              />
            )}
          />
          <Divider />
          <List.Item
            title="Data Backup"
            description="Automatically backup your data to cloud"
            left={(props) => <List.Icon {...props} icon="backup-restore" />}
            right={() => (
              <Switch
                value={dataBackup}
                onValueChange={setDataBackup}
                color={branding.primaryColor}
              />
            )}
          />
          <Divider />
          <List.Item
            title="Offline Mode"
            description="Enable offline functionality"
            left={(props) => <List.Icon {...props} icon="cloud-off" />}
            right={() => (
              <Switch
                value={offlineMode}
                onValueChange={setOfflineMode}
                color={branding.primaryColor}
              />
            )}
          />
        </Card>
      </View>

      <Button
        mode="contained"
        onPress={handleNext}
        loading={isLoading}
        disabled={isLoading}
        style={[styles.nextButton, { backgroundColor: branding.primaryColor }]}
        contentStyle={styles.buttonContent}
      >
        Continue
      </Button>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#64748B',
    textAlign: 'center',
    marginBottom: 32,
  },
  form: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
    marginTop: 16,
  },
  card: {
    marginBottom: 16,
  },
  preferenceHeader: {
    padding: 16,
    paddingBottom: 8,
  },
  preferenceTitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  optionsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 16,
    paddingTop: 8,
    gap: 8,
  },
  optionChip: {
    marginRight: 8,
    marginBottom: 8,
  },
  nextButton: {
    marginTop: 16,
    borderRadius: 12,
  },
  buttonContent: {
    paddingVertical: 8,
  },
});
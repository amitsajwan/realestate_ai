import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Dimensions,
} from 'react-native';
import {
  Text,
  Card,
  Avatar,
  Button,
  IconButton,
  Chip,
  Surface,
  FAB,
} from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import * as Animatable from 'react-native-animatable';
import { FlatGrid } from 'react-native-super-grid';
import { useBranding } from '../contexts/BrandingContext';
import { useAuth } from '../contexts/AuthContext';

const { width } = Dimensions.get('window');

const DASHBOARD_STATS = [
  {
    id: 'active_listings',
    title: 'Active Listings',
    value: '24',
    change: '+3',
    changeType: 'positive',
    icon: 'home',
    color: '#38A169',
  },
  {
    id: 'new_leads',
    title: 'New Leads',
    value: '18',
    change: '+5',
    changeType: 'positive',
    icon: 'account-plus',
    color: '#3182CE',
  },
  {
    id: 'pending_deals',
    title: 'Pending Deals',
    value: '7',
    change: '-2',
    changeType: 'negative',
    icon: 'handshake',
    color: '#F18F01',
  },
  {
    id: 'monthly_revenue',
    title: 'Monthly Revenue',
    value: '$45.2K',
    change: '+12%',
    changeType: 'positive',
    icon: 'currency-usd',
    color: '#38A169',
  },
];

const RECENT_ACTIVITIES = [
  {
    id: 1,
    type: 'new_lead',
    title: 'New lead inquiry',
    description: 'Sarah Johnson interested in downtown condo',
    time: '5 min ago',
    icon: 'account-plus',
    color: '#3182CE',
  },
  {
    id: 2,
    type: 'property_update',
    title: 'Property price updated',
    description: '123 Oak Street - Price reduced to $450K',
    time: '1 hour ago',
    icon: 'home-edit',
    color: '#F18F01',
  },
  {
    id: 3,
    type: 'appointment',
    title: 'Upcoming showing',
    description: 'Property viewing at 456 Pine Ave at 3 PM',
    time: '2 hours ago',
    icon: 'calendar-clock',
    color: '#9F7AEA',
  },
  {
    id: 4,
    type: 'deal_closed',
    title: 'Deal closed successfully',
    description: '789 Maple Drive sold for $325K',
    time: '1 day ago',
    icon: 'check-circle',
    color: '#38A169',
  },
];

const QUICK_ACTIONS = [
  {
    id: 'add_property',
    title: 'Add Property',
    icon: 'home-plus',
    color: '#3182CE',
  },
  {
    id: 'new_lead',
    title: 'Add Lead',
    icon: 'account-plus',
    color: '#38A169',
  },
  {
    id: 'schedule_showing',
    title: 'Schedule',
    icon: 'calendar-plus',
    color: '#9F7AEA',
  },
  {
    id: 'market_analysis',
    title: 'Analysis',
    icon: 'chart-line',
    color: '#F18F01',
  },
];

export default function DashboardScreen({ navigation }) {
  const [refreshing, setRefreshing] = useState(false);
  const [greeting, setGreeting] = useState('');
  
  const { branding } = useBranding();
  const { user } = useAuth();

  useEffect(() => {
    setGreeting(getGreeting());
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const onRefresh = async () => {
    setRefreshing(true);
    // Simulate API call
    setTimeout(() => setRefreshing(false), 2000);
  };

  const renderStatCard = ({ item }) => (
    <Animatable.View
      animation="fadeInUp"
      duration={600}
      delay={item.id === 'active_listings' ? 0 : 100}
    >
      <Card style={styles.statCard}>
        <View style={styles.statContent}>
          <View style={styles.statHeader}>
            <Avatar.Icon
              size={40}
              icon={item.icon}
              style={{ backgroundColor: item.color + '20' }}
              color={item.color}
            />
            <View style={styles.changeContainer}>
              <Text
                style={[
                  styles.changeText,
                  {
                    color: item.changeType === 'positive' ? '#38A169' : '#E53E3E'
                  }
                ]}
              >
                {item.change}
              </Text>
            </View>
          </View>
          <Text style={styles.statValue}>{item.value}</Text>
          <Text style={styles.statTitle}>{item.title}</Text>
        </View>
      </Card>
    </Animatable.View>
  );

  const renderQuickAction = (action) => (
    <Surface key={action.id} style={styles.quickAction}>
      <IconButton
        icon={action.icon}
        size={24}
        iconColor={action.color}
        onPress={() => {
          // Handle quick action
          console.log('Quick action:', action.id);
        }}
      />
      <Text style={styles.quickActionText}>{action.title}</Text>
    </Surface>
  );

  const renderActivity = ({ item }) => (
    <Card style={styles.activityCard}>
      <View style={styles.activityContent}>
        <Avatar.Icon
          size={40}
          icon={item.icon}
          style={{ backgroundColor: item.color + '20' }}
          color={item.color}
        />
        <View style={styles.activityDetails}>
          <Text style={styles.activityTitle}>{item.title}</Text>
          <Text style={styles.activityDescription}>{item.description}</Text>
          <Text style={styles.activityTime}>{item.time}</Text>
        </View>
      </View>
    </Card>
  );

  return (
    <View style={[styles.container, { backgroundColor: branding.backgroundColor }]}>
      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <LinearGradient
          colors={[branding.primaryColor, branding.secondaryColor]}
          style={styles.header}
        >
          <View style={styles.headerContent}>
            <View style={styles.userInfo}>
              <Avatar.Image
                size={50}
                source={user?.profileImage ? { uri: user.profileImage } : undefined}
                style={styles.avatar}
              />
              <View style={styles.userDetails}>
                <Text style={styles.greeting}>{greeting},</Text>
                <Text style={styles.userName}>
                  {user?.firstName || 'Agent'}
                </Text>
                {branding.companyName && (
                  <Text style={styles.companyName}>{branding.companyName}</Text>
                )}
              </View>
            </View>
            <IconButton
              icon="bell"
              iconColor="white"
              size={24}
              onPress={() => {
                // Handle notifications
              }}
            />
          </View>
        </LinearGradient>

        {/* Stats Grid */}
        <View style={styles.statsContainer}>
          <FlatGrid
            itemDimension={150}
            data={DASHBOARD_STATS}
            style={styles.statsGrid}
            spacing={12}
            renderItem={renderStatCard}
            scrollEnabled={false}
          />
        </View>

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <View style={styles.quickActionsContainer}>
            {QUICK_ACTIONS.map(renderQuickAction)}
          </View>
        </View>

        {/* Recent Activities */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Recent Activities</Text>
            <Button
              mode="text"
              onPress={() => {
                // Navigate to full activities
              }}
              textColor={branding.primaryColor}
            >
              View All
            </Button>
          </View>
          
          {RECENT_ACTIVITIES.map((activity) => (
            <Animatable.View
              key={activity.id}
              animation="fadeInLeft"
              delay={activity.id * 100}
            >
              {renderActivity({ item: activity })}
            </Animatable.View>
          ))}
        </View>
      </ScrollView>

      {/* Floating Action Button */}
      <FAB
        icon="plus"
        style={[styles.fab, { backgroundColor: branding.primaryColor }]}
        onPress={() => {
          // Handle FAB press
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingTop: 60,
    paddingBottom: 30,
    paddingHorizontal: 20,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    marginRight: 16,
  },
  userDetails: {
    flex: 1,
  },
  greeting: {
    color: 'rgba(255,255,255,0.9)',
    fontSize: 16,
  },
  userName: {
    color: 'white',
    fontSize: 24,
    fontWeight: 'bold',
  },
  companyName: {
    color: 'rgba(255,255,255,0.8)',
    fontSize: 14,
  },
  statsContainer: {
    padding: 16,
    marginTop: -20,
  },
  statsGrid: {
    flex: 1,
  },
  statCard: {
    borderRadius: 12,
    elevation: 4,
  },
  statContent: {
    padding: 16,
  },
  statHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  changeContainer: {
    backgroundColor: '#F7FAFC',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  changeText: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  statTitle: {
    fontSize: 14,
    color: '#64748B',
  },
  section: {
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  quickActionsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  quickAction: {
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    minWidth: 70,
  },
  quickActionText: {
    fontSize: 12,
    marginTop: 8,
    textAlign: 'center',
  },
  activityCard: {
    marginBottom: 12,
    borderRadius: 12,
  },
  activityContent: {
    flexDirection: 'row',
    padding: 16,
  },
  activityDetails: {
    marginLeft: 16,
    flex: 1,
  },
  activityTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  activityDescription: {
    fontSize: 14,
    color: '#64748B',
    marginBottom: 4,
  },
  activityTime: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
  },
});
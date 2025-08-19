import React, { useState } from 'react';
import { View, StyleSheet, FlatList } from 'react-native';
import {
  Text,
  Card,
  FAB,
  Searchbar,
  Chip,
  Avatar,
  Button,
  IconButton,
} from 'react-native-paper';
import { useBranding } from '../contexts/BrandingContext';

const SAMPLE_CLIENTS = [
  {
    id: '1',
    name: 'David & Lisa Thompson',
    email: 'thompson.family@email.com',
    phone: '+1 (555) 234-5678',
    type: 'buyer',
    status: 'active',
    property: '123 Oak Street - Purchased',
    value: '$425,000',
    lastActivity: 'Property closing completed',
    lastContact: '1 week ago',
    relationship: 'excellent',
  },
  {
    id: '2',
    name: 'Robert Martinez',
    email: 'r.martinez@email.com',
    phone: '+1 (555) 345-6789',
    type: 'seller',
    status: 'active',
    property: '456 Pine Avenue - Listed',
    value: '$385,000',
    lastActivity: 'Price adjustment discussion',
    lastContact: '3 days ago',
    relationship: 'good',
  },
  {
    id: '3',
    name: 'Jennifer Walsh',
    email: 'jen.walsh@email.com',
    phone: '+1 (555) 456-7890',
    type: 'investor',
    status: 'past',
    property: '789 Maple Drive - Sold',
    value: '$295,000',
    lastActivity: 'Referral provided',
    lastContact: '2 months ago',
    relationship: 'excellent',
  },
];

const TYPE_FILTERS = [
  { key: 'all', label: 'All', color: '#64748B' },
  { key: 'buyer', label: 'Buyers', color: '#3182CE' },
  { key: 'seller', label: 'Sellers', color: '#38A169' },
  { key: 'investor', label: 'Investors', color: '#9F7AEA' },
];

const STATUS_FILTERS = [
  { key: 'all', label: 'All Status' },
  { key: 'active', label: 'Active' },
  { key: 'past', label: 'Past' },
  { key: 'potential', label: 'Potential' },
];

export default function ClientsScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTypeFilter, setSelectedTypeFilter] = useState('all');
  const [selectedStatusFilter, setSelectedStatusFilter] = useState('all');
  const [clients] = useState(SAMPLE_CLIENTS);
  
  const { branding } = useBranding();

  const getTypeColor = (type) => {
    switch (type) {
      case 'buyer': return '#3182CE';
      case 'seller': return '#38A169';
      case 'investor': return '#9F7AEA';
      default: return '#64748B';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return '#38A169';
      case 'past': return '#64748B';
      case 'potential': return '#F18F01';
      default: return '#64748B';
    }
  };

  const getRelationshipColor = (relationship) => {
    switch (relationship) {
      case 'excellent': return '#38A169';
      case 'good': return '#3182CE';
      case 'fair': return '#F18F01';
      case 'poor': return '#E53E3E';
      default: return '#64748B';
    }
  };

  const filteredClients = clients.filter(client => {
    const matchesSearch = client.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         client.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         client.property.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = selectedTypeFilter === 'all' || client.type === selectedTypeFilter;
    const matchesStatus = selectedStatusFilter === 'all' || client.status === selectedStatusFilter;
    return matchesSearch && matchesType && matchesStatus;
  });

  const renderClient = ({ item }) => (
    <Card style={styles.clientCard}>
      <View style={styles.clientContent}>
        <View style={styles.clientHeader}>
          <Avatar.Text
            size={50}
            label={item.name.split(' ').map(n => n[0]).join('').substring(0, 2)}
            style={{ backgroundColor: getTypeColor(item.type) + '20' }}
            labelStyle={{ color: getTypeColor(item.type) }}
          />
          <View style={styles.clientInfo}>
            <Text style={styles.clientName}>{item.name}</Text>
            <Text style={styles.clientContact}>{item.email}</Text>
            <Text style={styles.clientPhone}>{item.phone}</Text>
          </View>
          <IconButton
            icon="dots-vertical"
            size={20}
            onPress={() => {
              // Handle client menu
            }}
          />
        </View>
        
        <View style={styles.clientDetails}>
          <View style={styles.clientRow}>
            <Text style={styles.clientLabel}>Property:</Text>
            <Text style={styles.clientValue}>{item.property}</Text>
          </View>
          <View style={styles.clientRow}>
            <Text style={styles.clientLabel}>Value:</Text>
            <Text style={[styles.clientValue, styles.valueText]}>{item.value}</Text>
          </View>
          <View style={styles.clientRow}>
            <Text style={styles.clientLabel}>Last Activity:</Text>
            <Text style={styles.clientValue}>{item.lastActivity}</Text>
          </View>
          <View style={styles.clientRow}>
            <Text style={styles.clientLabel}>Last Contact:</Text>
            <Text style={styles.clientValue}>{item.lastContact}</Text>
          </View>
        </View>

        <View style={styles.clientFooter}>
          <View style={styles.clientChips}>
            <Chip
              compact
              style={[
                styles.typeChip,
                { backgroundColor: getTypeColor(item.type) + '20' }
              ]}
              textStyle={{ color: getTypeColor(item.type) }}
            >
              {item.type.charAt(0).toUpperCase() + item.type.slice(1)}
            </Chip>
            
            <Chip
              compact
              style={[
                styles.statusChip,
                { backgroundColor: getStatusColor(item.status) + '20' }
              ]}
              textStyle={{ color: getStatusColor(item.status) }}
            >
              {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
            </Chip>

            <Chip
              compact
              style={[
                styles.relationshipChip,
                { backgroundColor: getRelationshipColor(item.relationship) + '20' }
              ]}
              textStyle={{ color: getRelationshipColor(item.relationship) }}
            >
              {item.relationship.charAt(0).toUpperCase() + item.relationship.slice(1)}
            </Chip>
          </View>
          
          <View style={styles.clientActions}>
            <IconButton
              icon="phone"
              size={20}
              iconColor={branding.primaryColor}
              onPress={() => {
                // Handle call
              }}
            />
            <IconButton
              icon="email"
              size={20}
              iconColor={branding.primaryColor}
              onPress={() => {
                // Handle email
              }}
            />
            <IconButton
              icon="calendar"
              size={20}
              iconColor={branding.primaryColor}
              onPress={() => {
                // Handle schedule
              }}
            />
          </View>
        </View>
      </View>
    </Card>
  );

  return (
    <View style={[styles.container, { backgroundColor: branding.backgroundColor }]}>
      <View style={styles.header}>
        <Searchbar
          placeholder="Search clients..."
          onChangeText={setSearchQuery}
          value={searchQuery}
          style={styles.searchbar}
        />
        
        <View style={styles.filters}>
          <Text style={styles.filterLabel}>Type:</Text>
          {TYPE_FILTERS.map((filter) => (
            <Chip
              key={filter.key}
              selected={selectedTypeFilter === filter.key}
              onPress={() => setSelectedTypeFilter(filter.key)}
              style={[
                styles.filterChip,
                selectedTypeFilter === filter.key && {
                  backgroundColor: branding.primaryColor,
                }
              ]}
              textStyle={[
                selectedTypeFilter === filter.key && { color: 'white' }
              ]}
              compact
            >
              {filter.label}
            </Chip>
          ))}
        </View>

        <View style={styles.filters}>
          <Text style={styles.filterLabel}>Status:</Text>
          {STATUS_FILTERS.map((filter) => (
            <Chip
              key={filter.key}
              selected={selectedStatusFilter === filter.key}
              onPress={() => setSelectedStatusFilter(filter.key)}
              style={[
                styles.filterChip,
                selectedStatusFilter === filter.key && {
                  backgroundColor: branding.primaryColor,
                }
              ]}
              textStyle={[
                selectedStatusFilter === filter.key && { color: 'white' }
              ]}
              compact
            >
              {filter.label}
            </Chip>
          ))}
        </View>
      </View>

      <FlatList
        data={filteredClients}
        renderItem={renderClient}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateText}>No clients found</Text>
          </View>
        }
      />

      <FAB
        icon="plus"
        style={[styles.fab, { backgroundColor: branding.primaryColor }]}
        onPress={() => {
          // Handle add client
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
    padding: 16,
    backgroundColor: 'white',
  },
  searchbar: {
    marginBottom: 16,
  },
  filters: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  filterLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#64748B',
    minWidth: 45,
  },
  filterChip: {
    marginRight: 8,
  },
  listContent: {
    padding: 16,
  },
  clientCard: {
    marginBottom: 16,
    borderRadius: 12,
  },
  clientContent: {
    padding: 16,
  },
  clientHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  clientInfo: {
    flex: 1,
    marginLeft: 16,
  },
  clientName: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  clientContact: {
    fontSize: 14,
    color: '#64748B',
    marginBottom: 2,
  },
  clientPhone: {
    fontSize: 14,
    color: '#64748B',
  },
  clientDetails: {
    marginBottom: 16,
  },
  clientRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
    alignItems: 'flex-start',
  },
  clientLabel: {
    fontSize: 14,
    color: '#64748B',
    fontWeight: '500',
    flex: 1,
  },
  clientValue: {
    fontSize: 14,
    color: '#2D3748',
    flex: 2,
    textAlign: 'right',
  },
  valueText: {
    fontWeight: 'bold',
    color: '#38A169',
  },
  clientFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  clientChips: {
    flexDirection: 'row',
    flex: 1,
    gap: 4,
  },
  typeChip: {
    height: 24,
  },
  statusChip: {
    height: 24,
  },
  relationshipChip: {
    height: 24,
  },
  clientActions: {
    flexDirection: 'row',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyStateText: {
    fontSize: 16,
    color: '#64748B',
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
  },
});
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

const SAMPLE_PROPERTIES = [
  {
    id: '1',
    title: 'Modern Downtown Condo',
    address: '123 Main St, Downtown',
    price: '$450,000',
    bedrooms: 2,
    bathrooms: 2,
    sqft: '1,200',
    status: 'active',
    image: null,
    daysOnMarket: 15,
  },
  {
    id: '2',
    title: 'Family Home with Garden',
    address: '456 Oak Ave, Suburbs',
    price: '$325,000',
    bedrooms: 3,
    bathrooms: 2,
    sqft: '1,800',
    status: 'pending',
    image: null,
    daysOnMarket: 8,
  },
  {
    id: '3',
    title: 'Luxury Waterfront Villa',
    address: '789 Beach Rd, Waterfront',
    price: '$850,000',
    bedrooms: 4,
    bathrooms: 3,
    sqft: '2,500',
    status: 'active',
    image: null,
    daysOnMarket: 32,
  },
];

const STATUS_FILTERS = [
  { key: 'all', label: 'All', color: '#64748B' },
  { key: 'active', label: 'Active', color: '#38A169' },
  { key: 'pending', label: 'Pending', color: '#F18F01' },
  { key: 'sold', label: 'Sold', color: '#3182CE' },
];

export default function PropertiesScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [properties] = useState(SAMPLE_PROPERTIES);
  
  const { branding } = useBranding();

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return '#38A169';
      case 'pending': return '#F18F01';
      case 'sold': return '#3182CE';
      default: return '#64748B';
    }
  };

  const filteredProperties = properties.filter(property => {
    const matchesSearch = property.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         property.address.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = selectedFilter === 'all' || property.status === selectedFilter;
    return matchesSearch && matchesFilter;
  });

  const renderProperty = ({ item }) => (
    <Card style={styles.propertyCard}>
      <View style={styles.propertyContent}>
        <View style={styles.propertyHeader}>
          <Avatar.Text
            size={60}
            label="🏠"
            style={{ backgroundColor: branding.primaryColor + '20' }}
          />
          <View style={styles.propertyInfo}>
            <Text style={styles.propertyTitle}>{item.title}</Text>
            <Text style={styles.propertyAddress}>{item.address}</Text>
            <Text style={styles.propertyPrice}>{item.price}</Text>
          </View>
          <IconButton
            icon="dots-vertical"
            size={20}
            onPress={() => {
              // Handle property menu
            }}
          />
        </View>
        
        <View style={styles.propertyDetails}>
          <View style={styles.propertySpec}>
            <Text style={styles.specValue}>{item.bedrooms}</Text>
            <Text style={styles.specLabel}>Bed</Text>
          </View>
          <View style={styles.propertySpec}>
            <Text style={styles.specValue}>{item.bathrooms}</Text>
            <Text style={styles.specLabel}>Bath</Text>
          </View>
          <View style={styles.propertySpec}>
            <Text style={styles.specValue}>{item.sqft}</Text>
            <Text style={styles.specLabel}>Sq Ft</Text>
          </View>
        </View>

        <View style={styles.propertyFooter}>
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
          <Text style={styles.daysOnMarket}>
            {item.daysOnMarket} days on market
          </Text>
        </View>
      </View>
    </Card>
  );

  return (
    <View style={[styles.container, { backgroundColor: branding.backgroundColor }]}>
      <View style={styles.header}>
        <Searchbar
          placeholder="Search properties..."
          onChangeText={setSearchQuery}
          value={searchQuery}
          style={styles.searchbar}
        />
        
        <View style={styles.filters}>
          {STATUS_FILTERS.map((filter) => (
            <Chip
              key={filter.key}
              selected={selectedFilter === filter.key}
              onPress={() => setSelectedFilter(filter.key)}
              style={[
                styles.filterChip,
                selectedFilter === filter.key && {
                  backgroundColor: branding.primaryColor,
                }
              ]}
              textStyle={[
                selectedFilter === filter.key && { color: 'white' }
              ]}
            >
              {filter.label}
            </Chip>
          ))}
        </View>
      </View>

      <FlatList
        data={filteredProperties}
        renderItem={renderProperty}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateText}>No properties found</Text>
          </View>
        }
      />

      <FAB
        icon="plus"
        style={[styles.fab, { backgroundColor: branding.primaryColor }]}
        onPress={() => {
          // Handle add property
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
    gap: 8,
  },
  filterChip: {
    marginRight: 8,
  },
  listContent: {
    padding: 16,
  },
  propertyCard: {
    marginBottom: 16,
    borderRadius: 12,
  },
  propertyContent: {
    padding: 16,
  },
  propertyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  propertyInfo: {
    flex: 1,
    marginLeft: 16,
  },
  propertyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  propertyAddress: {
    fontSize: 14,
    color: '#64748B',
    marginBottom: 4,
  },
  propertyPrice: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2D3748',
  },
  propertyDetails: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
    paddingVertical: 12,
    backgroundColor: '#F7FAFC',
    borderRadius: 8,
  },
  propertySpec: {
    alignItems: 'center',
  },
  specValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2D3748',
  },
  specLabel: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  propertyFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusChip: {
    height: 28,
  },
  daysOnMarket: {
    fontSize: 12,
    color: '#64748B',
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
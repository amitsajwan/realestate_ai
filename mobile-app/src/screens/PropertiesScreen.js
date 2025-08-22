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
  Modal,
  Portal,
  TextInput,
  Checkbox,
} from 'react-native-paper';
import groqService from '../services/groqService';
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
  // Add Property Modal State
  const [modalVisible, setModalVisible] = useState(false);
  const [propertyTitle, setPropertyTitle] = useState('');
  const [propertyAddress, setPropertyAddress] = useState('');
  const [propertyPrice, setPropertyPrice] = useState('');
  const [propertyType, setPropertyType] = useState('');
  const [bedrooms, setBedrooms] = useState('1');
  const [bathrooms, setBathrooms] = useState('1');
  const [features, setFeatures] = useState('');
  const [contentTone, setContentTone] = useState('Professional');
  const [languages, setLanguages] = useState({
    English: false,
    Hindi: false,
    Marathi: false,
    Gujarati: false,
  });
  const [aiContent, setAiContent] = useState({});
  const [loading, setLoading] = useState(false);

  const handleAddProperty = async () => {
    setLoading(true);
    const selectedLanguages = Object.keys(languages).filter(lang => languages[lang]);
    
    if (selectedLanguages.length === 0) {
      alert('Please select at least one language.');
      setLoading(false);
      return;
    }
    
    const propertyData = {
      title: propertyTitle,
      address: propertyAddress,
      price: propertyPrice,
      type: propertyType,
      bedrooms,
      bathrooms,
      features,
      tone: contentTone,
      languages: selectedLanguages,
    };
    
    try {
      const aiResult = await groqService.generateMultiLanguagePropertyDescription(propertyData);
      setAiContent(aiResult);
    } catch (err) {
      setAiContent({ error: 'Error generating AI content.' });
    }
    setLoading(false);
  };
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [properties] = useState(SAMPLE_PROPERTIES);
  const [modalVisible, setModalVisible] = useState(false);
  const [propertyTitle, setPropertyTitle] = useState('');
  const [aiContent, setAiContent] = useState('');

  const handleAddProperty = () => {
    // Simulate AI content generation
    setAiContent(`AI-generated description for: ${propertyTitle}`);
  };
  
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
        onPress={() => setModalVisible(true)}
  {/* Removed stray closing tag */}

      <Portal>
        <Modal visible={modalVisible} onDismiss={() => setModalVisible(false)} contentContainerStyle={{ margin: 20, backgroundColor: 'white', padding: 20, borderRadius: 12, elevation: 4 }}>
          <Text style={{ fontSize: 22, fontWeight: 'bold', marginBottom: 16, color: branding.primaryColor }}>🏠 Add New Property</Text>
          <TextInput label="Property Title *" value={propertyTitle} onChangeText={setPropertyTitle} style={{ marginBottom: 10 }} mode="outlined" />
          <TextInput label="Property Address *" value={propertyAddress} onChangeText={setPropertyAddress} style={{ marginBottom: 10 }} mode="outlined" />
          <TextInput label="Price *" value={propertyPrice} onChangeText={setPropertyPrice} style={{ marginBottom: 10 }} mode="outlined" keyboardType="numeric" />
          <TextInput label="Property Type *" value={propertyType} onChangeText={setPropertyType} style={{ marginBottom: 10 }} mode="outlined" placeholder="Select Type" />
          <View style={{ flexDirection: 'row', gap: 10, marginBottom: 10 }}>
            <TextInput label="Bedrooms" value={bedrooms} onChangeText={setBedrooms} style={{ flex: 1 }} mode="outlined" keyboardType="numeric" />
            <TextInput label="Bathrooms" value={bathrooms} onChangeText={setBathrooms} style={{ flex: 1 }} mode="outlined" keyboardType="numeric" />
          </View>
          <TextInput label="Features" value={features} onChangeText={setFeatures} style={{ marginBottom: 10 }} mode="outlined" placeholder="Gym, Swimming Pool, Garden, Parking..." />
          <Text style={{ fontWeight: 'bold', marginBottom: 6 }}>Content Tone</Text>
          <View style={{ flexDirection: 'row', gap: 10, marginBottom: 10 }}>
            {['Professional', 'Friendly', 'Luxury', 'Casual'].map(tone => (
              <Button key={tone} mode={contentTone === tone ? 'contained' : 'outlined'} onPress={() => setContentTone(tone)} style={{ marginRight: 6 }}>{tone}</Button>
            ))}
          </View>
          <Text style={{ fontWeight: 'bold', marginBottom: 6 }}>Languages (Select Multiple)</Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: 10 }}>
            {Object.keys(languages).map(lang => (
              <View key={lang} style={{ flexDirection: 'row', alignItems: 'center', marginRight: 16 }}>
                <Checkbox
                  status={languages[lang] ? 'checked' : 'unchecked'}
                  onPress={() => setLanguages(prev => ({ ...prev, [lang]: !prev[lang] }))}
                  uncheckedColor="#64748B"
                  color={branding.primaryColor}
                />
                <Text style={{ marginLeft: 4 }}>{lang}</Text>
              </View>
            ))}
          </View>
          <Button mode="contained" onPress={handleAddProperty} style={{ marginBottom: 10 }} loading={loading} disabled={loading}>
            {loading ? 'Generating...' : 'Generate AI Content'}
          </Button>
          {loading && (
            <View style={{ marginBottom: 10, alignItems: 'center' }}>
              <Text style={{ color: branding.primaryColor, fontWeight: 'bold' }}>Generating AI content...</Text>
            </View>
          )}
          {Object.keys(aiContent).length > 0 && !loading && (
            <View style={{ marginBottom: 10 }}>
              <Text style={{ fontWeight: 'bold', marginBottom: 8 }}>Generated AI Descriptions</Text>
              {aiContent.error ? (
                <Text style={{ color: 'red', marginBottom: 10 }}>Failed to generate AI content. Please try again.</Text>
              ) : (
                Object.entries(aiContent).map(([language, description]) => (
                  <View key={language} style={{ marginBottom: 12 }}>
                    <Text style={{ fontWeight: 'bold', marginBottom: 4, color: branding.primaryColor }}>{language}</Text>
                    <TextInput
                      value={description}
                      multiline
                      editable={false}
                      style={{ backgroundColor: '#F7FAFC', color: 'green', minHeight: 100, maxHeight: 200, borderWidth: 1, borderColor: '#E2E8F0', borderRadius: 8, padding: 8, marginBottom: 8 }}
                      scrollEnabled
                    />
                  </View>
                ))
              )}
            </View>
          )}
          <Button mode="outlined" onPress={() => setModalVisible(false)}>
            Close
          </Button>
        </Modal>
      </Portal>
      
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
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
  ProgressBar,
} from 'react-native-paper';
import { useBranding } from '../contexts/BrandingContext';

const SAMPLE_LEADS = [
  {
    id: '1',
    name: 'Sarah Johnson',
    email: 'sarah.j@email.com',
    phone: '+1 (555) 123-4567',
    source: 'Website',
    interest: 'Downtown Condo',
    budget: '$400K - $500K',
    stage: 'qualified',
    score: 85,
    lastContact: '2 hours ago',
    notes: 'Looking for 2BR condo, first-time buyer',
  },
  {
    id: '2',
    name: 'Mike Chen',
    email: 'mike.chen@email.com',
    phone: '+1 (555) 987-6543',
    source: 'Referral',
    interest: 'Family Home',
    budget: '$300K - $400K',
    stage: 'contacted',
    score: 92,
    lastContact: '1 day ago',
    notes: 'Growing family, needs 3BR with yard',
  },
  {
    id: '3',
    name: 'Emma Wilson',
    email: 'emma.w@email.com',
    phone: '+1 (555) 456-7890',
    source: 'Facebook',
    interest: 'Investment Property',
    budget: '$200K - $350K',
    stage: 'new',
    score: 67,
    lastContact: 'Never',
    notes: 'Investor looking for rental properties',
  },
];

const STAGE_FILTERS = [
  { key: 'all', label: 'All', color: '#64748B' },
  { key: 'new', label: 'New', color: '#3182CE' },
  { key: 'contacted', label: 'Contacted', color: '#F18F01' },
  { key: 'qualified', label: 'Qualified', color: '#38A169' },
  { key: 'nurturing', label: 'Nurturing', color: '#9F7AEA' },
];

export default function LeadsScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [leads] = useState(SAMPLE_LEADS);
  
  const { branding } = useBranding();

  const getStageColor = (stage) => {
    switch (stage) {
      case 'new': return '#3182CE';
      case 'contacted': return '#F18F01';
      case 'qualified': return '#38A169';
      case 'nurturing': return '#9F7AEA';
      default: return '#64748B';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#38A169';
    if (score >= 60) return '#F18F01';
    return '#E53E3E';
  };

  const filteredLeads = leads.filter(lead => {
    const matchesSearch = lead.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         lead.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         lead.interest.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = selectedFilter === 'all' || lead.stage === selectedFilter;
    return matchesSearch && matchesFilter;
  });

  const renderLead = ({ item }) => (
    <Card style={styles.leadCard}>
      <View style={styles.leadContent}>
        <View style={styles.leadHeader}>
          <Avatar.Text
            size={50}
            label={item.name.split(' ').map(n => n[0]).join('')}
            style={{ backgroundColor: branding.primaryColor + '20' }}
            labelStyle={{ color: branding.primaryColor }}
          />
          <View style={styles.leadInfo}>
            <Text style={styles.leadName}>{item.name}</Text>
            <Text style={styles.leadContact}>{item.email}</Text>
            <Text style={styles.leadPhone}>{item.phone}</Text>
          </View>
          <View style={styles.leadScore}>
            <Text style={[styles.scoreText, { color: getScoreColor(item.score) }]}>
              {item.score}
            </Text>
            <Text style={styles.scoreLabel}>Score</Text>
          </View>
        </View>
        
        <View style={styles.leadDetails}>
          <View style={styles.leadRow}>
            <Text style={styles.leadLabel}>Interest:</Text>
            <Text style={styles.leadValue}>{item.interest}</Text>
          </View>
          <View style={styles.leadRow}>
            <Text style={styles.leadLabel}>Budget:</Text>
            <Text style={styles.leadValue}>{item.budget}</Text>
          </View>
          <View style={styles.leadRow}>
            <Text style={styles.leadLabel}>Source:</Text>
            <Text style={styles.leadValue}>{item.source}</Text>
          </View>
          <View style={styles.leadRow}>
            <Text style={styles.leadLabel}>Last Contact:</Text>
            <Text style={styles.leadValue}>{item.lastContact}</Text>
          </View>
        </View>

        {item.notes && (
          <View style={styles.notesContainer}>
            <Text style={styles.notesLabel}>Notes:</Text>
            <Text style={styles.notesText}>{item.notes}</Text>
          </View>
        )}

        <View style={styles.leadFooter}>
          <Chip
            compact
            style={[
              styles.stageChip,
              { backgroundColor: getStageColor(item.stage) + '20' }
            ]}
            textStyle={{ color: getStageColor(item.stage) }}
          >
            {item.stage.charAt(0).toUpperCase() + item.stage.slice(1)}
          </Chip>
          
          <View style={styles.leadActions}>
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
              icon="message-text"
              size={20}
              iconColor={branding.primaryColor}
              onPress={() => {
                // Handle message
              }}
            />
          </View>
        </View>

        {/* Lead Score Progress */}
        <View style={styles.progressContainer}>
          <Text style={styles.progressLabel}>Lead Quality</Text>
          <ProgressBar
            progress={item.score / 100}
            color={getScoreColor(item.score)}
            style={styles.progressBar}
          />
        </View>
      </View>
    </Card>
  );

  return (
    <View style={[styles.container, { backgroundColor: branding.backgroundColor }]}>
      <View style={styles.header}>
        <Searchbar
          placeholder="Search leads..."
          onChangeText={setSearchQuery}
          value={searchQuery}
          style={styles.searchbar}
        />
        
        <View style={styles.filters}>
          {STAGE_FILTERS.map((filter) => (
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
        data={filteredLeads}
        renderItem={renderLead}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateText}>No leads found</Text>
          </View>
        }
      />

      <FAB
        icon="plus"
        style={[styles.fab, { backgroundColor: branding.primaryColor }]}
        onPress={() => {
          // Handle add lead
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
  leadCard: {
    marginBottom: 16,
    borderRadius: 12,
  },
  leadContent: {
    padding: 16,
  },
  leadHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  leadInfo: {
    flex: 1,
    marginLeft: 16,
  },
  leadName: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  leadContact: {
    fontSize: 14,
    color: '#64748B',
    marginBottom: 2,
  },
  leadPhone: {
    fontSize: 14,
    color: '#64748B',
  },
  leadScore: {
    alignItems: 'center',
  },
  scoreText: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  scoreLabel: {
    fontSize: 12,
    color: '#64748B',
  },
  leadDetails: {
    marginBottom: 16,
  },
  leadRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  leadLabel: {
    fontSize: 14,
    color: '#64748B',
    fontWeight: '500',
  },
  leadValue: {
    fontSize: 14,
    color: '#2D3748',
  },
  notesContainer: {
    backgroundColor: '#F7FAFC',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  notesLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#64748B',
    marginBottom: 4,
  },
  notesText: {
    fontSize: 14,
    color: '#2D3748',
  },
  leadFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  stageChip: {
    height: 28,
  },
  leadActions: {
    flexDirection: 'row',
  },
  progressContainer: {
    marginTop: 8,
  },
  progressLabel: {
    fontSize: 12,
    color: '#64748B',
    marginBottom: 4,
  },
  progressBar: {
    height: 6,
    borderRadius: 3,
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
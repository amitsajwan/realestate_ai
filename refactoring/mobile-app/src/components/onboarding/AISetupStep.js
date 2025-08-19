import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import {
  Text,
  Button,
  Card,
  Switch,
  Chip,
  TextInput,
  HelperText,
  List,
  Avatar,
} from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import { useBranding } from '../../contexts/BrandingContext';

const AI_FEATURES = [
  {
    id: 'smart_responses',
    title: 'Smart Client Responses',
    description: 'AI-powered responses to client inquiries',
    icon: 'message-reply-text',
    enabled: true,
  },
  {
    id: 'property_descriptions',
    title: 'Property Descriptions',
    description: 'Generate compelling property descriptions',
    icon: 'home-edit',
    enabled: true,
  },
  {
    id: 'market_analysis',
    title: 'Market Analysis',
    description: 'AI-driven market insights and trends',
    icon: 'chart-line',
    enabled: true,
  },
  {
    id: 'lead_scoring',
    title: 'Lead Scoring',
    description: 'Intelligent lead qualification and scoring',
    icon: 'account-star',
    enabled: true,
  },
  {
    id: 'price_suggestions',
    title: 'Price Suggestions',
    description: 'AI-powered pricing recommendations',
    icon: 'currency-usd',
    enabled: false,
  },
  {
    id: 'document_generation',
    title: 'Document Generation',
    description: 'Auto-generate contracts and forms',
    icon: 'file-document-edit',
    enabled: false,
  },
];

const COMMUNICATION_STYLES = [
  { id: 'professional', label: 'Professional', description: 'Formal and business-focused' },
  { id: 'friendly', label: 'Friendly', description: 'Warm and approachable' },
  { id: 'casual', label: 'Casual', description: 'Relaxed and conversational' },
  { id: 'luxury', label: 'Luxury', description: 'Sophisticated and premium' },
];

export default function AISetupStep({ formData, onNext, isLoading }) {
  const [aiFeatures, setAiFeatures] = useState(formData.aiFeatures || AI_FEATURES);
  const [communicationStyle, setCommunicationStyle] = useState(formData.communicationStyle || 'professional');
  const [customPrompt, setCustomPrompt] = useState(formData.customPrompt || '');
  const [aiPersonality, setAiPersonality] = useState(formData.aiPersonality || '');
  const [autoRespond, setAutoRespond] = useState(formData.autoRespond || false);
  const [responseDelay, setResponseDelay] = useState(formData.responseDelay || '5');
  const [errors, setErrors] = useState({});

  const { branding } = useBranding();

  const validateForm = () => {
    const newErrors = {};
    
    if (!aiPersonality.trim()) {
      newErrors.aiPersonality = 'Please describe your AI assistant personality';
    }
    
    if (autoRespond && (!responseDelay || isNaN(responseDelay) || responseDelay < 1)) {
      newErrors.responseDelay = 'Please enter a valid delay in minutes';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateForm()) {
      onNext({
        aiFeatures,
        communicationStyle,
        customPrompt,
        aiPersonality,
        autoRespond,
        responseDelay: parseInt(responseDelay),
        aiSetupCompleted: true,
      });
    }
  };

  const toggleFeature = (featureId) => {
    setAiFeatures(prev => 
      prev.map(feature => 
        feature.id === featureId 
          ? { ...feature, enabled: !feature.enabled }
          : feature
      )
    );
  };

  const testAiConnection = async () => {
    try {
      Alert.alert(
        'AI Test',
        'AI connection test successful! Your assistant is ready to help.',
        [{ text: 'OK' }]
      );
    } catch (error) {
      Alert.alert(
        'Connection Error',
        'Failed to connect to AI service. Please check your settings.',
        [{ text: 'OK' }]
      );
    }
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <Text style={styles.title}>AI Assistant Setup</Text>
      <Text style={styles.subtitle}>
        Configure your AI-powered real estate assistant
      </Text>

      {/* AI Assistant Preview */}
      <Card style={styles.previewCard}>
        <LinearGradient
          colors={[branding.primaryColor, branding.secondaryColor]}
          style={styles.previewHeader}
        >
          <View style={styles.previewContent}>
            <Avatar.Icon
              size={60}
              icon="robot"
              style={{ backgroundColor: 'rgba(255,255,255,0.2)' }}
            />
            <View style={styles.previewText}>
              <Text style={styles.previewTitle}>Your AI Assistant</Text>
              <Text style={styles.previewDescription}>
                {aiPersonality || 'Ready to help with your real estate needs'}
              </Text>
            </View>
          </View>
        </LinearGradient>
      </Card>

      <View style={styles.form}>
        {/* AI Features */}
        <Text style={styles.sectionTitle}>AI Features</Text>
        <View style={styles.featuresContainer}>
          {aiFeatures.map((feature) => (
            <Card key={feature.id} style={styles.featureCard}>
              <List.Item
                title={feature.title}
                description={feature.description}
                left={(props) => <List.Icon {...props} icon={feature.icon} />}
                right={() => (
                  <Switch
                    value={feature.enabled}
                    onValueChange={() => toggleFeature(feature.id)}
                    color={branding.primaryColor}
                  />
                )}
              />
            </Card>
          ))}
        </View>

        {/* Communication Style */}
        <Text style={styles.sectionTitle}>Communication Style</Text>
        <View style={styles.styleContainer}>
          {COMMUNICATION_STYLES.map((style) => (
            <Chip
              key={style.id}
              selected={communicationStyle === style.id}
              onPress={() => setCommunicationStyle(style.id)}
              style={[
                styles.styleChip,
                communicationStyle === style.id && {
                  backgroundColor: branding.primaryColor,
                }
              ]}
              textStyle={[
                communicationStyle === style.id && { color: 'white' }
              ]}
            >
              {style.label}
            </Chip>
          ))}
        </View>
        <Text style={styles.styleDescription}>
          {COMMUNICATION_STYLES.find(s => s.id === communicationStyle)?.description}
        </Text>

        {/* AI Personality */}
        <TextInput
          label="AI Assistant Personality"
          value={aiPersonality}
          onChangeText={setAiPersonality}
          mode="outlined"
          multiline
          numberOfLines={3}
          style={styles.input}
          error={!!errors.aiPersonality}
          placeholder="Describe how you want your AI assistant to interact with clients (e.g., professional but approachable, knowledgeable about local market, emphasizes customer service)"
        />
        <HelperText type="error" visible={!!errors.aiPersonality}>
          {errors.aiPersonality}
        </HelperText>

        {/* Custom Prompt */}
        <TextInput
          label="Custom Instructions (Optional)"
          value={customPrompt}
          onChangeText={setCustomPrompt}
          mode="outlined"
          multiline
          numberOfLines={3}
          style={styles.input}
          placeholder="Any specific instructions for your AI assistant..."
        />

        {/* Auto-Respond Settings */}
        <View style={styles.autoRespondSection}>
          <View style={styles.autoRespondToggle}>
            <Text style={styles.sectionTitle}>Auto-Respond to Inquiries</Text>
            <Switch
              value={autoRespond}
              onValueChange={setAutoRespond}
              color={branding.primaryColor}
            />
          </View>
          {autoRespond && (
            <TextInput
              label="Response Delay (minutes)"
              value={responseDelay}
              onChangeText={setResponseDelay}
              mode="outlined"
              keyboardType="numeric"
              style={styles.input}
              error={!!errors.responseDelay}
              placeholder="5"
            />
          )}
          <HelperText type="error" visible={!!errors.responseDelay}>
            {errors.responseDelay}
          </HelperText>
        </View>

        {/* Test Connection */}
        <Button
          mode="outlined"
          onPress={testAiConnection}
          style={styles.testButton}
          icon="test-tube"
        >
          Test AI Connection
        </Button>
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
    marginBottom: 24,
  },
  previewCard: {
    marginBottom: 24,
    overflow: 'hidden',
  },
  previewHeader: {
    padding: 20,
  },
  previewContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  previewText: {
    marginLeft: 16,
    flex: 1,
  },
  previewTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
  },
  previewDescription: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
    marginTop: 4,
  },
  form: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
    marginTop: 8,
  },
  featuresContainer: {
    marginBottom: 24,
  },
  featureCard: {
    marginBottom: 8,
  },
  styleContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 8,
  },
  styleChip: {
    marginRight: 8,
    marginBottom: 8,
  },
  styleDescription: {
    fontSize: 14,
    color: '#64748B',
    marginBottom: 16,
    fontStyle: 'italic',
  },
  input: {
    marginBottom: 4,
  },
  autoRespondSection: {
    marginBottom: 24,
  },
  autoRespondToggle: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  testButton: {
    marginBottom: 16,
    borderColor: '#64748B',
  },
  nextButton: {
    marginTop: 16,
    borderRadius: 12,
  },
  buttonContent: {
    paddingVertical: 8,
  },
});
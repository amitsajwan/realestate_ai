import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import {
  Text,
  TextInput,
  Button,
  HelperText,
  Card,
  Chip,
  IconButton,
  Avatar,
  Switch,
} from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import * as ImagePicker from 'expo-image-picker';
import { useBranding } from '../../contexts/BrandingContext';

const PRESET_COLORS = [
  '#2E86AB', '#A23B72', '#F18F01', '#C73E1D',
  '#16A085', '#8E44AD', '#2980B9', '#F39C12',
  '#E74C3C', '#27AE60', '#9B59B6', '#3498DB',
];

const BRAND_TAGS = [
  'Luxury', 'Affordable', 'Family-Friendly', 'Investment',
  'First-Time Buyers', 'Commercial', 'Waterfront', 'Historic',
  'Modern', 'Eco-Friendly', 'Downtown', 'Suburban',
  'Rural', 'High-End', 'Budget-Friendly', 'Quick Sale',
];

export default function BrandingStep({ formData, onNext, isLoading }) {
  const [companyName, setCompanyName] = useState(formData.companyName || '');
  const [tagline, setTagline] = useState(formData.tagline || '');
  const [logo, setLogo] = useState(formData.logo || null);
  const [primaryColor, setPrimaryColor] = useState(formData.primaryColor || '#2E86AB');
  const [selectedTags, setSelectedTags] = useState(formData.brandTags || []);
  const [isDarkTheme, setIsDarkTheme] = useState(formData.isDarkTheme || false);
  const [errors, setErrors] = useState({});

  const { branding, updateBranding, generateColorPalette } = useBranding();

  useEffect(() => {
    // Update branding context as user makes changes
    const colorPalette = generateColorPalette(primaryColor);
    updateBranding({
      primaryColor,
      ...colorPalette,
      companyName,
      tagline,
      logo,
      tags: selectedTags,
      theme: isDarkTheme ? 'dark' : 'light',
    });
  }, [primaryColor, companyName, tagline, logo, selectedTags, isDarkTheme]);

  const validateForm = () => {
    const newErrors = {};
    
    if (!companyName.trim()) newErrors.companyName = 'Company name is required';
    if (!tagline.trim()) newErrors.tagline = 'Tagline is required';
    if (selectedTags.length === 0) newErrors.tags = 'Please select at least one brand tag';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateForm()) {
      onNext({
        companyName,
        tagline,
        logo,
        primaryColor,
        brandTags: selectedTags,
        isDarkTheme,
        brandingCompleted: true,
      });
    }
  };

  const pickLogo = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
      });

      if (!result.canceled) {
        setLogo(result.assets[0].uri);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to pick image. Please try again.');
    }
  };

  const toggleTag = (tag) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const ColorPicker = ({ colors, selectedColor, onColorSelect }) => (
    <View style={styles.colorPicker}>
      {colors.map((color) => (
        <TouchableOpacity
          key={color}
          style={[
            styles.colorOption,
            { backgroundColor: color },
            selectedColor === color && styles.selectedColor,
          ]}
          onPress={() => onColorSelect(color)}
        />
      ))}
    </View>
  );

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <Text style={styles.title}>Build Your Brand Identity</Text>
      <Text style={styles.subtitle}>
        Customize how your brand appears to clients
      </Text>

      {/* Brand Preview Card */}
      <Card style={styles.previewCard}>
        <LinearGradient
          colors={[primaryColor, branding.secondaryColor]}
          style={styles.previewHeader}
        >
          <View style={styles.previewContent}>
            {logo ? (
              <Avatar.Image size={60} source={{ uri: logo }} />
            ) : (
              <Avatar.Text
                size={60}
                label={companyName.substring(0, 2).toUpperCase()}
                style={{ backgroundColor: 'rgba(255,255,255,0.2)' }}
                labelStyle={{ color: 'white' }}
              />
            )}
            <View style={styles.previewText}>
              <Text style={styles.previewCompanyName}>
                {companyName || 'Your Company Name'}
              </Text>
              <Text style={styles.previewTagline}>
                {tagline || 'Your tagline here'}
              </Text>
            </View>
          </View>
        </LinearGradient>
        <View style={styles.previewTags}>
          {selectedTags.slice(0, 3).map((tag) => (
            <Chip
              key={tag}
              compact
              style={[styles.previewTag, { backgroundColor: primaryColor + '20' }]}
              textStyle={{ color: primaryColor }}
            >
              {tag}
            </Chip>
          ))}
        </View>
      </Card>

      <View style={styles.form}>
        <TextInput
          label="Company/Brand Name"
          value={companyName}
          onChangeText={setCompanyName}
          mode="outlined"
          style={styles.input}
          error={!!errors.companyName}
        />
        <HelperText type="error" visible={!!errors.companyName}>
          {errors.companyName}
        </HelperText>

        <TextInput
          label="Tagline"
          value={tagline}
          onChangeText={setTagline}
          mode="outlined"
          style={styles.input}
          error={!!errors.tagline}
          placeholder="e.g., 'Making Dreams Come Home'"
        />
        <HelperText type="error" visible={!!errors.tagline}>
          {errors.tagline}
        </HelperText>

        <View style={styles.logoSection}>
          <Text style={styles.sectionTitle}>Logo</Text>
          <TouchableOpacity style={styles.logoUpload} onPress={pickLogo}>
            {logo ? (
              <Avatar.Image size={80} source={{ uri: logo }} />
            ) : (
              <View style={styles.logoPlaceholder}>
                <IconButton icon="camera-plus" size={32} />
                <Text>Add Logo</Text>
              </View>
            )}
          </TouchableOpacity>
        </View>

        <View style={styles.colorSection}>
          <Text style={styles.sectionTitle}>Primary Color</Text>
          <ColorPicker
            colors={PRESET_COLORS}
            selectedColor={primaryColor}
            onColorSelect={setPrimaryColor}
          />
        </View>

        <View style={styles.tagsSection}>
          <Text style={styles.sectionTitle}>Brand Tags</Text>
          <View style={styles.chipContainer}>
            {BRAND_TAGS.map((tag) => (
              <Chip
                key={tag}
                selected={selectedTags.includes(tag)}
                onPress={() => toggleTag(tag)}
                style={[
                  styles.chip,
                  selectedTags.includes(tag) && {
                    backgroundColor: primaryColor,
                  }
                ]}
                textStyle={[
                  selectedTags.includes(tag) && { color: 'white' }
                ]}
              >
                {tag}
              </Chip>
            ))}
          </View>
          <HelperText type="error" visible={!!errors.tags}>
            {errors.tags}
          </HelperText>
        </View>

        <View style={styles.themeSection}>
          <View style={styles.themeToggle}>
            <Text style={styles.sectionTitle}>Dark Theme</Text>
            <Switch
              value={isDarkTheme}
              onValueChange={setIsDarkTheme}
              color={primaryColor}
            />
          </View>
        </View>
      </View>

      <Button
        mode="contained"
        onPress={handleNext}
        loading={isLoading}
        disabled={isLoading}
        style={[styles.nextButton, { backgroundColor: primaryColor }]}
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
  previewCompanyName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
  },
  previewTagline: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.9)',
    marginTop: 4,
  },
  previewTags: {
    flexDirection: 'row',
    padding: 16,
    gap: 8,
  },
  previewTag: {
    height: 28,
  },
  form: {
    marginBottom: 32,
  },
  input: {
    marginBottom: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
    marginTop: 8,
  },
  logoSection: {
    marginBottom: 24,
  },
  logoUpload: {
    alignItems: 'center',
  },
  logoPlaceholder: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 2,
    borderColor: '#E2E8F0',
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
  },
  colorSection: {
    marginBottom: 24,
  },
  colorPicker: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  colorOption: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 3,
    borderColor: 'transparent',
  },
  selectedColor: {
    borderColor: '#2D3748',
  },
  tagsSection: {
    marginBottom: 24,
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 4,
  },
  chip: {
    marginRight: 8,
    marginBottom: 8,
  },
  themeSection: {
    marginBottom: 24,
  },
  themeToggle: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  nextButton: {
    marginTop: 16,
    borderRadius: 12,
  },
  buttonContent: {
    paddingVertical: 8,
  },
});
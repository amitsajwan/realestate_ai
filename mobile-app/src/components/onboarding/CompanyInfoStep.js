import React, { useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import {
  Text,
  TextInput,
  Button,
  HelperText,
  Chip,
  Menu,
  Divider,
} from 'react-native-paper';
import { useBranding } from '../../contexts/BrandingContext';

const PROPERTY_TYPES = [
  'Residential',
  'Commercial',
  'Industrial',
  'Land',
  'Luxury',
  'Investment',
  'Rental',
  'New Construction',
];

const EXPERIENCE_LEVELS = [
  { label: 'New Agent (0-1 years)', value: 'new' },
  { label: 'Experienced (2-5 years)', value: 'experienced' },
  { label: 'Senior (6-10 years)', value: 'senior' },
  { label: 'Expert (10+ years)', value: 'expert' },
];

export default function CompanyInfoStep({ formData, onNext, isLoading }) {
  const [companyName, setCompanyName] = useState(formData.companyName || '');
  const [licenseNumber, setLicenseNumber] = useState(formData.licenseNumber || '');
  const [yearsExperience, setYearsExperience] = useState(formData.yearsExperience || '');
  const [specializations, setSpecializations] = useState(formData.specializations || []);
  const [bio, setBio] = useState(formData.bio || '');
  const [website, setWebsite] = useState(formData.website || '');
  const [errors, setErrors] = useState({});
  const [experienceMenuVisible, setExperienceMenuVisible] = useState(false);

  const { branding } = useBranding();

  const validateForm = () => {
    const newErrors = {};
    
    if (!companyName.trim()) newErrors.companyName = 'Company name is required';
    if (!licenseNumber.trim()) newErrors.licenseNumber = 'License number is required';
    if (!yearsExperience) newErrors.yearsExperience = 'Experience level is required';
    if (specializations.length === 0) newErrors.specializations = 'Please select at least one specialization';
    if (!bio.trim()) newErrors.bio = 'Professional bio is required';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateForm()) {
      onNext({
        companyName,
        licenseNumber,
        yearsExperience,
        specializations,
        bio,
        website,
      });
    }
  };

  const toggleSpecialization = (type) => {
    setSpecializations(prev => 
      prev.includes(type) 
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  const getExperienceLabel = () => {
    const experience = EXPERIENCE_LEVELS.find(exp => exp.value === yearsExperience);
    return experience ? experience.label : 'Select experience level';
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <Text style={styles.title}>Company & Professional Info</Text>
      <Text style={styles.subtitle}>
        Help us understand your professional background
      </Text>

      <View style={styles.form}>
        <TextInput
          label="Company/Brokerage Name"
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
          label="Real Estate License Number"
          value={licenseNumber}
          onChangeText={setLicenseNumber}
          mode="outlined"
          style={styles.input}
          error={!!errors.licenseNumber}
        />
        <HelperText type="error" visible={!!errors.licenseNumber}>
          {errors.licenseNumber}
        </HelperText>

        <Menu
          visible={experienceMenuVisible}
          onDismiss={() => setExperienceMenuVisible(false)}
          anchor={
            <TextInput
              label="Years of Experience"
              value={getExperienceLabel()}
              mode="outlined"
              style={styles.input}
              error={!!errors.yearsExperience}
              onFocus={() => setExperienceMenuVisible(true)}
              showSoftInputOnFocus={false}
              right={<TextInput.Icon icon="chevron-down" />}
            />
          }
        >
          {EXPERIENCE_LEVELS.map((exp) => (
            <Menu.Item
              key={exp.value}
              onPress={() => {
                setYearsExperience(exp.value);
                setExperienceMenuVisible(false);
              }}
              title={exp.label}
            />
          ))}
        </Menu>
        <HelperText type="error" visible={!!errors.yearsExperience}>
          {errors.yearsExperience}
        </HelperText>

        <Text style={styles.sectionTitle}>Property Specializations</Text>
        <View style={styles.chipContainer}>
          {PROPERTY_TYPES.map((type) => (
            <Chip
              key={type}
              selected={specializations.includes(type)}
              onPress={() => toggleSpecialization(type)}
              style={[
                styles.chip,
                specializations.includes(type) && {
                  backgroundColor: branding.primaryColor,
                }
              ]}
              textStyle={[
                specializations.includes(type) && { color: 'white' }
              ]}
            >
              {type}
            </Chip>
          ))}
        </View>
        <HelperText type="error" visible={!!errors.specializations}>
          {errors.specializations}
        </HelperText>

        <TextInput
          label="Professional Bio"
          value={bio}
          onChangeText={setBio}
          mode="outlined"
          multiline
          numberOfLines={4}
          style={styles.input}
          error={!!errors.bio}
          placeholder="Tell clients about your experience, achievements, and what makes you unique..."
        />
        <HelperText type="error" visible={!!errors.bio}>
          {errors.bio}
        </HelperText>

        <TextInput
          label="Website (Optional)"
          value={website}
          onChangeText={setWebsite}
          mode="outlined"
          keyboardType="url"
          autoCapitalize="none"
          style={styles.input}
          placeholder="https://yourwebsite.com"
        />
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
  input: {
    marginBottom: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
    marginTop: 8,
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
  nextButton: {
    marginTop: 16,
    borderRadius: 12,
  },
  buttonContent: {
    paddingVertical: 8,
  },
});
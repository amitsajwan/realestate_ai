import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import {
  Text,
  TextInput,
  Button,
  HelperText,
  Avatar,
  IconButton,
} from 'react-native-paper';
import * as ImagePicker from 'expo-image-picker';
import { useBranding } from '../../contexts/BrandingContext';

export default function PersonalInfoStep({ formData, onNext, isLoading }) {
  const [firstName, setFirstName] = useState(formData.firstName || '');
  const [lastName, setLastName] = useState(formData.lastName || '');
  const [email, setEmail] = useState(formData.email || '');
  const [phone, setPhone] = useState(formData.phone || '');
  const [profileImage, setProfileImage] = useState(formData.profileImage || null);
  const [errors, setErrors] = useState({});

  const { branding } = useBranding();

  const validateForm = () => {
    const newErrors = {};
    
    if (!firstName.trim()) newErrors.firstName = 'First name is required';
    if (!lastName.trim()) newErrors.lastName = 'Last name is required';
    if (!email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Please enter a valid email';
    }
    if (!phone.trim()) {
      newErrors.phone = 'Phone number is required';
    } else if (!/^\+?[\d\s-()]+$/.test(phone)) {
      newErrors.phone = 'Please enter a valid phone number';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateForm()) {
      onNext({
        firstName,
        lastName,
        email,
        phone,
        profileImage,
      });
    }
  };

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });

    if (!result.canceled) {
      setProfileImage(result.assets[0].uri);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Let's get to know you</Text>
      <Text style={styles.subtitle}>
        Tell us about yourself to create your agent profile
      </Text>

      <View style={styles.profileImageContainer}>
        <Avatar.Image
          size={100}
          source={profileImage ? { uri: profileImage } : undefined}
          style={[styles.avatar, { backgroundColor: branding.primaryColor }]}
        />
        <IconButton
          icon="camera"
          size={24}
          iconColor={branding.primaryColor}
          containerColor="white"
          style={styles.cameraButton}
          onPress={pickImage}
        />
      </View>

      <View style={styles.form}>
        <TextInput
          label="First Name"
          value={firstName}
          onChangeText={setFirstName}
          mode="outlined"
          style={styles.input}
          error={!!errors.firstName}
        />
        <HelperText type="error" visible={!!errors.firstName}>
          {errors.firstName}
        </HelperText>

        <TextInput
          label="Last Name"
          value={lastName}
          onChangeText={setLastName}
          mode="outlined"
          style={styles.input}
          error={!!errors.lastName}
        />
        <HelperText type="error" visible={!!errors.lastName}>
          {errors.lastName}
        </HelperText>

        <TextInput
          label="Email Address"
          value={email}
          onChangeText={setEmail}
          mode="outlined"
          keyboardType="email-address"
          autoCapitalize="none"
          style={styles.input}
          error={!!errors.email}
        />
        <HelperText type="error" visible={!!errors.email}>
          {errors.email}
        </HelperText>

        <TextInput
          label="Phone Number"
          value={phone}
          onChangeText={setPhone}
          mode="outlined"
          keyboardType="phone-pad"
          style={styles.input}
          error={!!errors.phone}
        />
        <HelperText type="error" visible={!!errors.phone}>
          {errors.phone}
        </HelperText>
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
    </View>
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
  profileImageContainer: {
    alignItems: 'center',
    marginBottom: 32,
    position: 'relative',
  },
  avatar: {
    marginBottom: 16,
  },
  cameraButton: {
    position: 'absolute',
    bottom: 8,
    right: '35%',
    elevation: 4,
  },
  form: {
    marginBottom: 32,
  },
  input: {
    marginBottom: 4,
  },
  nextButton: {
    marginTop: 'auto',
    borderRadius: 12,
  },
  buttonContent: {
    paddingVertical: 8,
  },
});
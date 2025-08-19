import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Dimensions,
  Animated,
  Pressable,
  Alert,
  StatusBar,
  Platform,
  Image,
} from 'react-native';
import {
  Text,
  TextInput,
  Button,
  Card,
  Surface,
  IconButton,
  Chip,
  ProgressBar,
  Avatar,
  FAB,
  Portal,
  Modal,
} from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import * as Animatable from 'react-native-animatable';
import * as Haptics from 'expo-haptics';
import * as ImagePicker from 'expo-image-picker';
import * as DocumentPicker from 'expo-document-picker';
import { BlurView } from 'expo-blur';
import { KeyboardAwareScrollView } from 'react-native-keyboard-aware-scroll-view';
import { useBranding } from '../contexts/BrandingContext';
import { useAuth } from '../contexts/AuthContext';
import groqService from '../services/groqService';

const { width, height } = Dimensions.get('window');

const PROPERTY_TYPES = [
  { id: 'house', label: 'House', icon: '🏠' },
  { id: 'condo', label: 'Condo', icon: '🏢' },
  { id: 'townhouse', label: 'Townhouse', icon: '🏘️' },
  { id: 'apartment', label: 'Apartment', icon: '🏨' },
  { id: 'land', label: 'Land', icon: '🌾' },
  { id: 'commercial', label: 'Commercial', icon: '🏪' },
];

const LISTING_TYPES = [
  { id: 'sale', label: 'For Sale', icon: '💰', color: '#38A169' },
  { id: 'rent', label: 'For Rent', icon: '🔑', color: '#3182CE' },
  { id: 'sold', label: 'Sold', icon: '✅', color: '#9F7AEA' },
];

const POSTING_STEPS = [
  { id: 'basics', title: 'Property Basics', icon: 'home' },
  { id: 'details', title: 'Details & Features', icon: 'format-list-bulleted' },
  { id: 'media', title: 'Photos & Documents', icon: 'camera' },
  { id: 'description', title: 'AI Description', icon: 'robot' },
  { id: 'pricing', title: 'Pricing & Terms', icon: 'currency-usd' },
  { id: 'review', title: 'Review & Publish', icon: 'check-circle' },
];

export default function PostingScreen({ navigation, route }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [showAIModal, setShowAIModal] = useState(false);
  const [aiGenerating, setAiGenerating] = useState(false);
  
  // Form data
  const [formData, setFormData] = useState({
    // Basics
    title: '',
    propertyType: '',
    listingType: '',
    address: '',
    city: '',
    state: '',
    zipCode: '',
    
    // Details
    bedrooms: '',
    bathrooms: '',
    sqft: '',
    lotSize: '',
    yearBuilt: '',
    features: [],
    
    // Media
    images: [],
    documents: [],
    
    // Description
    description: '',
    highlights: [],
    
    // Pricing
    price: '',
    priceType: 'fixed', // fixed, negotiable, auction
    terms: '',
    availability: '',
  });

  const [errors, setErrors] = useState({});
  
  // Animation refs
  const progressAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(1)).current;

  const { branding } = useBranding();
  const { user } = useAuth();

  useEffect(() => {
    // Animate progress
    Animated.timing(progressAnim, {
      toValue: (currentStep + 1) / POSTING_STEPS.length,
      duration: 300,
      useNativeDriver: false,
    }).start();
  }, [currentStep]);

  const handleNext = async () => {
    if (!validateCurrentStep()) return;
    
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    
    if (currentStep < POSTING_STEPS.length - 1) {
      // Slide transition
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 0.3,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.timing(slideAnim, {
          toValue: -20,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start(() => {
        setCurrentStep(currentStep + 1);
        Animated.parallel([
          Animated.timing(fadeAnim, {
            toValue: 1,
            duration: 300,
            useNativeDriver: true,
          }),
          Animated.timing(slideAnim, {
            toValue: 0,
            duration: 300,
            useNativeDriver: true,
          }),
        ]).start();
      });
    } else {
      handlePublish();
    }
  };

  const handleBack = async () => {
    if (currentStep > 0) {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      setCurrentStep(currentStep - 1);
    } else {
      navigation.goBack();
    }
  };

  const validateCurrentStep = () => {
    const newErrors = {};
    
    switch (currentStep) {
      case 0: // Basics
        if (!formData.title.trim()) newErrors.title = 'Property title is required';
        if (!formData.propertyType) newErrors.propertyType = 'Property type is required';
        if (!formData.listingType) newErrors.listingType = 'Listing type is required';
        if (!formData.address.trim()) newErrors.address = 'Address is required';
        break;
      case 1: // Details
        if (!formData.bedrooms) newErrors.bedrooms = 'Bedrooms is required';
        if (!formData.bathrooms) newErrors.bathrooms = 'Bathrooms is required';
        if (!formData.sqft) newErrors.sqft = 'Square footage is required';
        break;
      case 4: // Pricing
        if (!formData.price) newErrors.price = 'Price is required';
        break;
    }
    
    setErrors(newErrors);
    
    if (Object.keys(newErrors).length > 0) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      // Shake animation
      Animated.sequence([
        Animated.timing(slideAnim, { toValue: -10, duration: 100, useNativeDriver: true }),
        Animated.timing(slideAnim, { toValue: 10, duration: 100, useNativeDriver: true }),
        Animated.timing(slideAnim, { toValue: 0, duration: 100, useNativeDriver: true }),
      ]).start();
    }
    
    return Object.keys(newErrors).length === 0;
  };

  const handleImagePicker = async () => {
    try {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsMultipleSelection: true,
        quality: 0.8,
        aspect: [16, 9],
      });

      if (!result.canceled) {
        setFormData(prev => ({
          ...prev,
          images: [...prev.images, ...result.assets],
        }));
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to pick images');
    }
  };

  const handleCameraPicker = async () => {
    try {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.8,
        aspect: [16, 9],
      });

      if (!result.canceled) {
        setFormData(prev => ({
          ...prev,
          images: [...prev.images, result.assets[0]],
        }));
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to take photo');
    }
  };

  const generateAIDescription = async () => {
    try {
      setAiGenerating(true);
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      
      const propertyData = {
        type: formData.propertyType,
        bedrooms: formData.bedrooms,
        bathrooms: formData.bathrooms,
        sqft: formData.sqft,
        location: `${formData.city}, ${formData.state}`,
        features: formData.features,
        price: formData.price,
      };

      const description = await groqService.generatePropertyDescription(propertyData);
      
      setFormData(prev => ({
        ...prev,
        description,
      }));
      
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setShowAIModal(false);
    } catch (error) {
      Alert.alert('AI Error', 'Failed to generate description. Please try again.');
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setAiGenerating(false);
    }
  };

  const handlePublish = async () => {
    try {
      setIsLoading(true);
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      
      Alert.alert(
        'Success!',
        'Your property has been published successfully.',
        [
          {
            text: 'View Listing',
            onPress: () => navigation.navigate('Properties'),
          },
          {
            text: 'Create Another',
            onPress: () => {
              setCurrentStep(0);
              setFormData({
                title: '', propertyType: '', listingType: '', address: '',
                city: '', state: '', zipCode: '', bedrooms: '', bathrooms: '',
                sqft: '', lotSize: '', yearBuilt: '', features: [], images: [],
                documents: [], description: '', highlights: [], price: '',
                priceType: 'fixed', terms: '', availability: '',
              });
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to publish listing');
    } finally {
      setIsLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return renderBasicsStep();
      case 1:
        return renderDetailsStep();
      case 2:
        return renderMediaStep();
      case 3:
        return renderDescriptionStep();
      case 4:
        return renderPricingStep();
      case 5:
        return renderReviewStep();
      default:
        return null;
    }
  };

  const renderBasicsStep = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>Property Basics</Text>
      <Text style={styles.stepSubtitle}>Let's start with the fundamentals</Text>

      <TextInput
        label="Property Title"
        value={formData.title}
        onChangeText={(text) => setFormData(prev => ({ ...prev, title: text }))}
        mode="outlined"
        style={styles.input}
        error={!!errors.title}
        placeholder="Beautiful 3BR Home in Downtown"
      />

      <Text style={styles.sectionTitle}>Property Type</Text>
      <View style={styles.chipContainer}>
        {PROPERTY_TYPES.map((type) => (
          <Pressable
            key={type.id}
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              setFormData(prev => ({ ...prev, propertyType: type.id }));
            }}
          >
            <Surface
              style={[
                styles.typeCard,
                formData.propertyType === type.id && styles.typeCardSelected,
              ]}
              elevation={formData.propertyType === type.id ? 4 : 2}
            >
              <Text style={styles.typeIcon}>{type.icon}</Text>
              <Text style={styles.typeLabel}>{type.label}</Text>
            </Surface>
          </Pressable>
        ))}
      </View>

      <Text style={styles.sectionTitle}>Listing Type</Text>
      <View style={styles.listingTypeContainer}>
        {LISTING_TYPES.map((type) => (
          <Pressable
            key={type.id}
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              setFormData(prev => ({ ...prev, listingType: type.id }));
            }}
            style={styles.listingTypeButton}
          >
            <LinearGradient
              colors={
                formData.listingType === type.id
                  ? [type.color, type.color + '80']
                  : ['#F7FAFC', '#E2E8F0']
              }
              style={styles.listingTypeGradient}
            >
              <Text style={styles.listingTypeIcon}>{type.icon}</Text>
              <Text
                style={[
                  styles.listingTypeLabel,
                  formData.listingType === type.id && styles.listingTypeLabelSelected,
                ]}
              >
                {type.label}
              </Text>
            </LinearGradient>
          </Pressable>
        ))}
      </View>

      <View style={styles.addressContainer}>
        <TextInput
          label="Street Address"
          value={formData.address}
          onChangeText={(text) => setFormData(prev => ({ ...prev, address: text }))}
          mode="outlined"
          style={styles.input}
          error={!!errors.address}
        />
        
        <View style={styles.addressRow}>
          <TextInput
            label="City"
            value={formData.city}
            onChangeText={(text) => setFormData(prev => ({ ...prev, city: text }))}
            mode="outlined"
            style={[styles.input, styles.cityInput]}
          />
          <TextInput
            label="State"
            value={formData.state}
            onChangeText={(text) => setFormData(prev => ({ ...prev, state: text }))}
            mode="outlined"
            style={[styles.input, styles.stateInput]}
          />
          <TextInput
            label="ZIP"
            value={formData.zipCode}
            onChangeText={(text) => setFormData(prev => ({ ...prev, zipCode: text }))}
            mode="outlined"
            keyboardType="numeric"
            style={[styles.input, styles.zipInput]}
          />
        </View>
      </View>
    </View>
  );

  const renderDetailsStep = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>Property Details</Text>
      <Text style={styles.stepSubtitle}>Add key features and specifications</Text>

      <View style={styles.detailsGrid}>
        <TextInput
          label="Bedrooms"
          value={formData.bedrooms}
          onChangeText={(text) => setFormData(prev => ({ ...prev, bedrooms: text }))}
          mode="outlined"
          keyboardType="numeric"
          style={[styles.input, styles.gridInput]}
          error={!!errors.bedrooms}
        />
        <TextInput
          label="Bathrooms"
          value={formData.bathrooms}
          onChangeText={(text) => setFormData(prev => ({ ...prev, bathrooms: text }))}
          mode="outlined"
          keyboardType="numeric"
          style={[styles.input, styles.gridInput]}
          error={!!errors.bathrooms}
        />
      </View>

      <View style={styles.detailsGrid}>
        <TextInput
          label="Square Feet"
          value={formData.sqft}
          onChangeText={(text) => setFormData(prev => ({ ...prev, sqft: text }))}
          mode="outlined"
          keyboardType="numeric"
          style={[styles.input, styles.gridInput]}
          error={!!errors.sqft}
        />
        <TextInput
          label="Lot Size"
          value={formData.lotSize}
          onChangeText={(text) => setFormData(prev => ({ ...prev, lotSize: text }))}
          mode="outlined"
          style={[styles.input, styles.gridInput]}
          placeholder="0.25 acres"
        />
      </View>

      <TextInput
        label="Year Built"
        value={formData.yearBuilt}
        onChangeText={(text) => setFormData(prev => ({ ...prev, yearBuilt: text }))}
        mode="outlined"
        keyboardType="numeric"
        style={styles.input}
        placeholder="2020"
      />
    </View>
  );

  const renderMediaStep = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>Photos & Media</Text>
      <Text style={styles.stepSubtitle}>Showcase your property with great visuals</Text>

      <View style={styles.mediaActions}>
        <Pressable onPress={handleCameraPicker} style={styles.mediaButton}>
          <Surface style={styles.mediaButtonSurface} elevation={4}>
            <LinearGradient
              colors={[branding.primaryColor, branding.secondaryColor]}
              style={styles.mediaButtonGradient}
            >
              <IconButton icon="camera" iconColor="white" size={28} />
              <Text style={styles.mediaButtonText}>Take Photo</Text>
            </LinearGradient>
          </Surface>
        </Pressable>

        <Pressable onPress={handleImagePicker} style={styles.mediaButton}>
          <Surface style={styles.mediaButtonSurface} elevation={4}>
            <LinearGradient
              colors={[branding.accentColor, branding.primaryColor]}
              style={styles.mediaButtonGradient}
            >
              <IconButton icon="image-multiple" iconColor="white" size={28} />
              <Text style={styles.mediaButtonText}>Choose Photos</Text>
            </LinearGradient>
          </Surface>
        </Pressable>
      </View>

      {formData.images.length > 0 && (
        <View style={styles.imageGrid}>
          {formData.images.map((image, index) => (
            <Animatable.View
              key={index}
              animation="fadeInUp"
              delay={index * 100}
              style={styles.imageItem}
            >
              <Surface style={styles.imageSurface} elevation={4}>
                <Image source={{ uri: image.uri }} style={styles.image} />
                <Pressable
                  onPress={() => {
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                    setFormData(prev => ({
                      ...prev,
                      images: prev.images.filter((_, i) => i !== index),
                    }));
                  }}
                  style={styles.imageDelete}
                >
                  <Surface style={styles.imageDeleteSurface} elevation={2}>
                    <IconButton icon="close" iconColor="white" size={16} />
                  </Surface>
                </Pressable>
              </Surface>
            </Animatable.View>
          ))}
        </View>
      )}
    </View>
  );

  const renderDescriptionStep = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>Property Description</Text>
      <Text style={styles.stepSubtitle}>Create compelling copy that sells</Text>

      <View style={styles.aiSection}>
        <Surface style={styles.aiCard} elevation={4}>
          <LinearGradient
            colors={[branding.primaryColor + '20', branding.accentColor + '20']}
            style={styles.aiCardGradient}
          >
            <View style={styles.aiCardContent}>
              <Avatar.Icon
                size={48}
                icon="robot"
                style={{ backgroundColor: branding.primaryColor }}
              />
              <View style={styles.aiCardText}>
                <Text style={styles.aiCardTitle}>AI Description Generator</Text>
                <Text style={styles.aiCardSubtitle}>
                  Let AI create a professional description based on your property details
                </Text>
              </View>
              <Button
                mode="contained"
                onPress={() => setShowAIModal(true)}
                style={styles.aiButton}
                buttonColor={branding.primaryColor}
              >
                Generate
              </Button>
            </View>
          </LinearGradient>
        </Surface>
      </View>

      <TextInput
        label="Property Description"
        value={formData.description}
        onChangeText={(text) => setFormData(prev => ({ ...prev, description: text }))}
        mode="outlined"
        multiline
        numberOfLines={8}
        style={styles.descriptionInput}
        placeholder="Describe the property's best features, location benefits, and what makes it special..."
      />
    </View>
  );

  const renderPricingStep = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>Pricing & Terms</Text>
      <Text style={styles.stepSubtitle}>Set your price and terms</Text>

      <TextInput
        label="Price"
        value={formData.price}
        onChangeText={(text) => setFormData(prev => ({ ...prev, price: text }))}
        mode="outlined"
        keyboardType="numeric"
        style={styles.input}
        error={!!errors.price}
        left={<TextInput.Icon icon="currency-usd" />}
        placeholder="450000"
      />

      <TextInput
        label="Terms & Conditions"
        value={formData.terms}
        onChangeText={(text) => setFormData(prev => ({ ...prev, terms: text }))}
        mode="outlined"
        multiline
        numberOfLines={4}
        style={styles.input}
        placeholder="Special terms, financing options, etc."
      />

      <TextInput
        label="Availability"
        value={formData.availability}
        onChangeText={(text) => setFormData(prev => ({ ...prev, availability: text }))}
        mode="outlined"
        style={styles.input}
        placeholder="Immediate, 30 days, etc."
      />
    </View>
  );

  const renderReviewStep = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>Review & Publish</Text>
      <Text style={styles.stepSubtitle}>Everything looks good? Let's publish!</Text>

      <Surface style={styles.reviewCard} elevation={4}>
        <View style={styles.reviewHeader}>
          <Text style={styles.reviewTitle}>{formData.title}</Text>
          <Chip style={styles.reviewChip}>{formData.listingType}</Chip>
        </View>
        <Text style={styles.reviewAddress}>
          {formData.address}, {formData.city}, {formData.state}
        </Text>
        <Text style={styles.reviewPrice}>${formData.price}</Text>
        <Text style={styles.reviewSpecs}>
          {formData.bedrooms} bed • {formData.bathrooms} bath • {formData.sqft} sqft
        </Text>
      </Surface>
    </View>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={branding.primaryColor} />
      
      {/* Header */}
      <LinearGradient
        colors={[branding.primaryColor, branding.secondaryColor]}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <IconButton
            icon="arrow-left"
            iconColor="white"
            size={24}
            onPress={handleBack}
          />
          <View style={styles.headerTitle}>
            <Text style={styles.stepCounter}>
              Step {currentStep + 1} of {POSTING_STEPS.length}
            </Text>
            <Text style={styles.stepName}>
              {POSTING_STEPS[currentStep].title}
            </Text>
          </View>
          <View style={{ width: 48 }} />
        </View>
        
        {/* Progress Bar */}
        <View style={styles.progressContainer}>
          <Animated.View
            style={[
              styles.progressBar,
              {
                width: progressAnim.interpolate({
                  inputRange: [0, 1],
                  outputRange: ['0%', '100%'],
                }),
              },
            ]}
          />
        </View>
      </LinearGradient>

      {/* Content */}
      <Animated.View
        style={[
          styles.content,
          {
            opacity: fadeAnim,
            transform: [{ translateY: slideAnim }],
          },
        ]}
      >
        <KeyboardAwareScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          enableOnAndroid={true}
          extraScrollHeight={20}
        >
          {renderStepContent()}
        </KeyboardAwareScrollView>
      </Animated.View>

      {/* Bottom Navigation */}
      <View style={styles.bottomNav}>
        <Surface style={styles.bottomNavSurface} elevation={8}>
          <View style={styles.bottomNavContent}>
            {currentStep > 0 && (
              <Button
                mode="outlined"
                onPress={handleBack}
                style={styles.backButton}
              >
                Back
              </Button>
            )}
            
            <Button
              mode="contained"
              onPress={handleNext}
              loading={isLoading}
              disabled={isLoading}
              style={[styles.nextButton, { backgroundColor: branding.primaryColor }]}
              contentStyle={styles.nextButtonContent}
            >
              {currentStep === POSTING_STEPS.length - 1 ? 'Publish Listing' : 'Continue'}
            </Button>
          </View>
        </Surface>
      </View>

      {/* AI Description Modal */}
      <Portal>
        <Modal
          visible={showAIModal}
          onDismiss={() => setShowAIModal(false)}
          contentContainerStyle={styles.modalContainer}
        >
          <Surface style={styles.modalSurface} elevation={8}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>AI Description Generator</Text>
              <Text style={styles.modalSubtitle}>
                Generate a professional property description using AI
              </Text>
              
              <View style={styles.modalActions}>
                <Button
                  mode="outlined"
                  onPress={() => setShowAIModal(false)}
                  style={styles.modalButton}
                >
                  Cancel
                </Button>
                <Button
                  mode="contained"
                  onPress={generateAIDescription}
                  loading={aiGenerating}
                  disabled={aiGenerating}
                  style={styles.modalButton}
                  buttonColor={branding.primaryColor}
                >
                  Generate
                </Button>
              </View>
            </View>
          </Surface>
        </Modal>
      </Portal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  header: {
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingBottom: 20,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  headerTitle: {
    alignItems: 'center',
  },
  stepCounter: {
    color: 'rgba(255,255,255,0.9)',
    fontSize: 14,
  },
  stepName: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  progressContainer: {
    height: 4,
    backgroundColor: 'rgba(255,255,255,0.3)',
    marginHorizontal: 16,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: 'white',
    borderRadius: 2,
  },
  content: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 120,
  },
  stepContent: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#2D3748',
  },
  stepSubtitle: {
    fontSize: 16,
    color: '#64748B',
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
    marginTop: 24,
    color: '#2D3748',
  },
  input: {
    marginBottom: 16,
    backgroundColor: 'white',
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 24,
  },
  typeCard: {
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    minWidth: 80,
    backgroundColor: 'white',
  },
  typeCardSelected: {
    backgroundColor: '#EBF8FF',
  },
  typeIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  typeLabel: {
    fontSize: 14,
    fontWeight: '500',
  },
  listingTypeContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  listingTypeButton: {
    flex: 1,
    borderRadius: 12,
    overflow: 'hidden',
  },
  listingTypeGradient: {
    padding: 16,
    alignItems: 'center',
  },
  listingTypeIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  listingTypeLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#64748B',
  },
  listingTypeLabelSelected: {
    color: 'white',
  },
  addressContainer: {
    marginTop: 8,
  },
  addressRow: {
    flexDirection: 'row',
    gap: 12,
  },
  cityInput: {
    flex: 2,
  },
  stateInput: {
    flex: 1,
  },
  zipInput: {
    flex: 1,
  },
  detailsGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  gridInput: {
    flex: 1,
  },
  mediaActions: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 24,
  },
  mediaButton: {
    flex: 1,
  },
  mediaButtonSurface: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  mediaButtonGradient: {
    padding: 20,
    alignItems: 'center',
  },
  mediaButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    marginTop: 8,
  },
  imageGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  imageItem: {
    width: (width - 60) / 3,
    aspectRatio: 1,
  },
  imageSurface: {
    flex: 1,
    borderRadius: 12,
    overflow: 'hidden',
  },
  image: {
    flex: 1,
    width: '100%',
  },
  imageDelete: {
    position: 'absolute',
    top: 4,
    right: 4,
  },
  imageDeleteSurface: {
    backgroundColor: 'rgba(0,0,0,0.7)',
    borderRadius: 16,
  },
  aiSection: {
    marginBottom: 24,
  },
  aiCard: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  aiCardGradient: {
    padding: 20,
  },
  aiCardContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  aiCardText: {
    flex: 1,
    marginLeft: 16,
  },
  aiCardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
    color: '#2D3748',
  },
  aiCardSubtitle: {
    fontSize: 14,
    color: '#64748B',
  },
  aiButton: {
    borderRadius: 8,
  },
  descriptionInput: {
    backgroundColor: 'white',
    minHeight: 120,
  },
  reviewCard: {
    padding: 20,
    borderRadius: 16,
    backgroundColor: 'white',
  },
  reviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  reviewTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    flex: 1,
    marginRight: 12,
  },
  reviewChip: {
    backgroundColor: '#EBF8FF',
  },
  reviewAddress: {
    fontSize: 16,
    color: '#64748B',
    marginBottom: 8,
  },
  reviewPrice: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#38A169',
    marginBottom: 8,
  },
  reviewSpecs: {
    fontSize: 16,
    color: '#64748B',
  },
  bottomNav: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
  },
  bottomNavSurface: {
    backgroundColor: 'white',
    paddingBottom: Platform.OS === 'ios' ? 40 : 20,
  },
  bottomNavContent: {
    flexDirection: 'row',
    padding: 20,
    gap: 16,
  },
  backButton: {
    flex: 1,
    borderRadius: 12,
  },
  nextButton: {
    flex: 2,
    borderRadius: 12,
  },
  nextButtonContent: {
    paddingVertical: 8,
  },
  modalContainer: {
    margin: 20,
  },
  modalSurface: {
    borderRadius: 16,
    backgroundColor: 'white',
  },
  modalContent: {
    padding: 24,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  modalSubtitle: {
    fontSize: 16,
    color: '#64748B',
    marginBottom: 24,
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
  },
  modalButton: {
    flex: 1,
  },
});
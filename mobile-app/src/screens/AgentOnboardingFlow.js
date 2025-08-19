import React, { useState, useRef } from 'react';
import {
  View,
  ScrollView,
  Dimensions,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import {
  Text,
  Button,
  ProgressBar,
  Surface,
  IconButton,
} from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import * as Animatable from 'react-native-animatable';
import { useBranding } from '../contexts/BrandingContext';
import { useAuth } from '../contexts/AuthContext';

// Onboarding Steps
import PersonalInfoStep from '../components/onboarding/PersonalInfoStep';
import CompanyInfoStep from '../components/onboarding/CompanyInfoStep';
import BrandingStep from '../components/onboarding/BrandingStep';
import PreferencesStep from '../components/onboarding/PreferencesStep';
import AISetupStep from '../components/onboarding/AISetupStep';
import VerificationStep from '../components/onboarding/VerificationStep';

const { width, height } = Dimensions.get('window');

const STEPS = [
  { id: 'personal', title: 'Personal Info', component: PersonalInfoStep },
  { id: 'company', title: 'Company Details', component: CompanyInfoStep },
  { id: 'branding', title: 'Brand Identity', component: BrandingStep },
  { id: 'preferences', title: 'Preferences', component: PreferencesStep },
  { id: 'ai-setup', title: 'AI Assistant', component: AISetupStep },
  { id: 'verification', title: 'Verification', component: VerificationStep },
];

export default function AgentOnboardingFlow({ navigation }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const scrollViewRef = useRef(null);
  const { branding } = useBranding();
  const { register } = useAuth();

  const progress = (currentStep + 1) / STEPS.length;
  const CurrentStepComponent = STEPS[currentStep].component;

  const handleNext = async (stepData) => {
    const updatedFormData = { ...formData, ...stepData };
    setFormData(updatedFormData);

    if (currentStep === STEPS.length - 1) {
      // Final step - complete onboarding
      await completeOnboarding(updatedFormData);
    } else {
      setCurrentStep(currentStep + 1);
      scrollViewRef.current?.scrollTo({ x: 0, y: 0, animated: true });
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
      scrollViewRef.current?.scrollTo({ x: 0, y: 0, animated: true });
    } else {
      navigation.goBack();
    }
  };

  const completeOnboarding = async (data) => {
    try {
      setIsLoading(true);
      
      // Register the agent with all collected data
      const result = await register({
        ...data,
        role: 'agent',
        onboardingCompleted: true,
      });

      if (result.success) {
        navigation.replace('Main');
      } else {
        // Handle registration error
        console.error('Onboarding failed:', result.error);
      }
    } catch (error) {
      console.error('Onboarding error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.container}>
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
            <Text style={styles.stepTitle}>
              Step {currentStep + 1} of {STEPS.length}
            </Text>
            <Text style={styles.stepName}>
              {STEPS[currentStep].title}
            </Text>
          </View>
          <View style={{ width: 48 }} />
        </View>
        <ProgressBar
          progress={progress}
          color="white"
          style={styles.progressBar}
        />
      </LinearGradient>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.content}
      >
        <ScrollView
          ref={scrollViewRef}
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          <Animatable.View
            animation="slideInRight"
            duration={300}
            style={styles.stepContainer}
          >
            <Surface style={styles.stepCard}>
              <CurrentStepComponent
                formData={formData}
                onNext={handleNext}
                onBack={handleBack}
                isLoading={isLoading}
                isLastStep={currentStep === STEPS.length - 1}
              />
            </Surface>
          </Animatable.View>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  header: {
    paddingTop: 50,
    paddingBottom: 20,
    paddingHorizontal: 16,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  headerTitle: {
    alignItems: 'center',
  },
  stepTitle: {
    color: 'white',
    fontSize: 14,
    opacity: 0.9,
  },
  stepName: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  progressBar: {
    height: 4,
    borderRadius: 2,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
  },
  content: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    minHeight: height - 200,
  },
  stepContainer: {
    flex: 1,
  },
  stepCard: {
    padding: 24,
    borderRadius: 16,
    elevation: 4,
    backgroundColor: 'white',
  },
});
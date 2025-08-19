import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import {
  Text,
  Button,
  Card,
  List,
  IconButton,
  ProgressBar,
  Chip,
} from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import * as Animatable from 'react-native-animatable';
import { useBranding } from '../../contexts/BrandingContext';

const VERIFICATION_STEPS = [
  {
    id: 'profile',
    title: 'Profile Information',
    description: 'Personal and company details',
    icon: 'account-check',
    status: 'completed',
  },
  {
    id: 'branding',
    title: 'Brand Setup',
    description: 'Logo, colors, and brand identity',
    icon: 'palette',
    status: 'completed',
  },
  {
    id: 'ai',
    title: 'AI Assistant',
    description: 'AI configuration and preferences',
    icon: 'robot',
    status: 'completed',
  },
  {
    id: 'license',
    title: 'License Verification',
    description: 'Real estate license validation',
    icon: 'certificate',
    status: 'pending',
  },
  {
    id: 'integration',
    title: 'System Integration',
    description: 'CRM and third-party connections',
    icon: 'connection',
    status: 'pending',
  },
];

export default function VerificationStep({ formData, onNext, isLoading, isLastStep }) {
  const [verificationSteps, setVerificationSteps] = useState(VERIFICATION_STEPS);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationProgress, setVerificationProgress] = useState(0);

  const { branding } = useBranding();

  useEffect(() => {
    // Simulate verification process
    startVerification();
  }, []);

  const startVerification = async () => {
    setIsVerifying(true);
    
    // Simulate license verification
    setTimeout(() => {
      updateStepStatus('license', 'verifying');
      setVerificationProgress(0.4);
    }, 1000);

    setTimeout(() => {
      updateStepStatus('license', 'completed');
      updateStepStatus('integration', 'verifying');
      setVerificationProgress(0.7);
    }, 3000);

    setTimeout(() => {
      updateStepStatus('integration', 'completed');
      setVerificationProgress(1.0);
      setIsVerifying(false);
    }, 5000);
  };

  const updateStepStatus = (stepId, status) => {
    setVerificationSteps(prev => 
      prev.map(step => 
        step.id === stepId ? { ...step, status } : step
      )
    );
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return 'check-circle';
      case 'verifying':
        return 'loading';
      case 'failed':
        return 'alert-circle';
      default:
        return 'clock-outline';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return '#38A169';
      case 'verifying':
        return branding.primaryColor;
      case 'failed':
        return '#E53E3E';
      default:
        return '#A0AEC0';
    }
  };

  const handleComplete = () => {
    const allCompleted = verificationSteps.every(step => step.status === 'completed');
    
    if (!allCompleted) {
      Alert.alert(
        'Verification Incomplete',
        'Please wait for all verification steps to complete.',
        [{ text: 'OK' }]
      );
      return;
    }

    onNext({
      verificationCompleted: true,
      verificationSteps,
      completedAt: new Date().toISOString(),
    });
  };

  const retryVerification = () => {
    setVerificationSteps(prev => 
      prev.map(step => 
        step.status === 'failed' ? { ...step, status: 'pending' } : step
      )
    );
    startVerification();
  };

  const allCompleted = verificationSteps.every(step => step.status === 'completed');
  const hasFailures = verificationSteps.some(step => step.status === 'failed');

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <Text style={styles.title}>Account Verification</Text>
      <Text style={styles.subtitle}>
        We're verifying your information to complete your setup
      </Text>

      {/* Progress Card */}
      <Card style={styles.progressCard}>
        <LinearGradient
          colors={[branding.primaryColor, branding.secondaryColor]}
          style={styles.progressHeader}
        >
          <Text style={styles.progressTitle}>Verification Progress</Text>
          <Text style={styles.progressText}>
            {Math.round(verificationProgress * 100)}% Complete
          </Text>
        </LinearGradient>
        <View style={styles.progressBody}>
          <ProgressBar
            progress={verificationProgress}
            color={branding.primaryColor}
            style={styles.progressBar}
          />
        </View>
      </Card>

      {/* Verification Steps */}
      <View style={styles.stepsContainer}>
        {verificationSteps.map((step, index) => (
          <Animatable.View
            key={step.id}
            animation={step.status === 'verifying' ? 'pulse' : undefined}
            iterationCount="infinite"
            duration={1000}
          >
            <Card style={styles.stepCard}>
              <List.Item
                title={step.title}
                description={step.description}
                left={() => (
                  <View style={styles.stepIconContainer}>
                    <IconButton
                      icon={getStatusIcon(step.status)}
                      iconColor={getStatusColor(step.status)}
                      size={24}
                    />
                  </View>
                )}
                right={() => (
                  <Chip
                    compact
                    style={[
                      styles.statusChip,
                      { backgroundColor: getStatusColor(step.status) + '20' }
                    ]}
                    textStyle={{ color: getStatusColor(step.status) }}
                  >
                    {step.status.charAt(0).toUpperCase() + step.status.slice(1)}
                  </Chip>
                )}
              />
            </Card>
          </Animatable.View>
        ))}
      </View>

      {/* Summary Card */}
      {allCompleted && (
        <Animatable.View animation="bounceIn" duration={800}>
          <Card style={styles.summaryCard}>
            <LinearGradient
              colors={['#38A169', '#48BB78']}
              style={styles.summaryHeader}
            >
              <IconButton
                icon="check-circle"
                iconColor="white"
                size={40}
              />
              <Text style={styles.summaryTitle}>Verification Complete!</Text>
              <Text style={styles.summaryText}>
                Your account has been successfully verified and is ready to use.
              </Text>
            </LinearGradient>
          </Card>
        </Animatable.View>
      )}

      {/* Action Buttons */}
      <View style={styles.buttonContainer}>
        {hasFailures && (
          <Button
            mode="outlined"
            onPress={retryVerification}
            style={styles.retryButton}
            icon="refresh"
          >
            Retry Verification
          </Button>
        )}

        <Button
          mode="contained"
          onPress={handleComplete}
          loading={isLoading}
          disabled={isLoading || !allCompleted}
          style={[
            styles.completeButton,
            { backgroundColor: allCompleted ? branding.primaryColor : '#A0AEC0' }
          ]}
          contentStyle={styles.buttonContent}
        >
          {isLastStep ? 'Complete Setup' : 'Continue'}
        </Button>
      </View>
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
  progressCard: {
    marginBottom: 24,
    overflow: 'hidden',
  },
  progressHeader: {
    padding: 20,
    alignItems: 'center',
  },
  progressTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
  },
  progressText: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.9)',
  },
  progressBody: {
    padding: 16,
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
  },
  stepsContainer: {
    marginBottom: 24,
  },
  stepCard: {
    marginBottom: 12,
  },
  stepIconContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  statusChip: {
    alignSelf: 'center',
  },
  summaryCard: {
    marginBottom: 24,
    overflow: 'hidden',
  },
  summaryHeader: {
    padding: 32,
    alignItems: 'center',
  },
  summaryTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
    marginTop: 16,
    marginBottom: 8,
  },
  summaryText: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.9)',
    textAlign: 'center',
  },
  buttonContainer: {
    gap: 12,
  },
  retryButton: {
    borderColor: '#E53E3E',
  },
  completeButton: {
    borderRadius: 12,
  },
  buttonContent: {
    paddingVertical: 8,
  },
});
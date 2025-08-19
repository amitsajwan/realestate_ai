import React, { useRef, useState } from 'react';
import {
  View,
  StyleSheet,
  Dimensions,
  ScrollView,
  Image,
} from 'react-native';
import { Text, Button, IconButton } from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import * as Animatable from 'react-native-animatable';
import { useBranding } from '../contexts/BrandingContext';

const { width, height } = Dimensions.get('window');

const ONBOARDING_SLIDES = [
  {
    id: 1,
    title: 'AI-Powered Property Solutions',
    subtitle: 'Leverage cutting-edge AI to transform your real estate business',
    description: 'Get intelligent insights, automated responses, and smart property recommendations powered by advanced AI technology.',
    icon: '🤖',
    gradient: ['#667eea', '#764ba2'],
  },
  {
    id: 2,
    title: 'Complete CRM Solution',
    subtitle: 'Manage leads, clients, and properties in one place',
    description: 'Streamline your workflow with our comprehensive CRM that grows with your business.',
    icon: '📊',
    gradient: ['#f093fb', '#f5576c'],
  },
  {
    id: 3,
    title: 'Custom Branding',
    subtitle: 'Make it truly yours with personalized branding',
    description: 'Customize colors, logos, and messaging to reflect your unique brand identity.',
    icon: '🎨',
    gradient: ['#4facfe', '#00f2fe'],
  },
  {
    id: 4,
    title: 'Mobile-First Design',
    subtitle: 'Work from anywhere, anytime',
    description: 'Built for mobile professionals who need access to their business on the go.',
    icon: '📱',
    gradient: ['#43e97b', '#38f9d7'],
  },
];

export default function OnboardingScreen({ navigation }) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const scrollViewRef = useRef(null);
  const { branding } = useBranding();

  const goToSlide = (index) => {
    setCurrentSlide(index);
    scrollViewRef.current?.scrollTo({
      x: index * width,
      animated: true,
    });
  };

  const handleNext = () => {
    if (currentSlide < ONBOARDING_SLIDES.length - 1) {
      goToSlide(currentSlide + 1);
    } else {
      navigation.navigate('Login');
    }
  };

  const handleSkip = () => {
    navigation.navigate('Login');
  };

  const handleGetStarted = () => {
    navigation.navigate('AgentOnboarding');
  };

  const onScroll = (event) => {
    const slideIndex = Math.round(event.nativeEvent.contentOffset.x / width);
    setCurrentSlide(slideIndex);
  };

  const renderSlide = (slide, index) => (
    <View key={slide.id} style={styles.slide}>
      <LinearGradient
        colors={slide.gradient}
        style={styles.slideBackground}
      >
        <View style={styles.slideContent}>
          <Animatable.Text
            animation="bounceIn"
            delay={300}
            style={styles.slideIcon}
          >
            {slide.icon}
          </Animatable.Text>
          
          <Animatable.Text
            animation="fadeInUp"
            delay={500}
            style={styles.slideTitle}
          >
            {slide.title}
          </Animatable.Text>
          
          <Animatable.Text
            animation="fadeInUp"
            delay={700}
            style={styles.slideSubtitle}
          >
            {slide.subtitle}
          </Animatable.Text>
          
          <Animatable.Text
            animation="fadeInUp"
            delay={900}
            style={styles.slideDescription}
          >
            {slide.description}
          </Animatable.Text>
        </View>
      </LinearGradient>
    </View>
  );

  const isLastSlide = currentSlide === ONBOARDING_SLIDES.length - 1;

  return (
    <View style={styles.container}>
      <ScrollView
        ref={scrollViewRef}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onScroll={onScroll}
        scrollEventThrottle={16}
      >
        {ONBOARDING_SLIDES.map((slide, index) => renderSlide(slide, index))}
      </ScrollView>

      {/* Header with Skip Button */}
      <View style={styles.header}>
        <View style={styles.skipContainer}>
          {!isLastSlide && (
            <Button
              mode="text"
              onPress={handleSkip}
              textColor="rgba(255,255,255,0.8)"
            >
              Skip
            </Button>
          )}
        </View>
      </View>

      {/* Bottom Navigation */}
      <View style={styles.bottomContainer}>
        {/* Page Indicators */}
        <View style={styles.pagination}>
          {ONBOARDING_SLIDES.map((_, index) => (
            <View
              key={index}
              style={[
                styles.paginationDot,
                {
                  backgroundColor: currentSlide === index 
                    ? 'white' 
                    : 'rgba(255,255,255,0.4)',
                  width: currentSlide === index ? 24 : 8,
                }
              ]}
            />
          ))}
        </View>

        {/* Navigation Buttons */}
        <View style={styles.navigationContainer}>
          {currentSlide > 0 && (
            <IconButton
              icon="arrow-left"
              iconColor="white"
              size={24}
              onPress={() => goToSlide(currentSlide - 1)}
              style={styles.navButton}
            />
          )}
          
          <View style={styles.spacer} />
          
          {isLastSlide ? (
            <Button
              mode="contained"
              onPress={handleGetStarted}
              style={styles.getStartedButton}
              contentStyle={styles.getStartedContent}
              buttonColor="white"
              textColor={ONBOARDING_SLIDES[currentSlide].gradient[0]}
            >
              Get Started
            </Button>
          ) : (
            <IconButton
              icon="arrow-right"
              iconColor="white"
              size={24}
              onPress={handleNext}
              style={styles.navButton}
            />
          )}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  slide: {
    width,
    height,
  },
  slideBackground: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  slideContent: {
    alignItems: 'center',
    paddingHorizontal: 40,
    paddingTop: 100,
  },
  slideIcon: {
    fontSize: 80,
    marginBottom: 40,
  },
  slideTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: 'white',
    textAlign: 'center',
    marginBottom: 16,
  },
  slideSubtitle: {
    fontSize: 20,
    color: 'rgba(255,255,255,0.9)',
    textAlign: 'center',
    marginBottom: 24,
    fontWeight: '500',
  },
  slideDescription: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.8)',
    textAlign: 'center',
    lineHeight: 24,
  },
  header: {
    position: 'absolute',
    top: 50,
    left: 0,
    right: 0,
    zIndex: 1,
  },
  skipContainer: {
    alignItems: 'flex-end',
    paddingRight: 20,
  },
  bottomContainer: {
    position: 'absolute',
    bottom: 60,
    left: 0,
    right: 0,
    paddingHorizontal: 40,
  },
  pagination: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 40,
  },
  paginationDot: {
    height: 8,
    borderRadius: 4,
    marginHorizontal: 4,
  },
  navigationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  navButton: {
    backgroundColor: 'rgba(255,255,255,0.2)',
  },
  spacer: {
    flex: 1,
  },
  getStartedButton: {
    borderRadius: 25,
    elevation: 0,
  },
  getStartedContent: {
    paddingVertical: 8,
    paddingHorizontal: 24,
  },
});
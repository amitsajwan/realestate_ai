import React, { useRef, useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  Dimensions,
  ScrollView,
  Animated,
  PanGestureHandler,
  State,
  Pressable,
  StatusBar,
} from 'react-native';
import { Text, Button, IconButton, Surface } from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import * as Animatable from 'react-native-animatable';
import * as Haptics from 'expo-haptics';
import { BlurView } from 'expo-blur';
import { useBranding } from '../contexts/BrandingContext';

const { width, height } = Dimensions.get('window');

const ONBOARDING_SLIDES = [
  {
    id: 1,
    title: 'AI-Powered Intelligence',
    subtitle: 'Your personal real estate assistant',
    description: 'Get instant property insights, market analysis, and personalized recommendations powered by advanced AI technology.',
    icon: '🤖',
    gradient: ['#667eea', '#764ba2'],
    features: ['Smart Property Analysis', 'Market Predictions', 'Automated Responses'],
    animation: 'bounceInLeft',
  },
  {
    id: 2,
    title: 'Complete CRM Solution',
    subtitle: 'Manage everything in one place',
    description: 'Track leads, manage clients, and close deals with our comprehensive CRM designed for modern real estate professionals.',
    icon: '📊',
    gradient: ['#f093fb', '#f5576c'],
    features: ['Lead Management', 'Client Tracking', 'Deal Pipeline'],
    animation: 'bounceInUp',
  },
  {
    id: 3,
    title: 'Your Brand, Your Way',
    subtitle: 'Personalized branding system',
    description: 'Customize colors, logos, and messaging to create a unique brand experience that reflects your professional identity.',
    icon: '🎨',
    gradient: ['#4facfe', '#00f2fe'],
    features: ['Custom Colors', 'Logo Integration', 'Brand Consistency'],
    animation: 'bounceInRight',
  },
  {
    id: 4,
    title: 'Mobile-First Design',
    subtitle: 'Work from anywhere, anytime',
    description: 'Built specifically for mobile professionals who need powerful tools that work seamlessly on any device.',
    icon: '📱',
    gradient: ['#43e97b', '#38f9d7'],
    features: ['Offline Capability', 'Touch Optimized', 'Cross-Platform'],
    animation: 'bounceInDown',
  },
];

export default function OnboardingScreen({ navigation }) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const scrollViewRef = useRef(null);
  const { branding } = useBranding();
  
  // Animation values
  const slideAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Animate progress bar
    Animated.timing(progressAnim, {
      toValue: (currentSlide + 1) / ONBOARDING_SLIDES.length,
      duration: 300,
      useNativeDriver: false,
    }).start();
  }, [currentSlide]);

  const goToSlide = async (index) => {
    if (index < 0 || index >= ONBOARDING_SLIDES.length) return;
    
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    
    // Slide transition animation
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 0.3,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 0.9,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start(() => {
      setCurrentSlide(index);
      scrollViewRef.current?.scrollTo({
        x: index * width,
        animated: true,
      });
      
      // Fade back in
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.timing(scaleAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
      ]).start();
    });
  };

  const handleNext = async () => {
    if (currentSlide < ONBOARDING_SLIDES.length - 1) {
      goToSlide(currentSlide + 1);
    } else {
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      navigation.navigate('Login');
    }
  };

  const handleSkip = async () => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    navigation.navigate('Login');
  };

  const handleGetStarted = async () => {
    await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    
    // Success animation
    Animated.sequence([
      Animated.timing(scaleAnim, {
        toValue: 1.1,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start(() => {
      navigation.navigate('AgentOnboarding');
    });
  };

  const onScroll = (event) => {
    const slideIndex = Math.round(event.nativeEvent.contentOffset.x / width);
    if (slideIndex !== currentSlide) {
      setCurrentSlide(slideIndex);
    }
  };

  const handlePanGesture = (event) => {
    if (event.nativeEvent.state === State.END) {
      const { translationX, velocityX } = event.nativeEvent;
      
      if (Math.abs(translationX) > width * 0.3 || Math.abs(velocityX) > 500) {
        if (translationX > 0 && currentSlide > 0) {
          goToSlide(currentSlide - 1);
        } else if (translationX < 0 && currentSlide < ONBOARDING_SLIDES.length - 1) {
          goToSlide(currentSlide + 1);
        }
      }
    }
  };

  const renderSlide = (slide, index) => (
    <View key={slide.id} style={styles.slide}>
      <LinearGradient
        colors={slide.gradient}
        style={styles.slideBackground}
      >
        {/* Animated Background Elements */}
        <Animatable.View
          animation="pulse"
          iterationCount="infinite"
          duration={3000}
          style={[styles.backgroundOrb, styles.orb1]}
        />
        <Animatable.View
          animation="pulse"
          iterationCount="infinite"
          duration={4000}
          delay={1000}
          style={[styles.backgroundOrb, styles.orb2]}
        />
        <Animatable.View
          animation="pulse"
          iterationCount="infinite"
          duration={5000}
          delay={2000}
          style={[styles.backgroundOrb, styles.orb3]}
        />

        <Animated.View
          style={[
            styles.slideContent,
            {
              opacity: fadeAnim,
              transform: [{ scale: scaleAnim }],
            },
          ]}
        >
          {/* Icon with animated container */}
          <Animatable.View
            animation={slide.animation}
            duration={1000}
            delay={300}
            style={styles.iconContainer}
          >
            <Surface style={styles.iconSurface} elevation={8}>
              <BlurView intensity={20} style={styles.iconBlur}>
                <Text style={styles.slideIcon}>{slide.icon}</Text>
              </BlurView>
            </Surface>
          </Animatable.View>
          
          {/* Content */}
          <View style={styles.textContainer}>
            <Animatable.Text
              animation="fadeInUp"
              delay={600}
              style={styles.slideTitle}
            >
              {slide.title}
            </Animatable.Text>
            
            <Animatable.Text
              animation="fadeInUp"
              delay={800}
              style={styles.slideSubtitle}
            >
              {slide.subtitle}
            </Animatable.Text>
            
            <Animatable.Text
              animation="fadeInUp"
              delay={1000}
              style={styles.slideDescription}
            >
              {slide.description}
            </Animatable.Text>

            {/* Feature List */}
            <Animatable.View
              animation="fadeInUp"
              delay={1200}
              style={styles.featureList}
            >
              {slide.features.map((feature, idx) => (
                <Animatable.View
                  key={feature}
                  animation="fadeInLeft"
                  delay={1400 + idx * 200}
                  style={styles.featureItem}
                >
                  <Surface style={styles.featureDot} elevation={2}>
                    <Text style={styles.featureDotText}>✓</Text>
                  </Surface>
                  <Text style={styles.featureText}>{feature}</Text>
                </Animatable.View>
              ))}
            </Animatable.View>
          </View>
        </Animated.View>
      </LinearGradient>
    </View>
  );

  const isLastSlide = currentSlide === ONBOARDING_SLIDES.length - 1;

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
      
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          {/* Progress Bar */}
          <View style={styles.progressContainer}>
            <View style={styles.progressTrack}>
              <Animated.View
                style={[
                  styles.progressFill,
                  {
                    width: progressAnim.interpolate({
                      inputRange: [0, 1],
                      outputRange: ['0%', '100%'],
                    }),
                  },
                ]}
              />
            </View>
            <Text style={styles.progressText}>
              {currentSlide + 1} of {ONBOARDING_SLIDES.length}
            </Text>
          </View>
        </View>
        
        <View style={styles.headerRight}>
          {!isLastSlide && (
            <Pressable onPress={handleSkip} style={styles.skipButton}>
              <BlurView intensity={20} style={styles.skipBlur}>
                <Text style={styles.skipText}>Skip</Text>
              </BlurView>
            </Pressable>
          )}
        </View>
      </View>

      {/* Slides */}
      <PanGestureHandler onHandlerStateChange={handlePanGesture}>
        <View style={styles.slidesContainer}>
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
        </View>
      </PanGestureHandler>

      {/* Bottom Navigation */}
      <View style={styles.bottomContainer}>
        <BlurView intensity={80} style={styles.bottomBlur}>
          <Surface style={styles.bottomSurface} elevation={8}>
            {/* Page Indicators */}
            <View style={styles.pagination}>
              {ONBOARDING_SLIDES.map((_, index) => (
                <Pressable
                  key={index}
                  onPress={() => goToSlide(index)}
                  style={styles.paginationDotContainer}
                >
                  <Animated.View
                    style={[
                      styles.paginationDot,
                      {
                        backgroundColor: currentSlide === index 
                          ? ONBOARDING_SLIDES[currentSlide].gradient[0]
                          : 'rgba(255,255,255,0.4)',
                        width: currentSlide === index ? 32 : 8,
                        transform: [{
                          scale: currentSlide === index ? 1.2 : 1,
                        }],
                      },
                    ]}
                  />
                </Pressable>
              ))}
            </View>

            {/* Navigation Buttons */}
            <View style={styles.navigationContainer}>
              {currentSlide > 0 && (
                <Pressable
                  onPress={() => goToSlide(currentSlide - 1)}
                  style={styles.navButton}
                >
                  <Surface style={styles.navButtonSurface} elevation={4}>
                    <IconButton
                      icon="arrow-left"
                      iconColor="white"
                      size={20}
                    />
                  </Surface>
                </Pressable>
              )}
              
              <View style={styles.spacer} />
              
              {isLastSlide ? (
                <Pressable
                  onPress={handleGetStarted}
                  style={styles.getStartedButton}
                >
                  <LinearGradient
                    colors={ONBOARDING_SLIDES[currentSlide].gradient}
                    style={styles.getStartedGradient}
                  >
                    <Text style={styles.getStartedText}>Get Started</Text>
                    <IconButton
                      icon="arrow-right"
                      iconColor="white"
                      size={20}
                    />
                  </LinearGradient>
                </Pressable>
              ) : (
                <Pressable
                  onPress={handleNext}
                  style={styles.navButton}
                >
                  <Surface style={styles.navButtonSurface} elevation={4}>
                    <LinearGradient
                      colors={ONBOARDING_SLIDES[currentSlide].gradient}
                      style={styles.nextButtonGradient}
                    >
                      <IconButton
                        icon="arrow-right"
                        iconColor="white"
                        size={20}
                      />
                    </LinearGradient>
                  </Surface>
                </Pressable>
              )}
            </View>
          </Surface>
        </BlurView>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  header: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  headerLeft: {
    flex: 1,
  },
  headerRight: {
    alignItems: 'flex-end',
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  progressTrack: {
    width: 120,
    height: 4,
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderRadius: 2,
    marginRight: 12,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: 'white',
    borderRadius: 2,
  },
  progressText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '500',
  },
  skipButton: {
    borderRadius: 20,
    overflow: 'hidden',
  },
  skipBlur: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  skipText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '500',
  },
  slidesContainer: {
    flex: 1,
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
  backgroundOrb: {
    position: 'absolute',
    borderRadius: 100,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  orb1: {
    width: 200,
    height: 200,
    top: '10%',
    right: '-20%',
  },
  orb2: {
    width: 150,
    height: 150,
    bottom: '20%',
    left: '-15%',
  },
  orb3: {
    width: 100,
    height: 100,
    top: '30%',
    left: '10%',
  },
  slideContent: {
    alignItems: 'center',
    paddingHorizontal: 40,
    paddingTop: 120,
    paddingBottom: 200,
  },
  iconContainer: {
    marginBottom: 40,
  },
  iconSurface: {
    width: 120,
    height: 120,
    borderRadius: 60,
    overflow: 'hidden',
  },
  iconBlur: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  slideIcon: {
    fontSize: 60,
  },
  textContainer: {
    alignItems: 'center',
  },
  slideTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: 'white',
    textAlign: 'center',
    marginBottom: 12,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  slideSubtitle: {
    fontSize: 18,
    color: 'rgba(255,255,255,0.9)',
    textAlign: 'center',
    marginBottom: 20,
    fontWeight: '500',
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  slideDescription: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.8)',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 30,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  featureList: {
    alignSelf: 'stretch',
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    paddingHorizontal: 20,
  },
  featureDot: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'rgba(255,255,255,0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  featureDotText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#2D3748',
  },
  featureText: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.9)',
    fontWeight: '500',
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  bottomContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingBottom: Platform.OS === 'ios' ? 40 : 20,
  },
  bottomBlur: {
    marginHorizontal: 20,
    borderRadius: 24,
    overflow: 'hidden',
  },
  bottomSurface: {
    padding: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 24,
  },
  pagination: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
    gap: 8,
  },
  paginationDotContainer: {
    padding: 4,
  },
  paginationDot: {
    height: 8,
    borderRadius: 4,
  },
  navigationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  navButton: {
    borderRadius: 28,
    overflow: 'hidden',
  },
  navButtonSurface: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'white',
    overflow: 'hidden',
  },
  nextButtonGradient: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  spacer: {
    flex: 1,
  },
  getStartedButton: {
    borderRadius: 28,
    overflow: 'hidden',
  },
  getStartedGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 16,
  },
  getStartedText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
    marginRight: 8,
  },
});
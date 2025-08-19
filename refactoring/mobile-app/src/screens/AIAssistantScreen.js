import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import {
  Text,
  TextInput,
  IconButton,
  Card,
  Avatar,
  Button,
  Chip,
  Surface,
} from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import * as Animatable from 'react-native-animatable';
import { useBranding } from '../contexts/BrandingContext';
import { useAuth } from '../contexts/AuthContext';

const QUICK_PROMPTS = [
  'Generate property description',
  'Market analysis for area',
  'Client follow-up email',
  'Price recommendation',
  'Showing schedule',
  'Contract review points',
];

const SAMPLE_CONVERSATIONS = [
  {
    id: 1,
    type: 'user',
    message: 'Can you help me write a description for a 3-bedroom house in downtown?',
    timestamp: new Date(Date.now() - 300000),
  },
  {
    id: 2,
    type: 'ai',
    message: 'I\'d be happy to help you create a compelling property description! To write the best description, I\'ll need a few details:\n\n• Square footage\n• Key features (garage, yard, updated kitchen, etc.)\n• Neighborhood highlights\n• Price range\n\nOnce you provide these details, I\'ll craft a professional description that highlights the property\'s best features and attracts potential buyers.',
    timestamp: new Date(Date.now() - 299000),
  },
];

export default function AIAssistantScreen() {
  const [message, setMessage] = useState('');
  const [conversations, setConversations] = useState(SAMPLE_CONVERSATIONS);
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  
  const scrollViewRef = useRef(null);
  const { branding } = useBranding();
  const { user } = useAuth();

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, [conversations]);

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      message: message.trim(),
      timestamp: new Date(),
    };

    setConversations(prev => [...prev, userMessage]);
    setMessage('');
    setIsLoading(true);
    setIsTyping(true);

    try {
      // Simulate AI response - In production, this would call your GROQ API
      const aiResponse = await simulateAIResponse(userMessage.message);
      
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        message: aiResponse,
        timestamp: new Date(),
      };

      setConversations(prev => [...prev, aiMessage]);
    } catch (error) {
      Alert.alert('Error', 'Failed to get AI response. Please try again.');
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const simulateAIResponse = async (userMessage) => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Simple response logic - replace with actual GROQ API call
    if (userMessage.toLowerCase().includes('property description')) {
      return 'I can help you create compelling property descriptions! Please provide me with:\n\n• Property type and size\n• Key features and amenities\n• Location highlights\n• Target price range\n\nI\'ll craft a professional description that attracts buyers and highlights the property\'s best features.';
    } else if (userMessage.toLowerCase().includes('market analysis')) {
      return 'For a comprehensive market analysis, I\'ll need:\n\n• Specific neighborhood or area\n• Property type of interest\n• Time frame for analysis\n\nI can provide insights on:\n• Recent sales data\n• Price trends\n• Market conditions\n• Competitive analysis';
    } else {
      return 'I\'m here to help with all your real estate needs! I can assist with:\n\n• Property descriptions\n• Market analysis\n• Client communications\n• Pricing strategies\n• Contract insights\n• Lead qualification\n\nWhat would you like help with today?';
    }
  };

  const useQuickPrompt = (prompt) => {
    setMessage(prompt);
  };

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderMessage = (msg) => (
    <Animatable.View
      key={msg.id}
      animation="fadeInUp"
      duration={400}
      style={[
        styles.messageContainer,
        msg.type === 'user' ? styles.userMessageContainer : styles.aiMessageContainer,
      ]}
    >
      <View
        style={[
          styles.messageBubble,
          msg.type === 'user' 
            ? [styles.userMessage, { backgroundColor: branding.primaryColor }]
            : styles.aiMessage,
        ]}
      >
        <Text
          style={[
            styles.messageText,
            msg.type === 'user' ? styles.userMessageText : styles.aiMessageText,
          ]}
        >
          {msg.message}
        </Text>
        <Text
          style={[
            styles.messageTime,
            msg.type === 'user' ? styles.userMessageTime : styles.aiMessageTime,
          ]}
        >
          {formatTime(msg.timestamp)}
        </Text>
      </View>
    </Animatable.View>
  );

  return (
    <View style={[styles.container, { backgroundColor: branding.backgroundColor }]}>
      {/* Header */}
      <LinearGradient
        colors={[branding.primaryColor, branding.secondaryColor]}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <Avatar.Icon
            size={40}
            icon="robot"
            style={{ backgroundColor: 'rgba(255,255,255,0.2)' }}
          />
          <View style={styles.headerText}>
            <Text style={styles.headerTitle}>AI Assistant</Text>
            <Text style={styles.headerSubtitle}>
              {isTyping ? 'Typing...' : 'Ready to help'}
            </Text>
          </View>
          <IconButton
            icon="cog"
            iconColor="white"
            size={24}
            onPress={() => {
              // Handle settings
            }}
          />
        </View>
      </LinearGradient>

      {/* Quick Prompts */}
      <View style={styles.quickPromptsContainer}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.quickPrompts}
        >
          {QUICK_PROMPTS.map((prompt, index) => (
            <Chip
              key={index}
              mode="outlined"
              onPress={() => useQuickPrompt(prompt)}
              style={styles.quickPromptChip}
            >
              {prompt}
            </Chip>
          ))}
        </ScrollView>
      </View>

      {/* Conversation */}
      <ScrollView
        ref={scrollViewRef}
        style={styles.conversationContainer}
        contentContainerStyle={styles.conversationContent}
        showsVerticalScrollIndicator={false}
      >
        {conversations.length === 0 ? (
          <View style={styles.emptyState}>
            <Avatar.Icon
              size={80}
              icon="robot"
              style={{ backgroundColor: branding.primaryColor + '20' }}
              color={branding.primaryColor}
            />
            <Text style={styles.emptyStateTitle}>AI Assistant Ready</Text>
            <Text style={styles.emptyStateText}>
              Ask me anything about real estate, property management, or client relations.
            </Text>
          </View>
        ) : (
          conversations.map(renderMessage)
        )}
        
        {isTyping && (
          <View style={styles.typingIndicator}>
            <Animatable.View
              animation="pulse"
              iterationCount="infinite"
              style={styles.typingDots}
            >
              <Text style={styles.typingText}>AI is typing...</Text>
            </Animatable.View>
          </View>
        )}
      </ScrollView>

      {/* Input */}
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.inputContainer}
      >
        <Surface style={styles.inputSurface}>
          <TextInput
            value={message}
            onChangeText={setMessage}
            placeholder="Ask your AI assistant..."
            mode="flat"
            multiline
            style={styles.textInput}
            theme={{ colors: { primary: branding.primaryColor } }}
          />
          <IconButton
            icon="send"
            iconColor={message.trim() ? branding.primaryColor : '#9CA3AF'}
            size={24}
            onPress={sendMessage}
            disabled={!message.trim() || isLoading}
          />
        </Surface>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingTop: 60,
    paddingBottom: 20,
    paddingHorizontal: 20,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerText: {
    flex: 1,
    marginLeft: 16,
  },
  headerTitle: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
  },
  headerSubtitle: {
    color: 'rgba(255,255,255,0.8)',
    fontSize: 14,
  },
  quickPromptsContainer: {
    backgroundColor: 'white',
    paddingVertical: 12,
  },
  quickPrompts: {
    paddingHorizontal: 16,
    gap: 8,
  },
  quickPromptChip: {
    marginRight: 8,
  },
  conversationContainer: {
    flex: 1,
  },
  conversationContent: {
    padding: 16,
    flexGrow: 1,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyStateTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 20,
    marginBottom: 12,
    textAlign: 'center',
  },
  emptyStateText: {
    fontSize: 16,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 24,
  },
  messageContainer: {
    marginBottom: 16,
  },
  userMessageContainer: {
    alignItems: 'flex-end',
  },
  aiMessageContainer: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '80%',
    borderRadius: 16,
    padding: 12,
  },
  userMessage: {
    borderBottomRightRadius: 4,
  },
  aiMessage: {
    backgroundColor: '#F7FAFC',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 20,
  },
  userMessageText: {
    color: 'white',
  },
  aiMessageText: {
    color: '#2D3748',
  },
  messageTime: {
    fontSize: 12,
    marginTop: 4,
  },
  userMessageTime: {
    color: 'rgba(255,255,255,0.8)',
  },
  aiMessageTime: {
    color: '#9CA3AF',
  },
  typingIndicator: {
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  typingDots: {
    backgroundColor: '#F7FAFC',
    borderRadius: 16,
    borderBottomLeftRadius: 4,
    padding: 12,
  },
  typingText: {
    color: '#64748B',
    fontSize: 14,
    fontStyle: 'italic',
  },
  inputContainer: {
    backgroundColor: 'white',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  inputSurface: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 8,
    elevation: 2,
  },
  textInput: {
    flex: 1,
    maxHeight: 100,
    backgroundColor: 'transparent',
  },
});
// Environment variable validation and configuration

interface EnvironmentConfig {
  NODE_ENV: 'development' | 'production' | 'test'
  NEXT_PUBLIC_API_BASE_URL: string
  NEXT_PUBLIC_APP_NAME: string
  NEXT_PUBLIC_APP_VERSION: string
  NEXT_PUBLIC_FACEBOOK_APP_ID?: string
  NEXT_PUBLIC_GOOGLE_ANALYTICS_ID?: string
}

// Required environment variables
const requiredEnvVars = [
  'NEXT_PUBLIC_API_BASE_URL',
  'NEXT_PUBLIC_APP_NAME',
  'NEXT_PUBLIC_APP_VERSION'
] as const

// Validate environment variables
function validateEnvironment(): EnvironmentConfig {
  const missingVars = requiredEnvVars.filter(
    varName => !process.env[varName]
  )

  if (missingVars.length > 0) {
    throw new Error(
      `Missing required environment variables: ${missingVars.join(', ')}`
    )
  }

  return {
    NODE_ENV: (process.env.NODE_ENV as EnvironmentConfig['NODE_ENV']) || 'development',
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL!,
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME!,
    NEXT_PUBLIC_APP_VERSION: process.env.NEXT_PUBLIC_APP_VERSION!,
    NEXT_PUBLIC_FACEBOOK_APP_ID: process.env.NEXT_PUBLIC_FACEBOOK_APP_ID,
    NEXT_PUBLIC_GOOGLE_ANALYTICS_ID: process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID
  }
}

// Export validated environment config
export const env = validateEnvironment()

// Environment-specific configurations
export const config = {
  isDevelopment: env.NODE_ENV === 'development',
  isProduction: env.NODE_ENV === 'production',
  isTest: env.NODE_ENV === 'test',
  
  // API Configuration
  api: {
    baseUrl: env.NEXT_PUBLIC_API_BASE_URL,
    timeout: 10000, // 10 seconds
    retryAttempts: 3
  },
  
  // App Configuration
  app: {
    name: env.NEXT_PUBLIC_APP_NAME,
    version: env.NEXT_PUBLIC_APP_VERSION,
    description: 'AI-Powered Real Estate Platform'
  },
  
  // Feature Flags
  features: {
    facebookIntegration: !!env.NEXT_PUBLIC_FACEBOOK_APP_ID,
    analytics: !!env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID,
    aiSuggestions: true,
    propertyManagement: true,
    crm: true
  },
  
  // Security Configuration
  security: {
    tokenExpiryBuffer: 5 * 60 * 1000, // 5 minutes
    maxLoginAttempts: 5,
    sessionTimeout: 24 * 60 * 60 * 1000 // 24 hours
  }
}

// Development-only configurations
if (config.isDevelopment) {
  console.log('🔧 Development mode enabled')
  console.log('📊 Environment config:', {
    api: config.api,
    app: config.app,
    features: config.features
  })
}

import 'dotenv/config';

export default {
  expo: {
    name: "PropertyAI - Real Estate CRM",
    slug: "property-ai-crm",
    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/icon.png",
    userInterfaceStyle: "automatic",
    splash: {
      image: "./assets/splash.png",
      resizeMode: "contain",
      backgroundColor: "#2E86AB"
    },
    assetBundlePatterns: [
      "**/*"
    ],
    ios: {
      supportsTablet: true,
      bundleIdentifier: "com.propertyai.crm"
    },
    android: {
      adaptiveIcon: {
        foregroundImage: "./assets/adaptive-icon.png",
        backgroundColor: "#2E86AB"
      },
      package: "com.propertyai.crm"
    },
    web: {
      favicon: "./assets/favicon.png",
      bundler: "metro"
    },
    extra: {
      API_URL: process.env.API_URL,
      GROQ_API_KEY: process.env.GROQ_API_KEY,
      ENABLE_PUSH_NOTIFICATIONS: process.env.ENABLE_PUSH_NOTIFICATIONS === 'true',
      ENABLE_OFFLINE_MODE: process.env.ENABLE_OFFLINE_MODE === 'true',
    },
    plugins: [
      [
        "expo-image-picker",
        {
          photosPermission: "The app accesses your photos to let you upload profile pictures and property images.",
          cameraPermission: "The app accesses your camera to let you take photos for profiles and properties."
        }
      ]
    ]
  }
};
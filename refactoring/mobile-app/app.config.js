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
      GROQ_API_KEY: process.env.GROQ_API_KEY,
      API_BASE_URL: process.env.API_BASE_URL || "http://127.0.0.1:8003",
    },
    plugins: [
      "expo-secure-store",
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
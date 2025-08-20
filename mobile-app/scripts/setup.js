/**
 * Setup script for PropertyAI Mobile App
 * Cross-platform compatible setup script
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { version } = require('process');

const ROOT_DIR = path.resolve(__dirname, '..');

console.log('🚀 Setting up PropertyAI Mobile App...');

// Check Node.js version
const nodeVersion = process.version.slice(1).split('.')[0];
if (parseInt(nodeVersion) < 18) {
  console.error(`❌ Node.js version 18+ is required. Current version: ${process.version}`);
  process.exit(1);
}

console.log(`✅ Node.js ${process.version} detected`);

// Install Expo CLI globally if not already installed
try {
  execSync('npx expo --version', { stdio: 'ignore' });
  console.log('✅ Expo CLI already installed');
} catch (error) {
  console.log('📦 Installing Expo CLI...');
  try {
    execSync('npm install -g @expo/cli', { stdio: 'inherit' });
  } catch (err) {
    console.error('Error installing Expo CLI:', err);
  }
}

// Create .env file if it doesn't exist
const envPath = path.join(ROOT_DIR, '.env');
const envExamplePath = path.join(ROOT_DIR, '.env.example');

if (!fs.existsSync(envPath) && fs.existsSync(envExamplePath)) {
  console.log('📝 Creating .env file from template...');
  fs.copyFileSync(envExamplePath, envPath);
  console.log('');
  console.log('⚠️  IMPORTANT: Edit .env file and add your GROQ_API_KEY');
  console.log('   1. Get your API key from: https://console.groq.com');
  console.log('   2. Replace \'your_groq_api_key_here\' with your actual key');
  console.log('');
}

// Create necessary directories
const dirsToCreate = [
  path.join(ROOT_DIR, 'assets'),
  path.join(ROOT_DIR, 'src/screens'),
  path.join(ROOT_DIR, 'src/components'),
  path.join(ROOT_DIR, 'src/utils')
];

dirsToCreate.forEach(dir => {
  if (!fs.existsSync(dir)) {
    console.log(`📁 Creating directory: ${path.relative(ROOT_DIR, dir)}`);
    fs.mkdirSync(dir, { recursive: true });
  }
});

// Check for placeholder assets
const iconPath = path.join(ROOT_DIR, 'assets/icon.png');
const splashPath = path.join(ROOT_DIR, 'assets/splash.png');

if (!fs.existsSync(iconPath)) {
  console.log('📱 Missing placeholder app icon...');
  console.log('Placeholder icon needed at assets/icon.png (1024x1024 px)');
}

if (!fs.existsSync(splashPath)) {
  console.log('🎨 Missing placeholder splash screen...');
  console.log('Placeholder splash needed at assets/splash.png (1242x2436 px)');
}

// Install dependencies
console.log('📦 Installing dependencies...');
try {
  execSync('npm install', { stdio: 'inherit', cwd: ROOT_DIR });
} catch (err) {
  console.error('Error installing dependencies:', err);
}

console.log('');
console.log('✅ Setup complete!');
console.log('');
console.log('📖 Next steps:');
console.log('   1. Edit .env file and add your GROQ_API_KEY');
console.log('   2. Make sure backend server is running on port 8003');
console.log('   3. Run \'npm start\' to start the development server');
console.log('');
console.log('🔧 Troubleshooting:');
console.log('   • If you get Metro bundler errors, try: npm run start:clean');
console.log('   • For iOS simulator: npx expo start --ios');
console.log('   • For Android emulator: npx expo start --android');
console.log('   • For web browser: npx expo start --web');
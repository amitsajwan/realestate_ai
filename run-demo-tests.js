#!/usr/bin/env node

/**
 * Demo Test Runner for Real Estate Platform
 * =========================================
 * 
 * This script runs the demo Playwright tests to showcase functionality
 * without requiring the full application to be running.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🎭 Demo Test Runner for Real Estate Platform');
console.log('============================================\n');

// Configuration
const config = {
  testTimeout: 30000,
  screenshotPath: './demo-screenshots',
  reportPath: './demo-reports'
};

// Create directories for test artifacts
function createDirectories() {
  console.log('📁 Creating demo test directories...');
  
  if (!fs.existsSync(config.screenshotPath)) {
    fs.mkdirSync(config.screenshotPath, { recursive: true });
  }
  
  if (!fs.existsSync(config.reportPath)) {
    fs.mkdirSync(config.reportPath, { recursive: true });
  }
  
  console.log('✅ Demo test directories created');
}

// Install Playwright if not already installed
function installPlaywright() {
  console.log('📦 Checking Playwright installation...');
  
  try {
    execSync('npx playwright --version', { stdio: 'pipe' });
    console.log('✅ Playwright is installed');
  } catch (error) {
    console.log('📦 Installing Playwright...');
    try {
      execSync('npm install @playwright/test playwright', { stdio: 'inherit' });
      execSync('npx playwright install', { stdio: 'inherit' });
      console.log('✅ Playwright installed successfully');
    } catch (installError) {
      console.log('❌ Failed to install Playwright:', installError.message);
      return false;
    }
  }
  
  return true;
}

// Run demo tests
function runDemoTests() {
  console.log('\n🧪 Running Demo Tests...');
  console.log('='.repeat(50));
  
  try {
    const command = `npx playwright test demo-functionality-test.spec.ts --headed --timeout=${config.testTimeout}`;
    console.log(`Command: ${command}`);
    
    const output = execSync(command, { 
      stdio: 'inherit',
      cwd: process.cwd()
    });
    
    console.log('✅ Demo tests completed successfully');
    return true;
  } catch (error) {
    console.log('❌ Demo tests failed:', error.message);
    return false;
  }
}

// Generate demo report
function generateDemoReport(testPassed) {
  console.log('\n📊 Generating Demo Report...');
  
  const report = {
    timestamp: new Date().toISOString(),
    testType: 'Demo Functionality Tests',
    status: testPassed ? 'PASSED' : 'FAILED',
    description: 'Demonstration of Playwright testing capabilities for Real Estate Platform',
    features: [
      'Multi-step property creation form',
      'Form validation and error handling',
      'Responsive design testing',
      'Screenshot generation',
      'User interaction testing'
    ],
    screenshots: [
      'demo-01-initial-page.png',
      'demo-02-step1-filled.png',
      'demo-03-step2-filled.png',
      'demo-04-step3-pricing.png',
      'demo-05-step4-images.png',
      'demo-06-step5-description.png',
      'demo-07-property-created.png',
      'demo-validation-01-initial.png',
      'demo-validation-02-errors.png',
      'demo-validation-03-invalid-email.png',
      'demo-validation-04-invalid-price.png',
      'demo-validation-05-success.png',
      'demo-responsive-01-desktop.png',
      'demo-responsive-02-tablet.png',
      'demo-responsive-03-mobile.png'
    ]
  };
  
  const reportFile = path.join(config.reportPath, `demo-report-${Date.now()}.json`);
  fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
  
  console.log(`📄 Demo report saved: ${reportFile}`);
  
  // Generate HTML report
  const htmlReport = generateHTMLReport(report);
  const htmlReportFile = path.join(config.reportPath, `demo-report-${Date.now()}.html`);
  fs.writeFileSync(htmlReportFile, htmlReport);
  
  console.log(`🌐 HTML demo report saved: ${htmlReportFile}`);
  
  return report;
}

// Generate HTML report
function generateHTMLReport(report) {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real Estate Platform - Demo Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .status { padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; font-size: 18px; font-weight: bold; }
        .status.passed { background-color: #d4edda; color: #155724; }
        .status.failed { background-color: #f8d7da; color: #721c24; }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .feature { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff; }
        .screenshots { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; margin-top: 20px; }
        .screenshot { text-align: center; }
        .screenshot img { max-width: 100%; height: auto; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .screenshot p { margin: 5px 0 0 0; font-size: 0.9em; color: #666; }
        .info-box { background: #e7f3ff; border: 1px solid #b3d9ff; padding: 15px; border-radius: 8px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 Real Estate Platform - Demo Test Report</h1>
            <p>Generated on: ${new Date(report.timestamp).toLocaleString()}</p>
        </div>
        
        <div class="status ${report.status.toLowerCase()}">
            ${report.status === 'PASSED' ? '✅' : '❌'} ${report.status}
        </div>
        
        <div class="info-box">
            <h3>📋 About This Demo</h3>
            <p>${report.description}</p>
            <p>This demo showcases Playwright's capabilities for testing web applications, including form interactions, validation, responsive design, and screenshot generation.</p>
        </div>
        
        <h2>🎯 Tested Features</h2>
        <div class="features">
            ${report.features.map(feature => `
                <div class="feature">
                    <h4>${feature}</h4>
                </div>
            `).join('')}
        </div>
        
        <h2>📸 Generated Screenshots</h2>
        <div class="screenshots">
            ${report.screenshots.map(screenshot => `
                <div class="screenshot">
                    <img src="${screenshot}" alt="Demo Screenshot" onerror="this.style.display='none'">
                    <p>${screenshot}</p>
                </div>
            `).join('')}
        </div>
        
        <div class="info-box">
            <h3>🚀 Next Steps</h3>
            <p>To run these tests against your actual application:</p>
            <ol>
                <li>Start your application: <code>./start_app.sh</code></li>
                <li>Update the BASE_URL in the test files</li>
                <li>Run: <code>npx playwright test comprehensive-functionality-tests.spec.ts</code></li>
            </ol>
        </div>
    </div>
</body>
</html>`;
}

// Main execution
async function main() {
  console.log('🚀 Starting Demo Test Runner...\n');
  
  // Create directories
  createDirectories();
  
  // Install Playwright
  if (!installPlaywright()) {
    console.log('❌ Failed to install Playwright. Exiting.');
    process.exit(1);
  }
  
  // Run demo tests
  const testPassed = runDemoTests();
  
  // Generate report
  const report = generateDemoReport(testPassed);
  
  // Print summary
  console.log('\n🎯 Demo Test Summary');
  console.log('==================');
  console.log(`Status: ${report.status} ${report.status === 'PASSED' ? '✅' : '❌'}`);
  console.log(`Features Tested: ${report.features.length}`);
  console.log(`Screenshots Generated: ${report.screenshots.length}`);
  
  if (testPassed) {
    console.log('\n🎉 Demo tests completed successfully!');
    console.log('📸 Check the generated screenshots to see the test execution');
    console.log('📄 View the HTML report for detailed results');
  } else {
    console.log('\n❌ Demo tests failed. Check the output above for details.');
    process.exit(1);
  }
}

// Handle errors
process.on('unhandledRejection', (error) => {
  console.error('❌ Unhandled error:', error);
  process.exit(1);
});

// Run the main function
main().catch((error) => {
  console.error('❌ Demo test runner failed:', error);
  process.exit(1);
});
#!/usr/bin/env node

/**
 * Playwright Test Runner for Real Estate Platform
 * ===============================================
 * 
 * This script runs comprehensive Playwright tests to verify functionality
 * and generates detailed reports with screenshots.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🎭 Playwright Test Runner for Real Estate Platform');
console.log('==================================================\n');

// Configuration
const config = {
  baseUrl: process.env.E2E_BASE_URL || 'http://localhost:3000',
  apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000',
  testTimeout: 60000,
  screenshotPath: './test-screenshots',
  reportPath: './test-reports'
};

// Create directories for test artifacts
function createDirectories() {
  console.log('📁 Creating test directories...');
  
  if (!fs.existsSync(config.screenshotPath)) {
    fs.mkdirSync(config.screenshotPath, { recursive: true });
  }
  
  if (!fs.existsSync(config.reportPath)) {
    fs.mkdirSync(config.reportPath, { recursive: true });
  }
  
  console.log('✅ Test directories created');
}

// Check if application is running
async function checkApplicationStatus() {
  console.log('🔍 Checking application status...');
  
  try {
    const { default: fetch } = await import('node-fetch');
    
    // Check frontend
    try {
      const frontendResponse = await fetch(config.baseUrl, { timeout: 5000 });
      console.log(`✅ Frontend accessible: ${frontendResponse.status}`);
    } catch (error) {
      console.log('❌ Frontend not accessible:', error.message);
      return false;
    }
    
    // Check backend
    try {
      const backendResponse = await fetch(`${config.apiBaseUrl}/health`, { timeout: 5000 });
      console.log(`✅ Backend accessible: ${backendResponse.status}`);
    } catch (error) {
      console.log('❌ Backend not accessible:', error.message);
      return false;
    }
    
    return true;
  } catch (error) {
    console.log('❌ Error checking application status:', error.message);
    return false;
  }
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

// Run specific test suite
function runTestSuite(testFile, description) {
  console.log(`\n🧪 Running ${description}...`);
  console.log('='.repeat(50));
  
  try {
    const command = `npx playwright test ${testFile} --headed --timeout=${config.testTimeout}`;
    console.log(`Command: ${command}`);
    
    const output = execSync(command, { 
      stdio: 'inherit',
      cwd: process.cwd(),
      env: {
        ...process.env,
        E2E_BASE_URL: config.baseUrl,
        API_BASE_URL: config.apiBaseUrl
      }
    });
    
    console.log(`✅ ${description} completed successfully`);
    return true;
  } catch (error) {
    console.log(`❌ ${description} failed:`, error.message);
    return false;
  }
}

// Generate test report
function generateTestReport(results) {
  console.log('\n📊 Generating Test Report...');
  
  const report = {
    timestamp: new Date().toISOString(),
    configuration: config,
    results: results,
    summary: {
      total: results.length,
      passed: results.filter(r => r.passed).length,
      failed: results.filter(r => !r.passed).length
    }
  };
  
  const reportFile = path.join(config.reportPath, `test-report-${Date.now()}.json`);
  fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
  
  console.log(`📄 Test report saved: ${reportFile}`);
  
  // Generate HTML report
  const htmlReport = generateHTMLReport(report);
  const htmlReportFile = path.join(config.reportPath, `test-report-${Date.now()}.html`);
  fs.writeFileSync(htmlReportFile, htmlReport);
  
  console.log(`🌐 HTML report saved: ${htmlReportFile}`);
  
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
    <title>Real Estate Platform - Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .summary-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
        .summary-card h3 { margin: 0 0 10px 0; color: #333; }
        .summary-card .number { font-size: 2em; font-weight: bold; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .test-result { margin-bottom: 20px; padding: 15px; border-radius: 8px; }
        .test-passed { background-color: #d4edda; border-left: 4px solid #28a745; }
        .test-failed { background-color: #f8d7da; border-left: 4px solid #dc3545; }
        .screenshots { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; margin-top: 20px; }
        .screenshot { text-align: center; }
        .screenshot img { max-width: 100%; height: auto; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .screenshot p { margin: 5px 0 0 0; font-size: 0.9em; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 Real Estate Platform - Test Report</h1>
            <p>Generated on: ${new Date(report.timestamp).toLocaleString()}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="number">${report.summary.total}</div>
            </div>
            <div class="summary-card">
                <h3>Passed</h3>
                <div class="number passed">${report.summary.passed}</div>
            </div>
            <div class="summary-card">
                <h3>Failed</h3>
                <div class="number failed">${report.summary.failed}</div>
            </div>
            <div class="summary-card">
                <h3>Success Rate</h3>
                <div class="number">${Math.round((report.summary.passed / report.summary.total) * 100)}%</div>
            </div>
        </div>
        
        <h2>Test Results</h2>
        ${report.results.map(result => `
            <div class="test-result ${result.passed ? 'test-passed' : 'test-failed'}">
                <h3>${result.name}</h3>
                <p><strong>Status:</strong> ${result.passed ? '✅ PASSED' : '❌ FAILED'}</p>
                <p><strong>Description:</strong> ${result.description}</p>
                ${result.error ? `<p><strong>Error:</strong> ${result.error}</p>` : ''}
                ${result.screenshots && result.screenshots.length > 0 ? `
                    <div class="screenshots">
                        ${result.screenshots.map(screenshot => `
                            <div class="screenshot">
                                <img src="${screenshot}" alt="Test Screenshot">
                                <p>${path.basename(screenshot)}</p>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('')}
        
        <h2>Configuration</h2>
        <pre>${JSON.stringify(report.configuration, null, 2)}</pre>
    </div>
</body>
</html>`;
}

// Main execution
async function main() {
  console.log('🚀 Starting Playwright Test Runner...\n');
  
  // Create directories
  createDirectories();
  
  // Install Playwright
  if (!installPlaywright()) {
    console.log('❌ Failed to install Playwright. Exiting.');
    process.exit(1);
  }
  
  // Check application status
  const appRunning = await checkApplicationStatus();
  if (!appRunning) {
    console.log('⚠️ Application is not running. Some tests may fail.');
    console.log('💡 To start the application, run: ./start_app.sh');
  }
  
  // Define test suites
  const testSuites = [
    {
      file: 'comprehensive-functionality-tests.spec.ts',
      name: 'Comprehensive Functionality Tests',
      description: 'Complete user journey and core functionality'
    },
    {
      file: 'e2e-tests/onboarding.spec.ts',
      name: 'Onboarding Flow Tests',
      description: 'User onboarding process'
    },
    {
      file: 'e2e-tests/property-creation-proof.spec.ts',
      name: 'Property Creation Tests',
      description: 'Property creation and management'
    }
  ];
  
  // Run test suites
  const results = [];
  
  for (const suite of testSuites) {
    if (fs.existsSync(suite.file)) {
      const passed = runTestSuite(suite.file, suite.description);
      results.push({
        name: suite.name,
        description: suite.description,
        passed: passed,
        file: suite.file
      });
    } else {
      console.log(`⚠️ Test file not found: ${suite.file}`);
      results.push({
        name: suite.name,
        description: suite.description,
        passed: false,
        error: `Test file not found: ${suite.file}`
      });
    }
  }
  
  // Generate report
  const report = generateTestReport(results);
  
  // Print summary
  console.log('\n🎯 Test Execution Summary');
  console.log('========================');
  console.log(`Total Tests: ${report.summary.total}`);
  console.log(`Passed: ${report.summary.passed} ✅`);
  console.log(`Failed: ${report.summary.failed} ❌`);
  console.log(`Success Rate: ${Math.round((report.summary.passed / report.summary.total) * 100)}%`);
  
  if (report.summary.failed > 0) {
    console.log('\n❌ Some tests failed. Check the detailed report for more information.');
    process.exit(1);
  } else {
    console.log('\n🎉 All tests passed successfully!');
    process.exit(0);
  }
}

// Handle errors
process.on('unhandledRejection', (error) => {
  console.error('❌ Unhandled error:', error);
  process.exit(1);
});

// Run the main function
main().catch((error) => {
  console.error('❌ Test runner failed:', error);
  process.exit(1);
});
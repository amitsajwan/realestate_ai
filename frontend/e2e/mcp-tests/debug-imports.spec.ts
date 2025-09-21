import { test, expect } from '@playwright/test';

/**
 * Debug Import and Module Loading Issues
 * ======================================
 */

test.describe('Debug Import Issues', () => {
  
  test('Check if modules are loading in browser', async ({ page }) => {
    
    console.log('🔍 Debugging module imports...');
    
    const errors: string[] = [];
    const logs: string[] = [];
    
    // Capture all console messages
    page.on('console', msg => {
      logs.push(`${msg.type()}: ${msg.text()}`);
      if (msg.type() === 'error') {
        errors.push(msg.text());
        console.log(`❌ Error: ${msg.text()}`);
      }
    });
    
    // Capture network errors
    page.on('response', response => {
      if (response.status() >= 400) {
        console.log(`🌐 Network Error: ${response.status()} ${response.url()}`);
      }
    });
    
    // Go to login page
    await page.goto('/login');
    
    // Wait for page to load
    await page.waitForTimeout(3000);
    
    // Check if any JavaScript modules failed to load
    const moduleErrors = errors.filter(error => 
      error.includes('Failed to load module') ||
      error.includes('Cannot resolve module') ||
      error.includes('Module not found') ||
      error.includes('Import') ||
      error.includes('auth') ||
      error.includes('component')
    );
    
    console.log(`📦 Module errors found: ${moduleErrors.length}`);
    moduleErrors.forEach(error => console.log(`   ${error}`));
    
    // Check if AuthManager is available in window
    const authManagerCheck = await page.evaluate(() => {
      // Check if authManager is in global scope
      const hasAuthManager = typeof (window as any).authManager !== 'undefined';
      
      // Check if we can access it through Next.js modules
      const moduleCheck = {
        hasAuthManager,
        authManagerType: typeof (window as any).authManager,
        windowKeys: Object.keys(window).filter(key => key.includes('auth')),
        documentScripts: Array.from(document.scripts).map(script => script.src).filter(src => src.includes('auth')),
        localStorage: Object.keys(localStorage),
        sessionStorage: Object.keys(sessionStorage)
      };
      
      return moduleCheck;
    });
    
    console.log('🔐 AuthManager Check:', JSON.stringify(authManagerCheck, null, 2));
    
    // Check page content for clues
    const pageContent = await page.content();
    const contentChecks = {
      hasAuthManager: pageContent.includes('AuthManager'),
      hasLoginForm: pageContent.includes('LoginForm'),
      hasLoadingStates: pageContent.includes('LoadingButton'),
      hasUseLoading: pageContent.includes('useFormSubmission'),
      hasLoadingText: pageContent.includes('Loading...'),
      hasEmailInput: pageContent.includes('input'),
      hasForm: pageContent.includes('<form'),
      scriptTags: (pageContent.match(/<script[^>]*>/g) || []).length
    };
    
    console.log('📄 Content Checks:', JSON.stringify(contentChecks, null, 2));
    
    // Check if any components are rendered
    const componentChecks = await page.evaluate(() => {
      return {
        forms: document.querySelectorAll('form').length,
        inputs: document.querySelectorAll('input').length,
        buttons: document.querySelectorAll('button').length,
        divs: document.querySelectorAll('div').length,
        bodyText: document.body.textContent?.substring(0, 200) || '',
        hasReactRoot: !!document.querySelector('#__next') || !!document.querySelector('#root'),
        hasNextScript: !!document.querySelector('script[src*="_next"]')
      };
    });
    
    console.log('🧩 Component Checks:', JSON.stringify(componentChecks, null, 2));
    
    // Take screenshot
    await page.screenshot({ path: 'debug-imports.png' });
    console.log('📸 Screenshot saved: debug-imports.png');
    
    // Summary
    console.log('\n📊 SUMMARY:');
    console.log(`   Total console logs: ${logs.length}`);
    console.log(`   Total errors: ${errors.length}`);
    console.log(`   Module errors: ${moduleErrors.length}`);
    console.log(`   Forms rendered: ${componentChecks.forms}`);
    console.log(`   Inputs rendered: ${componentChecks.inputs}`);
    console.log(`   AuthManager available: ${authManagerCheck.hasAuthManager}`);
  });

  test('Test direct component rendering', async ({ page }) => {
    
    console.log('🧪 Testing direct component access...');
    
    // Go to login page
    await page.goto('/login');
    
    // Wait for page to load
    await page.waitForTimeout(5000);
    
    // Try to interact with any elements that might be there
    const elements = await page.evaluate(() => {
      const allElements = document.querySelectorAll('*');
      const elementInfo = Array.from(allElements).map(el => ({
        tagName: el.tagName,
        className: el.className,
        id: el.id,
        textContent: el.textContent?.substring(0, 50) || '',
        visible: el.offsetParent !== null
      })).filter(info => info.visible);
      
      return elementInfo.slice(0, 20); // First 20 visible elements
    });
    
    console.log('👁️ Visible Elements:');
    elements.forEach(el => {
      console.log(`   ${el.tagName}${el.className ? '.' + el.className.split(' ')[0] : ''}${el.id ? '#' + el.id : ''}: "${el.textContent}"`);
    });
    
    // Try to find any interactive elements
    const interactiveElements = await page.evaluate(() => {
      return {
        clickable: document.querySelectorAll('button, a, input[type="submit"], input[type="button"]').length,
        inputs: document.querySelectorAll('input').length,
        forms: document.querySelectorAll('form').length,
        links: document.querySelectorAll('a').length
      };
    });
    
    console.log('🖱️ Interactive Elements:', JSON.stringify(interactiveElements, null, 2));
  });
});
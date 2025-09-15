const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function captureScreenshots() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // Set viewport size
  await page.setViewportSize({ width: 1920, height: 1080 });
  
  try {
    // Navigate to the posting workflow page
    await page.goto('http://localhost:3000/test');
    await page.waitForLoadState('networkidle');
    
    // Create screenshots directory
    const screenshotsDir = path.join(__dirname, 'screenshots', 'posting-workflow');
    if (!fs.existsSync(screenshotsDir)) {
      fs.mkdirSync(screenshotsDir, { recursive: true });
    }
    
    // Step 1: Select Property
    console.log('Capturing Step 1: Select Property');
    await page.screenshot({ 
      path: path.join(screenshotsDir, '01-select-property.png'),
      fullPage: true 
    });
    
    // Click on first property
    await page.click('div[class*="p-4 border-2 rounded-lg cursor-pointer"]:first-child');
    await page.waitForTimeout(500);
    
    // Step 2: Generate Content
    console.log('Capturing Step 2: Generate Content');
    await page.click('button:has-text("Next")');
    await page.waitForTimeout(1000);
    
    // Fill in content
    await page.fill('textarea', 'Create an engaging social media post for a luxury apartment');
    await page.check('input[type="checkbox"]');
    await page.waitForTimeout(1000);
    
    await page.screenshot({ 
      path: path.join(screenshotsDir, '02-generate-content.png'),
      fullPage: true 
    });
    
    // Step 3: Choose Channels
    console.log('Capturing Step 3: Choose Channels');
    await page.click('button:has-text("Next")');
    await page.waitForTimeout(1000);
    
    // Select Facebook and Instagram
    await page.click('div:has-text("Facebook")');
    await page.click('div:has-text("Instagram")');
    await page.waitForTimeout(500);
    
    await page.screenshot({ 
      path: path.join(screenshotsDir, '03-choose-channels.png'),
      fullPage: true 
    });
    
    // Step 4: Schedule Post
    console.log('Capturing Step 4: Schedule Post');
    await page.click('button:has-text("Next")');
    await page.waitForTimeout(1000);
    
    // Select "Publish Now"
    await page.click('div:has-text("Publish Now")');
    await page.waitForTimeout(500);
    
    await page.screenshot({ 
      path: path.join(screenshotsDir, '04-schedule-post.png'),
      fullPage: true 
    });
    
    // Step 5: Review & Publish
    console.log('Capturing Step 5: Review & Publish');
    await page.click('button:has-text("Next")');
    await page.waitForTimeout(1000);
    
    await page.screenshot({ 
      path: path.join(screenshotsDir, '05-review-publish.png'),
      fullPage: true 
    });
    
    // Mobile view
    console.log('Capturing Mobile View');
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('http://localhost:3000/test');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    await page.screenshot({ 
      path: path.join(screenshotsDir, '06-mobile-view.png'),
      fullPage: true 
    });
    
    console.log('✅ Screenshots captured successfully!');
    
  } catch (error) {
    console.error('❌ Error capturing screenshots:', error);
  } finally {
    await browser.close();
  }
}

captureScreenshots().catch(console.error);
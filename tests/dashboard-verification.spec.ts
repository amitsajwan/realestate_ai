import { test, expect } from '@playwright/test';

test('verify clean dashboard without onboarding', async ({ page }) => {
    // Login first
    await page.goto('/');
    await page.fill('#email', 'demo@mumbai.com');
    await page.fill('#password', 'demo123');
    await page.click('button[type="submit"]');
    
    // Wait for redirect to dashboard
    await page.waitForURL('/dashboard');
    
    // Verify it's the correct dashboard
    await expect(page).toHaveTitle(/PropertyAI - Next-Gen AI Real Estate Dashboard/);
    
    // Check for the proper navigation
    await expect(page.locator('.navbar-brand-nextgen')).toContainText('PropertyAI');
    await expect(page.locator('.ai-badge')).toContainText('AI Powered');
    
    // Verify it has the right sections (no onboarding mixed in)
    await expect(page.locator('h3:has-text("AI Content Generation")')).toBeVisible();
    await expect(page.locator('h3:has-text("Social Media Automation")')).toBeVisible();
    await expect(page.locator('h3:has-text("AI-Powered Analytics")')).toBeVisible();
    
    // Check for stats cards
    await expect(page.locator('.stat-card')).toHaveCount(4);
    
    // Verify onboarding is only in the sidebar navigation, not mixed in content
    const sidebarOnboardingLink = page.locator('.nav-item-nextgen[href="/modern-onboarding"]');
    await expect(sidebarOnboardingLink).toBeVisible();
    await expect(sidebarOnboardingLink).toContainText('AI Onboarding');
    
    // Verify no onboarding forms or steps are visible in main content
    await expect(page.locator('#firstName')).not.toBeVisible();
    await expect(page.locator('#lastName')).not.toBeVisible();
    await expect(page.locator('#companyName')).not.toBeVisible();
    
    // Check for AI assistant
    await expect(page.locator('.ai-assistant')).toBeVisible();
    
    console.log('✅ Dashboard verification passed - clean dashboard without onboarding mixed in');
});

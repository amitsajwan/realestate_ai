import { test, expect } from '@playwright/test';

test.describe('CRM System', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication and navigate to dashboard
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('authState', JSON.stringify({
        isAuthenticated: true,
        user: { id: 'test-user-id', email: 'test@example.com' }
      }));
    });

    // Mock CRM data
    await page.route('**/api/v1/crm/leads', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          leads: [
            {
              id: 'lead-1',
              name: 'John Smith',
              email: 'john.smith@example.com',
              phone: '+1234567890',
              status: 'new',
              source: 'website',
              priority: 'high',
              property_interest: 'Beautiful 3BR Apartment',
              budget: 500000,
              timeline: '3 months',
              notes: 'Looking for family home',
              created_at: '2024-01-01T00:00:00Z',
              updated_at: '2024-01-01T00:00:00Z'
            },
            {
              id: 'lead-2',
              name: 'Sarah Johnson',
              email: 'sarah.johnson@example.com',
              phone: '+1234567891',
              status: 'contacted',
              source: 'referral',
              priority: 'medium',
              property_interest: 'Luxury Penthouse',
              budget: 1200000,
              timeline: '6 months',
              notes: 'Investor looking for luxury property',
              created_at: '2024-01-02T00:00:00Z',
              updated_at: '2024-01-02T00:00:00Z'
            }
          ],
          stats: {
            total_leads: 150,
            new_leads: 45,
            contacted_leads: 60,
            qualified_leads: 30,
            converted_leads: 15,
            conversion_rate: 10.0
          }
        })
      });
    });
  });

  test('should display CRM dashboard', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Check if CRM dashboard is visible
    await expect(page.locator('text=CRM Dashboard')).toBeVisible();
    await expect(page.locator('[data-testid="crm-dashboard"]')).toBeVisible();
  });

  test('should display lead statistics', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Check if lead statistics are visible
    await expect(page.locator('[data-testid="lead-stats"]')).toBeVisible();
    await expect(page.locator('text=Total Leads')).toBeVisible();
    await expect(page.locator('text=150')).toBeVisible();
    await expect(page.locator('text=New Leads')).toBeVisible();
    await expect(page.locator('text=45')).toBeVisible();
    await expect(page.locator('text=Contacted')).toBeVisible();
    await expect(page.locator('text=60')).toBeVisible();
    await expect(page.locator('text=Qualified')).toBeVisible();
    await expect(page.locator('text=30')).toBeVisible();
    await expect(page.locator('text=Converted')).toBeVisible();
    await expect(page.locator('text=15')).toBeVisible();
    await expect(page.locator('text=Conversion Rate')).toBeVisible();
    await expect(page.locator('text=10.0%')).toBeVisible();
  });

  test('should display leads list', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Check if leads list is visible
    await expect(page.locator('[data-testid="leads-list"]')).toBeVisible();
    await expect(page.locator('text=John Smith')).toBeVisible();
    await expect(page.locator('text=Sarah Johnson')).toBeVisible();
  });

  test('should display lead details', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Check if lead details are visible
    await expect(page.locator('text=john.smith@example.com')).toBeVisible();
    await expect(page.locator('text=+1234567890')).toBeVisible();
    await expect(page.locator('text=New')).toBeVisible();
    await expect(page.locator('text=Website')).toBeVisible();
    await expect(page.locator('text=High')).toBeVisible();
  });

  test('should create new lead', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Click add lead button
    await page.click('button[data-testid="add-lead"]');
    
    // Check if lead creation form is visible
    await expect(page.locator('[data-testid="lead-form"]')).toBeVisible();
    await expect(page.locator('text=Create New Lead')).toBeVisible();
  });

  test('should fill lead creation form', async ({ page }) => {
    // Navigate to CRM and open lead form
    await page.click('text=CRM');
    await page.click('button[data-testid="add-lead"]');
    
    // Fill lead details
    await page.fill('input[name="name"]', 'Jane Doe');
    await page.fill('input[name="email"]', 'jane.doe@example.com');
    await page.fill('input[name="phone"]', '+1234567892');
    await page.selectOption('select[name="status"]', 'new');
    await page.selectOption('select[name="source"]', 'website');
    await page.selectOption('select[name="priority"]', 'medium');
    await page.fill('input[name="propertyInterest"]', '2BR Apartment');
    await page.fill('input[name="budget"]', '400000');
    await page.selectOption('select[name="timeline"]', '6 months');
    await page.fill('textarea[name="notes"]', 'First-time buyer');
  });

  test('should save new lead', async ({ page }) => {
    // Navigate to CRM and open lead form
    await page.click('text=CRM');
    await page.click('button[data-testid="add-lead"]');
    
    // Fill lead details
    await page.fill('input[name="name"]', 'Jane Doe');
    await page.fill('input[name="email"]', 'jane.doe@example.com');
    await page.fill('input[name="phone"]', '+1234567892');
    await page.selectOption('select[name="status"]', 'new');
    await page.selectOption('select[name="source"]', 'website');
    await page.selectOption('select[name="priority"]', 'medium');
    await page.fill('input[name="propertyInterest"]', '2BR Apartment');
    await page.fill('input[name="budget"]', '400000');
    await page.selectOption('select[name="timeline"]', '6 months');
    await page.fill('textarea[name="notes"]', 'First-time buyer');
    
    // Save lead
    await page.click('button[data-testid="save-lead"]');
    
    // Should show success message
    await expect(page.locator('text=Lead created successfully')).toBeVisible();
  });

  test('should edit existing lead', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Click edit button on first lead
    await page.click('[data-testid="lead-item"] button[data-testid="edit-lead"]');
    
    // Should open edit form
    await expect(page.locator('[data-testid="lead-form"]')).toBeVisible();
    await expect(page.locator('text=Edit Lead')).toBeVisible();
    
    // Modify lead details
    await page.fill('input[name="name"]', 'John Smith Updated');
    await page.selectOption('select[name="status"]', 'contacted');
    
    // Save changes
    await page.click('button[data-testid="save-lead"]');
    
    // Should show success message
    await expect(page.locator('text=Lead updated successfully')).toBeVisible();
  });

  test('should delete lead', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Click delete button on first lead
    await page.click('[data-testid="lead-item"] button[data-testid="delete-lead"]');
    
    // Should show confirmation dialog
    await expect(page.locator('[data-testid="delete-confirmation"]')).toBeVisible();
    await expect(page.locator('text=Are you sure you want to delete this lead?')).toBeVisible();
    
    // Confirm deletion
    await page.click('button[data-testid="confirm-delete"]');
    
    // Should show success message
    await expect(page.locator('text=Lead deleted successfully')).toBeVisible();
  });

  test('should filter leads by status', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Filter by new status
    await page.selectOption('select[name="statusFilter"]', 'new');
    
    // Should show only new leads
    await expect(page.locator('[data-testid="lead-item"][data-status="new"]')).toBeVisible();
  });

  test('should filter leads by priority', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Filter by high priority
    await page.selectOption('select[name="priorityFilter"]', 'high');
    
    // Should show only high priority leads
    await expect(page.locator('[data-testid="lead-item"][data-priority="high"]')).toBeVisible();
  });

  test('should search leads', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Search for lead by name
    await page.fill('input[name="search"]', 'John Smith');
    await page.click('button[data-testid="search-leads"]');
    
    // Should show search results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    await expect(page.locator('text=John Smith')).toBeVisible();
  });

  test('should add lead activity', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Click on first lead
    await page.click('[data-testid="lead-item"]');
    
    // Should open lead details
    await expect(page.locator('[data-testid="lead-details"]')).toBeVisible();
    
    // Click add activity button
    await page.click('button[data-testid="add-activity"]');
    
    // Should open activity form
    await expect(page.locator('[data-testid="activity-form"]')).toBeVisible();
    
    // Fill activity details
    await page.selectOption('select[name="activityType"]', 'call');
    await page.fill('textarea[name="description"]', 'Called client to discuss property requirements');
    await page.fill('input[name="scheduledAt"]', '2024-12-31T10:00');
    
    // Save activity
    await page.click('button[data-testid="save-activity"]');
    
    // Should show success message
    await expect(page.locator('text=Activity added successfully')).toBeVisible();
  });

  test('should view lead timeline', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Click on first lead
    await page.click('[data-testid="lead-item"]');
    
    // Should open lead details
    await expect(page.locator('[data-testid="lead-details"]')).toBeVisible();
    
    // Check if timeline is visible
    await expect(page.locator('[data-testid="lead-timeline"]')).toBeVisible();
    await expect(page.locator('text=Lead Timeline')).toBeVisible();
  });

  test('should update lead status', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Click status dropdown on first lead
    await page.click('[data-testid="lead-item"] select[name="status"]');
    
    // Select new status
    await page.selectOption('[data-testid="lead-item"] select[name="status"]', 'contacted');
    
    // Should update lead status
    await expect(page.locator('[data-testid="lead-item"][data-status="contacted"]')).toBeVisible();
  });

  test('should assign lead to team member', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Click assign button on first lead
    await page.click('[data-testid="lead-item"] button[data-testid="assign-lead"]');
    
    // Should open assignment modal
    await expect(page.locator('[data-testid="assignment-modal"]')).toBeVisible();
    
    // Select team member
    await page.selectOption('select[name="assignedTo"]', 'agent-1');
    
    // Assign lead
    await page.click('button[data-testid="assign-lead"]');
    
    // Should show success message
    await expect(page.locator('text=Lead assigned successfully')).toBeVisible();
  });

  test('should export leads data', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Click export button
    await page.click('button[data-testid="export-leads"]');
    
    // Should show export options
    await expect(page.locator('[data-testid="export-options"]')).toBeVisible();
    await expect(page.locator('text=Export as CSV')).toBeVisible();
    await expect(page.locator('text=Export as Excel')).toBeVisible();
  });

  test('should display lead conversion funnel', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Check if conversion funnel is visible
    await expect(page.locator('[data-testid="conversion-funnel"]')).toBeVisible();
    await expect(page.locator('text=Lead Conversion Funnel')).toBeVisible();
    await expect(page.locator('text=New')).toBeVisible();
    await expect(page.locator('text=Contacted')).toBeVisible();
    await expect(page.locator('text=Qualified')).toBeVisible();
    await expect(page.locator('text=Converted')).toBeVisible();
  });

  test('should display lead source analytics', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Check if lead source analytics is visible
    await expect(page.locator('[data-testid="lead-source-analytics"]')).toBeVisible();
    await expect(page.locator('text=Lead Sources')).toBeVisible();
    await expect(page.locator('text=Website')).toBeVisible();
    await expect(page.locator('text=Referral')).toBeVisible();
    await expect(page.locator('text=Social Media')).toBeVisible();
  });

  test('should handle lead creation error', async ({ page }) => {
    // Mock API error
    await page.route('**/api/v1/crm/leads', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'CRM service unavailable' })
      });
    });
    
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Should show error message
    await expect(page.locator('text=Failed to load leads')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Check if CRM is still usable on mobile
    await expect(page.locator('[data-testid="crm-dashboard"]')).toBeVisible();
    await expect(page.locator('[data-testid="leads-list"]')).toBeVisible();
  });

  test('should display lead notes', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Click on first lead
    await page.click('[data-testid="lead-item"]');
    
    // Should open lead details
    await expect(page.locator('[data-testid="lead-details"]')).toBeVisible();
    
    // Check if notes are visible
    await expect(page.locator('text=Notes')).toBeVisible();
    await expect(page.locator('text=Looking for family home')).toBeVisible();
  });

  test('should add lead notes', async ({ page }) => {
    // Navigate to CRM
    await page.click('text=CRM');
    
    // Click on first lead
    await page.click('[data-testid="lead-item"]');
    
    // Should open lead details
    await expect(page.locator('[data-testid="lead-details"]')).toBeVisible();
    
    // Click add note button
    await page.click('button[data-testid="add-note"]');
    
    // Should open note form
    await expect(page.locator('[data-testid="note-form"]')).toBeVisible();
    
    // Fill note details
    await page.fill('textarea[name="note"]', 'Client is very interested in the property');
    
    // Save note
    await page.click('button[data-testid="save-note"]');
    
    // Should show success message
    await expect(page.locator('text=Note added successfully')).toBeVisible();
  });
});
import { test, expect } from '@playwright/test';

test.describe('Team Management System', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication and navigate to dashboard
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('authState', JSON.stringify({
        isAuthenticated: true,
        user: { id: 'test-user-id', email: 'test@example.com', role: 'admin' }
      }));
    });

    // Mock team data
    await page.route('**/api/v1/team', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          team: {
            id: 'team-1',
            name: 'PropertyAI Team',
            members: [
              {
                id: 'member-1',
                name: 'John Doe',
                email: 'john.doe@example.com',
                role: 'admin',
                status: 'active',
                permissions: ['read', 'write', 'delete'],
                joined_at: '2024-01-01T00:00:00Z'
              },
              {
                id: 'member-2',
                name: 'Jane Smith',
                email: 'jane.smith@example.com',
                role: 'agent',
                status: 'active',
                permissions: ['read', 'write'],
                joined_at: '2024-01-02T00:00:00Z'
              },
              {
                id: 'member-3',
                name: 'Bob Johnson',
                email: 'bob.johnson@example.com',
                role: 'viewer',
                status: 'inactive',
                permissions: ['read'],
                joined_at: '2024-01-03T00:00:00Z'
              }
            ]
          }
        })
      });
    });
  });

  test('should display team management dashboard', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Check if team management interface is visible
    await expect(page.locator('text=Team Management')).toBeVisible();
    await expect(page.locator('[data-testid="team-dashboard"]')).toBeVisible();
  });

  test('should display team members list', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Check if team members list is visible
    await expect(page.locator('[data-testid="team-members-list"]')).toBeVisible();
    await expect(page.locator('text=John Doe')).toBeVisible();
    await expect(page.locator('text=Jane Smith')).toBeVisible();
    await expect(page.locator('text=Bob Johnson')).toBeVisible();
  });

  test('should display member details', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Check if member details are visible
    await expect(page.locator('text=john.doe@example.com')).toBeVisible();
    await expect(page.locator('text=Admin')).toBeVisible();
    await expect(page.locator('text=Active')).toBeVisible();
    await expect(page.locator('text=Read, Write, Delete')).toBeVisible();
  });

  test('should invite new team member', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Click invite member button
    await page.click('button[data-testid="invite-member"]');
    
    // Check if invite form is visible
    await expect(page.locator('[data-testid="invite-form"]')).toBeVisible();
    await expect(page.locator('text=Invite Team Member')).toBeVisible();
  });

  test('should fill invite form', async ({ page }) => {
    // Navigate to team management and open invite form
    await page.click('text=Team Management');
    await page.click('button[data-testid="invite-member"]');
    
    // Fill invite details
    await page.fill('input[name="email"]', 'new.member@example.com');
    await page.fill('input[name="name"]', 'New Member');
    await page.selectOption('select[name="role"]', 'agent');
    await page.check('input[name="permissions"][value="read"]');
    await page.check('input[name="permissions"][value="write"]');
    await page.fill('textarea[name="message"]', 'Welcome to our team!');
  });

  test('should send invitation', async ({ page }) => {
    // Navigate to team management and open invite form
    await page.click('text=Team Management');
    await page.click('button[data-testid="invite-member"]');
    
    // Fill invite details
    await page.fill('input[name="email"]', 'new.member@example.com');
    await page.fill('input[name="name"]', 'New Member');
    await page.selectOption('select[name="role"]', 'agent');
    await page.check('input[name="permissions"][value="read"]');
    await page.check('input[name="permissions"][value="write"]');
    await page.fill('textarea[name="message"]', 'Welcome to our team!');
    
    // Send invitation
    await page.click('button[data-testid="send-invitation"]');
    
    // Should show success message
    await expect(page.locator('text=Invitation sent successfully')).toBeVisible();
  });

  test('should edit team member', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Click edit button on first member
    await page.click('[data-testid="member-item"] button[data-testid="edit-member"]');
    
    // Should open edit form
    await expect(page.locator('[data-testid="edit-member-form"]')).toBeVisible();
    await expect(page.locator('text=Edit Team Member')).toBeVisible();
  });

  test('should update member role', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Click edit button on first member
    await page.click('[data-testid="member-item"] button[data-testid="edit-member"]');
    
    // Update role
    await page.selectOption('select[name="role"]', 'agent');
    
    // Save changes
    await page.click('button[data-testid="save-member"]');
    
    // Should show success message
    await expect(page.locator('text=Member updated successfully')).toBeVisible();
  });

  test('should update member permissions', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Click edit button on first member
    await page.click('[data-testid="member-item"] button[data-testid="edit-member"]');
    
    // Update permissions
    await page.uncheck('input[name="permissions"][value="delete"]');
    await page.check('input[name="permissions"][value="read"]');
    await page.check('input[name="permissions"][value="write"]');
    
    // Save changes
    await page.click('button[data-testid="save-member"]');
    
    // Should show success message
    await expect(page.locator('text=Member updated successfully')).toBeVisible();
  });

  test('should remove team member', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Click remove button on first member
    await page.click('[data-testid="member-item"] button[data-testid="remove-member"]');
    
    // Should show confirmation dialog
    await expect(page.locator('[data-testid="remove-confirmation"]')).toBeVisible();
    await expect(page.locator('text=Are you sure you want to remove this team member?')).toBeVisible();
    
    // Confirm removal
    await page.click('button[data-testid="confirm-remove"]');
    
    // Should show success message
    await expect(page.locator('text=Team member removed successfully')).toBeVisible();
  });

  test('should filter members by role', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Filter by admin role
    await page.selectOption('select[name="roleFilter"]', 'admin');
    
    // Should show only admin members
    await expect(page.locator('[data-testid="member-item"][data-role="admin"]')).toBeVisible();
  });

  test('should filter members by status', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Filter by active status
    await page.selectOption('select[name="statusFilter"]', 'active');
    
    // Should show only active members
    await expect(page.locator('[data-testid="member-item"][data-status="active"]')).toBeVisible();
  });

  test('should search team members', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Search for member by name
    await page.fill('input[name="search"]', 'John Doe');
    await page.click('button[data-testid="search-members"]');
    
    // Should show search results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    await expect(page.locator('text=John Doe')).toBeVisible();
  });

  test('should display member activity', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Click on first member
    await page.click('[data-testid="member-item"]');
    
    // Should open member details
    await expect(page.locator('[data-testid="member-details"]')).toBeVisible();
    
    // Check if activity is visible
    await expect(page.locator('[data-testid="member-activity"]')).toBeVisible();
    await expect(page.locator('text=Recent Activity')).toBeVisible();
  });

  test('should display team statistics', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Check if team statistics are visible
    await expect(page.locator('[data-testid="team-stats"]')).toBeVisible();
    await expect(page.locator('text=Total Members')).toBeVisible();
    await expect(page.locator('text=Active Members')).toBeVisible();
    await expect(page.locator('text=Admins')).toBeVisible();
    await expect(page.locator('text=Agents')).toBeVisible();
    await expect(page.locator('text=Viewers')).toBeVisible();
  });

  test('should display role permissions', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Check if role permissions are visible
    await expect(page.locator('[data-testid="role-permissions"]')).toBeVisible();
    await expect(page.locator('text=Role Permissions')).toBeVisible();
    await expect(page.locator('text=Admin')).toBeVisible();
    await expect(page.locator('text=Agent')).toBeVisible();
    await expect(page.locator('text=Viewer')).toBeVisible();
  });

  test('should handle invitation errors', async ({ page }) => {
    // Mock API error
    await page.route('**/api/v1/team/invite', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Invitation service unavailable' })
      });
    });
    
    // Navigate to team management and open invite form
    await page.click('text=Team Management');
    await page.click('button[data-testid="invite-member"]');
    
    // Fill invite details
    await page.fill('input[name="email"]', 'new.member@example.com');
    await page.fill('input[name="name"]', 'New Member');
    await page.selectOption('select[name="role"]', 'agent');
    
    // Send invitation
    await page.click('button[data-testid="send-invitation"]');
    
    // Should show error message
    await expect(page.locator('text=Failed to send invitation')).toBeVisible();
  });

  test('should validate invite form', async ({ page }) => {
    // Navigate to team management and open invite form
    await page.click('text=Team Management');
    await page.click('button[data-testid="invite-member"]');
    
    // Try to send invitation without required fields
    await page.click('button[data-testid="send-invitation"]');
    
    // Should show validation errors
    await expect(page.locator('text=Email is required')).toBeVisible();
    await expect(page.locator('text=Name is required')).toBeVisible();
    await expect(page.locator('text=Role is required')).toBeVisible();
  });

  test('should display pending invitations', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Check if pending invitations are visible
    await expect(page.locator('[data-testid="pending-invitations"]')).toBeVisible();
    await expect(page.locator('text=Pending Invitations')).toBeVisible();
  });

  test('should resend invitation', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Click resend button on pending invitation
    await page.click('[data-testid="pending-invitation"] button[data-testid="resend-invitation"]');
    
    // Should show success message
    await expect(page.locator('text=Invitation resent successfully')).toBeVisible();
  });

  test('should cancel invitation', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Click cancel button on pending invitation
    await page.click('[data-testid="pending-invitation"] button[data-testid="cancel-invitation"]');
    
    // Should show confirmation dialog
    await expect(page.locator('[data-testid="cancel-confirmation"]')).toBeVisible();
    await expect(page.locator('text=Are you sure you want to cancel this invitation?')).toBeVisible();
    
    // Confirm cancellation
    await page.click('button[data-testid="confirm-cancel"]');
    
    // Should show success message
    await expect(page.locator('text=Invitation cancelled successfully')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Check if team management is still usable on mobile
    await expect(page.locator('[data-testid="team-dashboard"]')).toBeVisible();
    await expect(page.locator('[data-testid="team-members-list"]')).toBeVisible();
  });

  test('should display member performance', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Click on first member
    await page.click('[data-testid="member-item"]');
    
    // Should open member details
    await expect(page.locator('[data-testid="member-details"]')).toBeVisible();
    
    // Check if performance metrics are visible
    await expect(page.locator('[data-testid="member-performance"]')).toBeVisible();
    await expect(page.locator('text=Performance Metrics')).toBeVisible();
    await expect(page.locator('text=Properties Listed')).toBeVisible();
    await expect(page.locator('text=Leads Generated')).toBeVisible();
    await expect(page.locator('text=Deals Closed')).toBeVisible();
  });

  test('should display team calendar', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Check if team calendar is visible
    await expect(page.locator('[data-testid="team-calendar"]')).toBeVisible();
    await expect(page.locator('text=Team Calendar')).toBeVisible();
  });

  test('should export team data', async ({ page }) => {
    // Navigate to team management
    await page.click('text=Team Management');
    
    // Click export button
    await page.click('button[data-testid="export-team"]');
    
    // Should show export options
    await expect(page.locator('[data-testid="export-options"]')).toBeVisible();
    await expect(page.locator('text=Export as CSV')).toBeVisible();
    await expect(page.locator('text=Export as Excel')).toBeVisible();
  });
});
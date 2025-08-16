# Leads Management Tests

## Unit Tests (`tests/unit/leads/`)

### Lead Model Tests
```python
# test_lead_model.py
import pytest
from models.lead import Lead

def test_lead_creation():
    """Test lead model creation with all fields"""
    lead_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-0123",
        "property_interest": "3 bed, 2 bath home",
        "budget_range": "$400,000 - $500,000"
    }
    lead = Lead(**lead_data)
    assert lead.name == "John Doe"
    assert lead.email == "john@example.com"

def test_lead_validation():
    """Test lead data validation"""
    with pytest.raises(ValueError):
        Lead(name="", email="invalid-email")

def test_lead_status_updates():
    """Test lead status transitions"""
    lead = Lead(name="Jane Doe", email="jane@example.com", status="new")
    lead.update_status("contacted")
    assert lead.status == "contacted"
```

### Lead Repository Tests
```python
# test_lead_repository.py
def test_lead_save():
    """Test saving lead to database"""
    pass

def test_lead_retrieval():
    """Test retrieving leads with filters"""
    pass

def test_lead_update():
    """Test updating existing lead"""
    pass

def test_lead_search():
    """Test lead search functionality"""
    pass
```

## E2E Tests (`tests/e2e/leads/`)

### Playwright UI Tests
```javascript
// leads-management.spec.ts
test('Create new lead from dashboard', async ({ page }) => {
  await page.goto('/dashboard');
  await page.click('[data-testid="leads-tab"]');
  
  // Open new lead form
  await page.click('[data-testid="new-lead-button"]');
  
  // Fill lead form
  await page.fill('[data-testid="lead-name"]', 'John Doe');
  await page.fill('[data-testid="lead-email"]', 'john@example.com');
  await page.fill('[data-testid="lead-phone"]', '555-0123');
  await page.fill('[data-testid="lead-interest"]', '3BR house');
  
  // Submit form
  await page.click('[data-testid="save-lead"]');
  
  // Verify lead appears in list
  await page.waitForSelector('[data-testid="lead-list"]');
  await expect(page.locator('[data-testid="lead-item"]')).toContainText('John Doe');
});

test('Lead status updates', async ({ page }) => {
  await page.goto('/dashboard');
  await page.click('[data-testid="leads-tab"]');
  
  // Select existing lead
  await page.click('[data-testid="lead-item"]:first-child');
  
  // Update status
  await page.selectOption('[data-testid="status-select"]', 'contacted');
  await page.click('[data-testid="update-status"]');
  
  // Verify status updated
  await expect(page.locator('[data-testid="lead-status"]')).toContainText('contacted');
});

test('Lead search and filtering', async ({ page }) => {
  await page.goto('/dashboard');
  await page.click('[data-testid="leads-tab"]');
  
  // Search for lead
  await page.fill('[data-testid="lead-search"]', 'John');
  await page.click('[data-testid="search-button"]');
  
  // Verify filtered results
  const results = await page.locator('[data-testid="lead-item"]').count();
  expect(results).toBeGreaterThan(0);
});
```

## Integration Tests
- Lead capture from forms
- Email/SMS integration
- CRM data synchronization
- Lead scoring and prioritization

## API Tests
- Lead CRUD operations
- Search and filtering endpoints
- Data validation
- Error handling

## Test Data
- Sample lead profiles
- Various lead sources
- Different property interests
- Status transition scenarios

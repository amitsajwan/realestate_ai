# 🧪 Testing Guidelines

## **📋 Overview**

This document outlines our testing strategy and best practices for the real estate platform.

## **🎯 Testing Philosophy**

### **✅ What TO Test:**
- **Component Behavior** - User interactions, state changes, data flow
- **Business Logic** - Calculations, validations, transformations
- **API Integration** - Data fetching, error handling, loading states
- **User Experience** - Form submissions, navigation, accessibility
- **Edge Cases** - Empty states, error conditions, boundary values

### **❌ What NOT to Test:**
- **CSS Styling** - Colors, fonts, spacing, layout
- **Visual Appearance** - Icons, images, animations
- **Implementation Details** - Internal component structure
- **Third-party Libraries** - Framer Motion, Heroicons, etc.

## **🏗️ Test Structure**

### **1. Unit Tests**
- **Location**: `__tests__/components/ComponentName.test.tsx`
- **Purpose**: Test individual component functionality
- **Focus**: Props, state, user interactions

### **2. Integration Tests**
- **Location**: `__tests__/components/ComponentName.api.test.tsx`
- **Purpose**: Test API integration and data flow
- **Focus**: API calls, error handling, loading states

### **3. Simple Tests**
- **Location**: `__tests__/components/ComponentName.simple.test.tsx`
- **Purpose**: Basic smoke tests for complex components
- **Focus**: Rendering, basic functionality

## **📝 Test Naming Conventions**

### **Test Files:**
```
ComponentName.test.tsx          # Main component tests
ComponentName.api.test.tsx      # API integration tests
ComponentName.simple.test.tsx   # Simple smoke tests
```

### **Test Descriptions:**
```javascript
describe('ComponentName', () => {
  describe('Basic Rendering', () => {
    it('renders without crashing', () => {})
    it('displays correct content', () => {})
  })
  
  describe('User Interactions', () => {
    it('handles button clicks', () => {})
    it('updates form inputs', () => {})
  })
  
  describe('API Integration', () => {
    it('loads data on mount', () => {})
    it('handles API errors', () => {})
  })
})
```

## **🔧 Testing Tools**

### **Core Libraries:**
- **Jest** - Test runner and assertion library
- **React Testing Library** - Component testing utilities
- **User Event** - User interaction simulation
- **MSW** - API mocking (when needed)

### **Mocking Strategy:**
```javascript
// Mock external dependencies
jest.mock('@/lib/crm-api', () => ({
  crmApi: {
    getLeads: jest.fn(),
    createLead: jest.fn(),
  },
}))

// Mock React hooks
jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'user-1', email: 'test@example.com' },
  }),
}))
```

## **📊 Test Coverage Goals**

### **Coverage Thresholds:**
- **Branches**: 70%
- **Functions**: 70%
- **Lines**: 70%
- **Statements**: 70%

### **Excluded from Coverage:**
- CSS files (`*.css`)
- Style directories (`styles/`)
- Type definitions (`*.d.ts`)
- Test files (`*.test.*`)

## **🎨 CSS Testing Policy**

### **❌ DO NOT Test:**
```javascript
// ❌ BAD - Testing CSS classes
expect(element).toHaveClass('bg-blue-500')
expect(element).toHaveStyle('color: red')

// ❌ BAD - Testing visual appearance
expect(element).toHaveStyle('font-size: 16px')
expect(element).toHaveStyle('margin: 10px')
```

### **✅ DO Test:**
```javascript
// ✅ GOOD - Testing functionality
expect(screen.getByText('Submit')).toBeInTheDocument()
expect(screen.getByRole('button')).toBeInTheDocument()

// ✅ GOOD - Testing behavior
await user.click(screen.getByRole('button'))
expect(mockFunction).toHaveBeenCalled()
```

## **🚀 Best Practices**

### **1. Test User Behavior, Not Implementation**
```javascript
// ❌ BAD - Testing implementation
expect(component.state.isLoading).toBe(true)

// ✅ GOOD - Testing user experience
expect(screen.getByText('Loading...')).toBeInTheDocument()
```

### **2. Use Semantic Queries**
```javascript
// ❌ BAD - Testing by CSS class
screen.getByClassName('submit-button')

// ✅ GOOD - Testing by role/label
screen.getByRole('button', { name: 'Submit' })
screen.getByLabelText('Email Address')
```

### **3. Test Error States**
```javascript
it('handles API errors gracefully', async () => {
  mockApi.getData.mockRejectedValue(new Error('API Error'))
  
  render(<Component />)
  
  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument()
  })
})
```

### **4. Test Loading States**
```javascript
it('shows loading state while fetching data', () => {
  mockApi.getData.mockImplementation(() => new Promise(() => {}))
  
  render(<Component />)
  
  expect(screen.getByText(/loading/i)).toBeInTheDocument()
})
```

### **5. Test Accessibility**
```javascript
it('supports keyboard navigation', async () => {
  const user = userEvent.setup()
  
  render(<Component />)
  
  const button = screen.getByRole('button')
  button.focus()
  expect(document.activeElement).toBe(button)
  
  await user.keyboard('{Enter}')
  expect(mockFunction).toHaveBeenCalled()
})
```

## **🔍 Test Categories**

### **1. Rendering Tests**
- Component renders without crashing
- Displays correct content
- Shows loading/error states

### **2. Interaction Tests**
- Button clicks
- Form submissions
- Input changes
- Modal open/close

### **3. Data Tests**
- API data loading
- Data calculations
- State updates
- Error handling

### **4. Navigation Tests**
- Route changes
- Modal navigation
- Tab switching
- Back/forward buttons

### **5. Accessibility Tests**
- ARIA labels
- Keyboard navigation
- Screen reader support
- Focus management

## **📈 Performance Testing**

### **Render Performance:**
```javascript
it('renders efficiently with large dataset', () => {
  const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
    id: i,
    name: `Item ${i}`,
  }))
  
  const startTime = Date.now()
  render(<Component data={largeDataset} />)
  const endTime = Date.now()
  
  expect(endTime - startTime).toBeLessThan(1000)
})
```

### **API Performance:**
```javascript
it('loads data within acceptable time', async () => {
  const startTime = Date.now()
  render(<Component />)
  
  await waitFor(() => {
    expect(screen.getByText('Data loaded')).toBeInTheDocument()
  })
  
  const endTime = Date.now()
  expect(endTime - startTime).toBeLessThan(2000)
})
```

## **🐛 Debugging Tests**

### **Common Issues:**
1. **Async operations** - Use `waitFor()` for async updates
2. **Mock functions** - Clear mocks between tests
3. **DOM queries** - Use semantic queries over CSS selectors
4. **User events** - Use `userEvent` for realistic interactions

### **Debugging Tips:**
```javascript
// Debug DOM structure
screen.debug()

// Debug specific element
screen.debug(screen.getByRole('button'))

// Check if element exists
expect(screen.queryByText('Text')).not.toBeInTheDocument()
```

## **📋 Test Checklist**

### **Before Writing Tests:**
- [ ] Understand component requirements
- [ ] Identify key user interactions
- [ ] Plan test scenarios
- [ ] Set up proper mocks

### **While Writing Tests:**
- [ ] Test happy path scenarios
- [ ] Test error conditions
- [ ] Test edge cases
- [ ] Test accessibility
- [ ] Use semantic queries
- [ ] Avoid testing CSS

### **After Writing Tests:**
- [ ] Run tests locally
- [ ] Check coverage report
- [ ] Review test quality
- [ ] Update documentation

## **🎯 Component-Specific Guidelines**

### **CRM Component:**
- Test lead filtering and search
- Test lead creation and updates
- Test modal interactions
- Test API error handling

### **Analytics Component:**
- Test data calculations
- Test period selection
- Test chart rendering
- Test loading states

### **Team Management Component:**
- Test team member management
- Test invitation flow
- Test role changes
- Test permission handling

## **📚 Resources**

- [React Testing Library Docs](https://testing-library.com/docs/react-testing-library/intro/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [User Event Library](https://testing-library.com/docs/user-event/intro/)
- [Accessibility Testing](https://testing-library.com/docs/guide-accessibility/)

---

**Remember**: Tests should make you confident that your code works correctly, not that it looks pretty! 🎨❌🧪✅
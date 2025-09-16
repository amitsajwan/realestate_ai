# Frontend Library Architecture

## 🏗️ **Modular Architecture Overview**

This frontend library follows a clean, modular architecture similar to the auth module, ensuring proper separation of concerns, no duplicates, and perfect backend/frontend model synchronization.

## 📁 **Module Structure**

### 🔐 **Auth Module** (`/lib/auth/`)
- **Purpose**: User authentication and authorization
- **Files**: `types.ts`, `api.ts`, `manager.ts`, `index.ts`
- **Usage**: `import { authManager, User } from '@/lib/auth'`

### 🏠 **Properties Module** (`/lib/properties/`)
- **Purpose**: Property management and operations
- **Files**: `types.ts`, `api.ts`, `manager.ts`, `index.ts`
- **Usage**: `import { propertiesManager, Property } from '@/lib/properties'`

### 📝 **Posts Module** (`/lib/posts/`)
- **Purpose**: Post creation, management, and publishing
- **Files**: `types.ts`, `api.ts`, `manager.ts`, `index.ts`
- **Usage**: `import { postsManager, Post } from '@/lib/posts'`

### 👤 **Agent Module** (`/lib/agent/`)
- **Purpose**: Agent profiles, websites, and branding
- **Files**: `types.ts`, `api.ts`, `manager.ts`, `index.ts`
- **Usage**: `import { agentManager, Agent } from '@/lib/agent'`

## 🎯 **Key Benefits**

### ✅ **Clean Separation**
- Each module handles its own domain
- No cross-module dependencies
- Clear boundaries and responsibilities

### ✅ **Consistent Patterns**
- All modules follow the same structure
- Standardized API patterns
- Unified error handling

### ✅ **Type Safety**
- Full TypeScript support
- Synchronized backend/frontend models
- Compile-time error checking

### ✅ **State Management**
- Centralized state per module
- Reactive updates with subscribers
- Optimistic updates where appropriate

### ✅ **No Duplicates**
- Single source of truth for each type
- Removed duplicate interfaces
- Consistent field naming (camelCase)

## 🔄 **Migration Guide**

### **From Old API to New Modules**

#### **Properties**
```typescript
// OLD (deprecated)
import { apiService } from '@/lib/api'
const properties = await apiService.getProperties()

// NEW (recommended)
import { propertiesAPI } from '@/lib/properties'
const response = await propertiesAPI.getProperties()
```

#### **Agent Profile**
```typescript
// OLD (deprecated)
import { apiService } from '@/lib/api'
const profile = await apiService.getAgentProfile()

// NEW (recommended)
import { agentAPI } from '@/lib/agent'
const response = await agentAPI.getAgentProfile()
```

#### **Posts**
```typescript
// OLD (deprecated)
import { apiService } from '@/lib/api'
const posts = await apiService.getPosts()

// NEW (recommended)
import { postsAPI } from '@/lib/posts'
const response = await postsAPI.getPosts()
```

## 📋 **Module Usage Examples**

### **Properties Module**
```typescript
import { propertiesManager, Property, PropertyCreate } from '@/lib/properties'

// Load properties
const result = await propertiesManager.loadProperties()

// Create property
const newProperty: PropertyCreate = {
  title: 'Beautiful Home',
  description: 'A lovely property',
  propertyType: 'house',
  price: 500000,
  location: '123 Main St',
  bedrooms: 3,
  bathrooms: 2,
  features: ['garden', 'garage'],
  images: []
}

const createResult = await propertiesManager.createProperty(newProperty)

// Subscribe to state changes
const unsubscribe = propertiesManager.subscribe((state) => {
  console.log('Properties updated:', state.properties)
})
```

### **Posts Module**
```typescript
import { postsManager, Post, PostCreate } from '@/lib/posts'

// Load posts
const result = await postsManager.loadPosts()

// Create post
const newPost: PostCreate = {
  propertyId: 'property-123',
  title: 'New Listing Available!',
  content: 'Check out this amazing property...',
  language: 'en',
  channels: ['facebook', 'instagram'],
  tags: ['real-estate', 'listing']
}

const createResult = await postsManager.createPost(newPost)
```

### **Agent Module**
```typescript
import { agentManager, Agent, AgentCreate } from '@/lib/agent'

// Load agent profile
const result = await agentManager.loadAgentProfile()

// Create agent profile
const newAgent: AgentCreate = {
  name: 'John Doe',
  email: 'john@example.com',
  phone: '+1234567890',
  company: 'Real Estate Co',
  bio: 'Experienced real estate agent',
  isPublic: true
}

const createResult = await agentManager.createAgentProfile(newAgent)
```

## 🚫 **Deprecated Files**

The following files are deprecated and should not be used:

- `frontend/types/property.ts` - Use `@/lib/properties` instead
- `frontend/lib/api.ts` (property/agent methods) - Use specific modules instead

## 🔧 **Development Guidelines**

### **Adding New Features**
1. Determine which module the feature belongs to
2. Add types to the module's `types.ts`
3. Add API methods to the module's `api.ts`
4. Add state management to the module's `manager.ts`
5. Export from the module's `index.ts`

### **Backend Synchronization**
1. Ensure backend models match frontend types
2. Use camelCase for all field names
3. Keep enums synchronized
4. Update API endpoints as needed

### **Error Handling**
- All modules use consistent error handling
- Errors are logged using the logger utility
- State includes error information for UI display

## 🧪 **Testing**

Each module can be tested independently:

```typescript
// Test properties module
import { propertiesManager } from '@/lib/properties'

// Mock the API
jest.mock('@/lib/properties/api')

// Test state management
const result = await propertiesManager.loadProperties()
expect(result.success).toBe(true)
```

## 📈 **Performance**

- Modules use lazy loading where appropriate
- State updates are batched
- Subscribers are automatically cleaned up
- API calls include proper caching headers

## 🔒 **Security**

- All API calls include authentication headers
- Sensitive data is properly handled
- CORS is configured for development and production
- Input validation is performed at the API level

---

This modular architecture ensures maintainable, scalable, and type-safe code while providing a great developer experience.

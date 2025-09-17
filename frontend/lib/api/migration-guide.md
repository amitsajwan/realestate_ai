# API Client Migration Guide

## Overview
This guide helps migrate from the old fragmented API clients to the new unified API client.

## Migration Steps

### 1. Replace Old API Calls

**Before:**
```typescript
import { api } from '@/lib/api';

// Old way
const posts = await api.enhancedPosts.get(filters);
const properties = await api.getProperties();
const user = await api.getCurrentUser();
```

**After:**
```typescript
import { apiClient } from '@/lib/api/unified-client';

// New way
const posts = await apiClient.getPosts(filters);
const properties = await apiClient.getProperties();
const user = await apiClient.getCurrentUser();
```

### 2. Error Handling

**Before:**
```typescript
try {
  const result = await api.enhancedPosts.create(data);
} catch (error) {
  console.error('Error:', error);
}
```

**After:**
```typescript
import { APIError } from '@/lib/api/unified-client';

try {
  const result = await apiClient.createPost(data);
} catch (error) {
  if (error instanceof APIError) {
    console.error('API Error:', error.message, 'Status:', error.status);
  } else {
    console.error('Unexpected error:', error);
  }
}
```

### 3. Type Safety

The unified client provides full TypeScript support with proper types that match the backend schemas.

## API Endpoint Mapping

| Old Endpoint | New Method | Notes |
|-------------|------------|-------|
| `api.enhancedPosts.get()` | `apiClient.getPosts()` | Uses enhanced posts endpoint |
| `api.enhancedPosts.create()` | `apiClient.createPost()` | Full type safety |
| `api.getProperties()` | `apiClient.getProperties()` | Uses unified properties |
| `api.getCurrentUser()` | `apiClient.getCurrentUser()` | Consistent auth handling |
| `api.login()` | `apiClient.login()` | Improved error handling |

## Benefits

1. **Consistent Error Handling**: All API calls use the same error handling pattern
2. **Type Safety**: Full TypeScript support with backend schema matching
3. **Centralized Configuration**: Single place to manage API settings
4. **Better Authentication**: Consistent auth header handling
5. **Easier Testing**: Mock the single client instead of multiple clients

## Deprecation Timeline

- **Phase 1**: New code should use `apiClient`
- **Phase 2**: Migrate existing code to `apiClient`
- **Phase 3**: Remove old API clients (planned for next major version)
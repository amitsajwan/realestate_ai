# API Cleanup Plan - Remove Duplicate/Old AI Endpoints

## 🎯 **Current State Analysis**

### **APIs Currently Used by Frontend:**
1. ✅ `/api/v1/ai-unified/generate-unified` - **NEW UNIFIED ENDPOINT** (UnifiedAIContentGenerator)
2. ❌ `/api/v1/ai/generate` - **OLD** (QuickPostGenerator, PropertyMarketingHub)
3. ❌ `/api/v1/ai-content/generate-content` - **OLD** (AIContentGenerator)
4. ❌ `/api/v1/ai-content/regenerate/{property_id}` - **OLD** (AIContentGenerator)
5. ✅ `/api/v1/ai-content/properties` - **KEEP** (Used by all components for property list)

### **APIs NOT Used by Frontend (Can be removed):**
1. ❌ `/api/v1/unified-ai/generate` - **UNUSED**
2. ❌ `/api/v1/unified-ai/generate-multi` - **UNUSED**
3. ❌ `/api/v1/ai/generate-single` - **UNUSED**
4. ❌ `/api/v1/ai/generate-batch` - **UNUSED**
5. ❌ `/api/v1/ai-content/generate` - **UNUSED**
6. ❌ `/api/v1/quick-posts/property/{property_id}/generate` - **UNUSED**
7. ❌ `/api/v1/properties/{property_id}/ai-suggestions` - **UNUSED**
8. ❌ `/api/v1/social-publishing/generate` - **UNUSED**
9. ❌ `/api/v1/listing-posts/generate` - **UNUSED**
10. ❌ `/api/v1/listing-posts/generate-and-post` - **UNUSED**
11. ❌ `/api/v1/india-market/generate` - **UNUSED**
12. ❌ `/api/v1/india-market/generate-multilingual` - **UNUSED**
13. ❌ `/api/v1/india-market/generate-and-post` - **UNUSED**
14. ❌ `/api/v1/content/generate-test-content` - **UNUSED**

## 🧹 **Cleanup Plan**

### **Phase 1: Update Frontend Components**
1. **Update QuickPostGenerator** - Replace `/api/v1/ai/generate` with `/api/v1/ai-unified/generate-unified`
2. **Update PropertyMarketingHub** - Replace `/api/v1/ai/generate` with `/api/v1/ai-unified/generate-unified`
3. **Update AIContentGenerator** - Replace `/api/v1/ai-content/generate-content` with `/api/v1/ai-unified/generate-unified`
4. **Keep property list endpoint** - `/api/v1/ai-content/properties` (still needed)

### **Phase 2: Remove Unused API Endpoints**
1. **Remove entire files:**
   - `backend/app/api/v1/endpoints/unified_ai_content.py` (replaced by unified_ai_unified.py)
   - `backend/app/api/v1/endpoints/unified_ai_v2.py` (replaced by unified_ai_unified.py)
   - `backend/app/api/v1/endpoints/ai_content_generation.py` (replaced by unified_ai_unified.py)
   - `backend/app/api/v1/endpoints/quick_posts.py` (unused)
   - `backend/app/api/v1/endpoints/listing_posts.py` (unused)
   - `backend/app/api/v1/endpoints/india_market.py` (unused)

2. **Remove specific endpoints from existing files:**
   - Remove `/generate` from `social_publishing.py`
   - Remove `/ai-suggestions` from `unified_properties.py`
   - Remove `/generate-test-content` from `content_library.py`

### **Phase 3: Update Router**
1. **Remove imports** for deleted endpoint files
2. **Remove router includes** for deleted endpoints
3. **Keep only** `/api/v1/ai-unified` and `/api/v1/ai-content/properties`

### **Phase 4: Update Frontend Components**
1. **Replace AIContentGenerator** with UnifiedAIContentGenerator
2. **Update QuickPostGenerator** to use unified endpoint
3. **Update PropertyMarketingHub** to use unified endpoint
4. **Remove old component files** after migration

## 📊 **Benefits After Cleanup**

### **Before Cleanup:**
- 15+ AI-related API endpoints
- 3+ different AI UI components
- Inconsistent response formats
- Multiple code paths for same functionality

### **After Cleanup:**
- 2 AI-related API endpoints (unified + properties list)
- 1 AI UI component (UnifiedAIContentGenerator)
- Consistent response format
- Single code path for all AI content generation

## 🚀 **Implementation Steps**

1. **Update frontend components** to use unified endpoint
2. **Test all functionality** works with unified endpoint
3. **Remove unused API endpoints** and files
4. **Update router** to remove unused routes
5. **Remove old frontend components**
6. **Update documentation**

## ⚠️ **Important Notes**

- **Keep `/api/v1/ai-content/properties`** - Still needed for property list
- **Test thoroughly** before removing endpoints
- **Update any external integrations** that might use old endpoints
- **Maintain backward compatibility** during transition if needed

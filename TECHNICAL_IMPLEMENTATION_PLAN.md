# 🔧 **TECHNICAL IMPLEMENTATION PLAN: Multi-Post Management System**

## 📋 **Implementation Overview**

This document provides a detailed technical implementation plan for the multi-post management system, including code structure, API design, database changes, and integration points.

## 🏗️ **Code Architecture Changes**

### **1. Database Schema Updates**

#### **New Collections**
```python
# PropertyPost Collection
class PropertyPost(BaseModel):
    id: Optional[str] = Field(alias="_id")
    property_id: str
    agent_id: str
    title: str
    content: str
    language: str
    template_id: Optional[str]
    status: PostStatus = PostStatus.DRAFT
    channels: List[str] = []
    scheduled_at: Optional[datetime]
    published_at: Optional[datetime]
    facebook_post_id: Optional[str]
    instagram_post_id: Optional[str]
    linkedin_post_id: Optional[str]
    website_post_id: Optional[str]
    email_campaign_id: Optional[str]
    ai_generated: bool = False
    ai_prompt: Optional[str]
    version: int = 1
    created_at: datetime
    updated_at: datetime
    analytics: Optional[PostAnalytics]

# PostTemplate Collection
class PostTemplate(BaseModel):
    id: Optional[str] = Field(alias="_id")
    name: str
    description: str
    property_type: str
    language: str
    template: str
    variables: List[str] = []
    channels: List[str] = []
    is_active: bool = True
    created_by: str
    created_at: datetime
    updated_at: datetime
```

#### **Existing Collection Updates**
```python
# Update Property schema to include post count
class Property(BaseModel):
    # ... existing fields
    post_count: int = 0
    last_post_created: Optional[datetime]
    last_post_published: Optional[datetime]
```

### **2. API Endpoints Implementation**

#### **Post Management API**
```python
# /backend/app/api/v1/endpoints/posts.py
@router.post("/", response_model=PostResponse)
async def create_post(
    post_data: PostCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new post for a property"""
    pass

@router.get("/", response_model=List[PostResponse])
async def get_posts(
    property_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    status: Optional[PostStatus] = None,
    language: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get posts with optional filters"""
    pass

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific post by ID"""
    pass

@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    post_data: PostUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update an existing post"""
    pass

@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a post"""
    pass
```

#### **Template Management API**
```python
# /backend/app/api/v1/endpoints/templates.py
@router.post("/", response_model=TemplateResponse)
async def create_template(
    template_data: TemplateCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new post template"""
    pass

@router.get("/", response_model=List[TemplateResponse])
async def get_templates(
    property_type: Optional[str] = None,
    language: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    """Get templates with optional filters"""
    pass
```

#### **Publishing API**
```python
# /backend/app/api/v1/endpoints/publishing.py
@router.post("/{post_id}/publish")
async def publish_post(
    post_id: str,
    channels: List[str],
    current_user: User = Depends(get_current_user)
):
    """Publish a post to specified channels"""
    pass

@router.post("/{post_id}/unpublish")
async def unpublish_post(
    post_id: str,
    channels: List[str],
    current_user: User = Depends(get_current_user)
):
    """Unpublish a post from specified channels"""
    pass
```

### **3. Service Layer Implementation**

#### **Post Management Service**
```python
# /backend/app/services/post_management_service.py
class PostManagementService:
    def __init__(self, db: Database, ai_service: AIService):
        self.db = db
        self.ai_service = ai_service
    
    async def create_post(self, post_data: PostCreateRequest) -> PostResponse:
        """Create a new post with AI content generation"""
        # 1. Validate property exists
        # 2. Generate AI content if requested
        # 3. Create post record
        # 4. Update property post count
        # 5. Return post response
        pass
    
    async def get_posts(self, filters: PostFilters) -> List[PostResponse]:
        """Get posts with filters and pagination"""
        # 1. Build MongoDB query from filters
        # 2. Execute query with pagination
        # 3. Return formatted response
        pass
    
    async def update_post(self, post_id: str, updates: PostUpdateRequest) -> PostResponse:
        """Update an existing post"""
        # 1. Validate post exists and user has access
        # 2. Apply updates
        # 3. Increment version
        # 4. Return updated post
        pass
    
    async def delete_post(self, post_id: str) -> bool:
        """Delete a post and update property count"""
        # 1. Validate post exists
        # 2. Delete post
        # 3. Update property post count
        # 4. Return success status
        pass
```

#### **Template Service**
```python
# /backend/app/services/template_service.py
class TemplateService:
    def __init__(self, db: Database):
        self.db = db
    
    async def create_template(self, template_data: TemplateCreateRequest) -> TemplateResponse:
        """Create a new post template"""
        # 1. Validate template data
        # 2. Create template record
        # 3. Return template response
        pass
    
    async def get_templates(self, filters: TemplateFilters) -> List[TemplateResponse]:
        """Get templates with filters"""
        # 1. Build query from filters
        # 2. Execute query
        # 3. Return formatted response
        pass
```

### **4. Frontend Component Implementation**

#### **Post Management Dashboard**
```typescript
// /frontend/components/PostManagement/PostManagementDashboard.tsx
interface PostManagementDashboardProps {
  propertyId?: string;
  agentId?: string;
}

export const PostManagementDashboard: React.FC<PostManagementDashboardProps> = ({
  propertyId,
  agentId
}) => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [filters, setFilters] = useState<PostFilters>({});
  const [loading, setLoading] = useState(false);

  // Component implementation
  return (
    <div className="post-management-dashboard">
      {/* Dashboard content */}
    </div>
  );
};
```

#### **Post Creation Wizard**
```typescript
// /frontend/components/PostManagement/PostCreationWizard.tsx
interface PostCreationWizardProps {
  propertyId: string;
  onPostCreated: (post: Post) => void;
  onCancel: () => void;
}

export const PostCreationWizard: React.FC<PostCreationWizardProps> = ({
  propertyId,
  onPostCreated,
  onCancel
}) => {
  const [step, setStep] = useState(1);
  const [postData, setPostData] = useState<PostCreateRequest>({});
  
  // Wizard implementation
  return (
    <div className="post-creation-wizard">
      {/* Wizard steps */}
    </div>
  );
};
```

#### **Post Editor**
```typescript
// /frontend/components/PostManagement/PostEditor.tsx
interface PostEditorProps {
  post: Post;
  onPostUpdated: (post: Post) => void;
  onCancel: () => void;
}

export const PostEditor: React.FC<PostEditorProps> = ({
  post,
  onPostUpdated,
  onCancel
}) => {
  const [content, setContent] = useState(post.content);
  const [isDirty, setIsDirty] = useState(false);
  
  // Editor implementation
  return (
    <div className="post-editor">
      {/* Editor content */}
    </div>
  );
};
```

### **5. Integration Points**

#### **Enhanced Properties Component**
```typescript
// /frontend/components/Properties.tsx (Enhanced)
export const Properties: React.FC = () => {
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [showPostManagement, setShowPostManagement] = useState(false);

  const handleManagePosts = (property: Property) => {
    setSelectedProperty(property);
    setShowPostManagement(true);
  };

  return (
    <div className="properties-container">
      {/* Existing properties list */}
      {properties.map(property => (
        <PropertyCard
          key={property.id}
          property={property}
          onManagePosts={() => handleManagePosts(property)}
        />
      ))}
      
      {/* Post management modal */}
      {showPostManagement && selectedProperty && (
        <PostManagementModal
          property={selectedProperty}
          onClose={() => setShowPostManagement(false)}
        />
      )}
    </div>
  );
};
```

#### **Enhanced Navigation**
```typescript
// /frontend/components/Navigation.tsx (Enhanced)
export const Navigation: React.FC = () => {
  const [activeSection, setActiveSection] = useState('properties');

  const navigationItems = [
    { id: 'properties', label: 'Properties', icon: '🏠' },
    { id: 'posts', label: 'Post Management', icon: '📝' },
    { id: 'templates', label: 'Templates', icon: '📋' },
    { id: 'analytics', label: 'Analytics', icon: '📊' },
    // ... other items
  ];

  return (
    <nav className="navigation">
      {navigationItems.map(item => (
        <button
          key={item.id}
          className={`nav-item ${activeSection === item.id ? 'active' : ''}`}
          onClick={() => setActiveSection(item.id)}
        >
          <span className="nav-icon">{item.icon}</span>
          <span className="nav-label">{item.label}</span>
        </button>
      ))}
    </nav>
  );
};
```

## 🔄 **Migration Strategy**

### **Phase 1: Database Migration**
```python
# /backend/app/utils/migration.py
async def migrate_to_multi_post():
    """Migrate existing data to support multi-post system"""
    # 1. Create new collections
    # 2. Migrate existing property data
    # 3. Create initial posts from existing properties
    # 4. Update property schemas
    pass
```

### **Phase 2: API Migration**
```python
# /backend/app/api/v1/endpoints/property_publishing.py (Updated)
@router.post("/{property_id}/publish")
async def publish_property(
    property_id: str,
    publish_data: PropertyPublishRequest,
    current_user: User = Depends(get_current_user)
):
    """Legacy endpoint - redirects to new post system"""
    # 1. Create post from property data
    # 2. Publish post
    # 3. Return legacy response format
    pass
```

### **Phase 3: Frontend Migration**
```typescript
// /frontend/lib/api.ts (Enhanced)
export const api = {
  // Existing API calls
  ...existingApi,
  
  // New post management API calls
  posts: {
    create: (postData: PostCreateRequest) => apiCall('POST', '/posts', postData),
    get: (filters?: PostFilters) => apiCall('GET', '/posts', { params: filters }),
    getById: (postId: string) => apiCall('GET', `/posts/${postId}`),
    update: (postId: string, updates: PostUpdateRequest) => apiCall('PUT', `/posts/${postId}`, updates),
    delete: (postId: string) => apiCall('DELETE', `/posts/${postId}`),
    publish: (postId: string, channels: string[]) => apiCall('POST', `/posts/${postId}/publish`, { channels }),
    unpublish: (postId: string, channels: string[]) => apiCall('POST', `/posts/${postId}/unpublish`, { channels }),
  },
  
  templates: {
    create: (templateData: TemplateCreateRequest) => apiCall('POST', '/templates', templateData),
    get: (filters?: TemplateFilters) => apiCall('GET', '/templates', { params: filters }),
    update: (templateId: string, updates: TemplateUpdateRequest) => apiCall('PUT', `/templates/${templateId}`, updates),
    delete: (templateId: string) => apiCall('DELETE', `/templates/${templateId}`),
  }
};
```

## 🧪 **Testing Implementation**

### **Backend Testing**
```python
# /backend/tests/test_post_management.py
class TestPostManagement:
    async def test_create_post(self):
        """Test post creation with AI content generation"""
        pass
    
    async def test_get_posts_with_filters(self):
        """Test post retrieval with various filters"""
        pass
    
    async def test_update_post(self):
        """Test post updates and versioning"""
        pass
    
    async def test_delete_post(self):
        """Test post deletion and property count update"""
        pass
```

### **Frontend Testing**
```typescript
// /frontend/tests/PostManagement.test.tsx
describe('PostManagement', () => {
  test('renders post management dashboard', () => {
    // Test dashboard rendering
  });
  
  test('creates new post successfully', () => {
    // Test post creation flow
  });
  
  test('edits existing post', () => {
    // Test post editing
  });
});
```

## 📊 **Performance Considerations**

### **Database Optimization**
```python
# /backend/app/utils/database_indexes.py
async def create_post_indexes():
    """Create optimized indexes for post queries"""
    await db.property_posts.create_index([("property_id", 1), ("status", 1)])
    await db.property_posts.create_index([("agent_id", 1), ("created_at", -1)])
    await db.property_posts.create_index([("language", 1), ("status", 1)])
    await db.property_posts.create_index([("scheduled_at", 1)])
    await db.post_templates.create_index([("property_type", 1), ("language", 1)])
```

### **Caching Strategy**
```python
# /backend/app/services/cache_service.py
class CacheService:
    async def get_templates(self, filters: TemplateFilters) -> List[TemplateResponse]:
        """Get templates with caching"""
        cache_key = f"templates:{hash(str(filters))}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        templates = await self.template_service.get_templates(filters)
        await self.redis.setex(cache_key, 3600, json.dumps(templates))
        return templates
```

## 🔒 **Security Implementation**

### **Authorization Middleware**
```python
# /backend/app/middleware/authorization.py
async def verify_post_access(post_id: str, user: User) -> bool:
    """Verify user has access to specific post"""
    post = await db.property_posts.find_one({"_id": post_id})
    if not post:
        return False
    
    # Check if user is the post owner or has admin access
    return post["agent_id"] == user.id or user.role == "admin"
```

### **Input Validation**
```python
# /backend/app/schemas/post_schemas.py
class PostCreateRequest(BaseModel):
    property_id: str = Field(..., description="Property ID")
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    language: str = Field(..., regex="^[a-z]{2}$")
    template_id: Optional[str] = None
    channels: List[str] = Field(default=[], max_items=5)
    scheduled_at: Optional[datetime] = None
    ai_generated: bool = False
    ai_prompt: Optional[str] = Field(None, max_length=1000)
```

## 📈 **Monitoring & Analytics**

### **Performance Metrics**
```python
# /backend/app/middleware/metrics.py
async def track_post_metrics(request: Request, call_next):
    """Track performance metrics for post operations"""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Log metrics
    await log_metric("post_api_duration", duration, {
        "endpoint": request.url.path,
        "method": request.method,
        "status_code": response.status_code
    })
    
    return response
```

### **Error Tracking**
```python
# /backend/app/utils/error_tracking.py
async def track_post_errors(error: Exception, context: dict):
    """Track errors in post operations"""
    await log_error("post_operation_error", {
        "error": str(error),
        "context": context,
        "timestamp": datetime.utcnow()
    })
```

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Implementation Status**: Ready for Architect Review
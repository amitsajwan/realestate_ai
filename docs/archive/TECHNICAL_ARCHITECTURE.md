# UnifiedPostingHub - Technical Architecture

## 🏗️ Component Architecture

### Main Component Structure
```
UnifiedPostingHub/
├── index.tsx                    # Main component export
├── UnifiedPostingHub.tsx        # Core component
├── hooks/
│   ├── usePropertySelection.ts  # Property selection logic
│   ├── useContentGeneration.ts  # AI content generation
│   ├── usePublishing.ts         # Publishing workflow
│   └── useDraftManagement.ts    # Draft save/load
├── components/
│   ├── PropertySelector.tsx     # Property selection UI
│   ├── PlatformSelector.tsx     # Platform selection UI
│   ├── ContentPreview.tsx       # Content review/edit
│   ├── PublishingControls.tsx   # Publish/save/schedule
│   └── ProgressIndicator.tsx    # Loading states
├── types/
│   ├── posting.ts              # TypeScript interfaces
│   └── api.ts                  # API response types
└── utils/
    ├── contentTransformers.ts   # Content formatting
    ├── validation.ts            # Input validation
    └── helpers.ts               # Utility functions
```

## 🔧 Technical Implementation Plan

### 1. Core Component (UnifiedPostingHub.tsx)
```typescript
interface UnifiedPostingHubProps {
  mode: 'quick-post' | 'standalone' | 'marketing-hub' | 'property-creation'
  propertyData?: PropertyData
  onContentGenerated?: (content: GeneratedContent[]) => void
  onPublish?: (content: GeneratedContent[], language?: string) => void
  onClose?: () => void
  isOpen?: boolean
  preselectedLanguage?: string
  preselectedPlatforms?: string[]
  preselectedProperty?: string
}
```

### 2. State Management
```typescript
// Main state structure
interface PostingState {
  // Property selection
  selectedProperty: PropertyData | null
  availableProperties: PropertyData[]
  
  // Platform & language
  selectedPlatforms: string[]
  selectedLanguage: string
  
  // Content generation
  customPrompt: string
  generatedContent: GeneratedContent[]
  isGenerating: boolean
  
  // Publishing
  isPublishing: boolean
  publishingStatus: 'idle' | 'publishing' | 'success' | 'error'
  
  // UI state
  currentStep: 1 | 2 | 3  // Configuration → Review → Success
  editingContent: GeneratedContent | null
}
```

### 3. Custom Hooks
```typescript
// usePropertySelection.ts
export const usePropertySelection = () => {
  const [properties, setProperties] = useState<PropertyData[]>([])
  const [selectedProperty, setSelectedProperty] = useState<PropertyData | null>(null)
  
  const loadProperties = async () => {
    const data = await apiService.getProperties()
    setProperties(data.data || [])
  }
  
  return { properties, selectedProperty, setSelectedProperty, loadProperties }
}

// useContentGeneration.ts
export const useContentGeneration = () => {
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent[]>([])
  
  const generateContent = async (params: ContentGenerationParams) => {
    setIsGenerating(true)
    try {
      const result = await apiService.generateAIContent(params)
      // Transform and set content
      setGeneratedContent(transformContent(result))
    } finally {
      setIsGenerating(false)
    }
  }
  
  return { isGenerating, generatedContent, generateContent }
}
```

## 🎨 UI Component Structure

### 1. Step-Based Wizard
```typescript
const renderStep = () => {
  switch (currentStep) {
    case 1:
      return <ConfigurationStep />
    case 2:
      return <ContentReviewStep />
    case 3:
      return <SuccessStep />
  }
}
```

### 2. Responsive Design
```css
/* Mobile-first approach */
.unified-posting-hub {
  @apply w-full max-w-md mx-auto;
}

@media (min-width: 768px) {
  .unified-posting-hub {
    @apply max-w-2xl;
  }
}

@media (min-width: 1024px) {
  .unified-posting-hub {
    @apply max-w-4xl;
  }
}
```

### 3. Animation & Transitions
```typescript
// Framer Motion animations
const stepVariants = {
  enter: { opacity: 0, x: 20 },
  center: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -20 }
}

<AnimatePresence mode="wait">
  <motion.div
    key={currentStep}
    variants={stepVariants}
    initial="enter"
    animate="center"
    exit="exit"
  >
    {renderStep()}
  </motion.div>
</AnimatePresence>
```

## 🔌 API Integration

### 1. Centralized API Client
```typescript
// Already implemented in centralized-client.ts
export class CentralizedAPIClient {
  async generateAIContent(data: any): Promise<any>
  async createPost(postData: any): Promise<any>
  async publishContent(publishData: any): Promise<any>
  async getProperties(): Promise<any>
  async getContent(query?: string): Promise<any>
}
```

### 2. Error Handling
```typescript
const handleApiError = (error: any) => {
  if (error.status === 401) {
    authManager.logout()
    throw new Error('Authentication expired')
  }
  
  const message = error.detail || 'An unexpected error occurred'
  throw new Error(message)
}
```

## 📱 Mobile Optimization

### 1. Touch-Friendly Design
```css
.touch-target {
  min-height: 48px;
  min-width: 48px;
}

.platform-button {
  @apply p-4 rounded-lg border-2 transition-all;
  @apply touch-target;
}

.platform-button.selected {
  @apply border-blue-500 bg-blue-50;
}
```

### 2. Responsive Grid
```css
.platform-grid {
  @apply grid grid-cols-2 gap-3;
}

@media (min-width: 640px) {
  .platform-grid {
    @apply grid-cols-3;
  }
}
```

## 🧪 Testing Strategy

### 1. Unit Tests
```typescript
// Component tests
describe('UnifiedPostingHub', () => {
  it('should render in quick-post mode', () => {
    render(<UnifiedPostingHub mode="quick-post" />)
    expect(screen.getByText('Quick Post Generator')).toBeInTheDocument()
  })
  
  it('should generate content when property is selected', async () => {
    // Test content generation flow
  })
})
```

### 2. Integration Tests
```typescript
// API integration tests
describe('Content Generation', () => {
  it('should call API with correct parameters', async () => {
    const mockApi = jest.fn()
    await generateContent(mockApi, testParams)
    expect(mockApi).toHaveBeenCalledWith(expectedParams)
  })
})
```

## 🚀 Performance Optimization

### 1. Code Splitting
```typescript
// Lazy load heavy components
const ContentPreview = lazy(() => import('./ContentPreview'))
const PublishingControls = lazy(() => import('./PublishingControls'))
```

### 2. Memoization
```typescript
const PlatformSelector = memo(({ platforms, selected, onToggle }) => {
  // Memoized platform selection component
})

const filteredProperties = useMemo(() => {
  return properties.filter(p => p.title.includes(searchTerm))
}, [properties, searchTerm])
```

### 3. Optimistic Updates
```typescript
const handlePublish = async (content: GeneratedContent[]) => {
  // Optimistically update UI
  setPublishingStatus('publishing')
  
  try {
    await apiService.publishContent(content)
    setPublishingStatus('success')
  } catch (error) {
    setPublishingStatus('error')
    // Revert optimistic update
  }
}
```

## 🔒 Security Considerations

### 1. Input Validation
```typescript
const validateContent = (content: string) => {
  if (!content || content.length < 10) {
    throw new Error('Content must be at least 10 characters')
  }
  
  // Sanitize HTML content
  return DOMPurify.sanitize(content)
}
```

### 2. Rate Limiting
```typescript
const useRateLimit = () => {
  const [isRateLimited, setIsRateLimited] = useState(false)
  
  const checkRateLimit = async () => {
    try {
      await apiService.checkRateLimit()
    } catch (error) {
      if (error.status === 429) {
        setIsRateLimited(true)
        setTimeout(() => setIsRateLimited(false), 60000)
      }
    }
  }
  
  return { isRateLimited, checkRateLimit }
}
```

## 📊 Analytics Integration

### 1. Usage Tracking
```typescript
const trackUsage = (action: string, properties?: any) => {
  analytics.track('UnifiedPostingHub', action, {
    mode: currentMode,
    platforms: selectedPlatforms,
    language: selectedLanguage,
    ...properties
  })
}
```

### 2. Performance Metrics
```typescript
const measurePerformance = () => {
  const startTime = performance.now()
  
  return {
    end: () => {
      const duration = performance.now() - startTime
      analytics.track('Performance', 'ContentGeneration', { duration })
    }
  }
}
```
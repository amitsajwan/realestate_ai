# PropertyAI Platform Cleanup Plan
## 🧹 Redundancy Analysis & Removal Strategy

### ✅ SAFE TO REMOVE (Confirmed Redundant)

#### 1. Duplicate Social Publishing Files
- `backend/app/api/v1/endpoints/social_publishing_old.py` - OLD version
- `backend/app/api/v1/endpoints/social_publishing_new.py` - NEW version  
- **KEEP**: `social_publishing.py` (actively used in router)

#### 2. Duplicate Docker Files
- `backend/Dockerfile.dev` - Development version
- `frontend/Dockerfile.dev` - Development version
- `frontend/Dockerfile.frontend` - Duplicate of main Dockerfile
- **KEEP**: Main `Dockerfile` files (used in production)

#### 3. Legacy/Test Files
- `backend/simple_main.py` - Test application
- `frontend/auth.py` - Legacy auth wrapper (just re-exports)
- `backend/test_auth.py` - Standalone test file
- `backend/test_server.py` - Standalone test file

#### 4. Potential Redundant Modules
- `backend/modules/auth/` - Check if this duplicates core auth functionality

### ⚠️ INVESTIGATE BEFORE REMOVING

#### 1. Auth System Analysis
- Compare `backend/modules/auth/` vs `backend/app/core/auth_backend.py`
- Check if both are needed or if one can be removed

#### 2. Frontend Auth Files
- `frontend/auth.ts` vs `frontend/auth.legacy.ts`
- Determine which is actively used

### 🔒 DO NOT REMOVE (Critical Files)
- Main application files (`app/main.py`, `app/layout.tsx`)
- Core services and models
- Production Docker configurations
- Environment templates
- Test suites and documentation

### 📋 Cleanup Steps
1. Remove duplicate social publishing files
2. Remove duplicate Docker files
3. Remove legacy/test files
4. Analyze auth system redundancy
5. Test functionality after each step
6. Update documentation if needed
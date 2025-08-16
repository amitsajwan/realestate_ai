# 📋 DOCUMENTATION & TEST AUDIT PLAN

## 🎯 SYSTEMATIC CLEANUP & TESTING PLAN

### Phase 1: Documentation Audit (5 mins)
1. **Categorize all 130+ documentation files**
2. **Identify outdated/duplicate files**
3. **Create single source of truth documents**

### Phase 2: UI-Documentation Verification (5 mins)
1. **Test dashboard UI features**
2. **Compare with documentation claims**
3. **Update/remove incorrect docs**

### Phase 3: Test Suite Organization (10 mins)
1. **Create structured test directories**
2. **Group tests by functionality**
3. **Set up Playwright UI tests**
4. **Ensure tests catch UI/backend mismatches**

---

## 📁 DOCUMENTATION CATEGORIES FOUND

### ✅ KEEP & UPDATE
- README.md (main project info)
- USER_MANUAL.md (user guide)
- CODEMAP.md (architecture overview)

### 🔄 CONSOLIDATE  
- Multiple Facebook integration docs (15+ files)
- Various production status reports (8+ files)
- Login fix documentation (5+ files)

### ❌ ARCHIVE/REMOVE
- Debug session logs 
- Outdated troubleshooting guides
- Duplicate setup instructions

---

## 🧪 TEST STRUCTURE PLAN

```
tests/
├── unit/
│   ├── facebook/
│   │   ├── test_oauth.py
│   │   ├── test_pages.py  
│   │   └── test_client.py
│   ├── ai/
│   │   ├── test_listing_generation.py
│   │   ├── test_localization.py
│   │   └── test_templates.py
│   ├── leads/
│   │   ├── test_crud.py
│   │   └── test_scoring.py
│   └── properties/
│       ├── test_crud.py
│       └── test_management.py
├── integration/
│   ├── test_facebook_flow.py
│   ├── test_ai_to_facebook.py
│   └── test_end_to_end.py
├── ui/
│   ├── playwright/
│   │   ├── dashboard.spec.js
│   │   ├── facebook.spec.js
│   │   ├── ai_generation.spec.js
│   │   └── leads.spec.js
│   └── test_ui_backend_sync.py
└── smoke/
    └── test_critical_paths.py
```

---

## 🎯 EXECUTION PLAN

Starting systematic cleanup now...

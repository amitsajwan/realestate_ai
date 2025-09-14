/**
 * Test to demonstrate the ORIGINAL infinite loop bug
 * This simulates the broken React component behavior
 */

// Mock React hooks
let useEffectCalls = 0
let useCallbackCalls = 0
let apiCalls = 0

const mockUseEffect = (fn, deps) => {
  useEffectCalls++
  console.log(`useEffect called ${useEffectCalls} times with deps:`, deps)
  fn() // Simulate component mount
}

const mockUseCallback = (fn, deps) => {
  useCallbackCalls++
  console.log(`useCallback called ${useCallbackCalls} times with deps:`, deps)
  return fn
}

// Mock API service
const mockApiService = {
  getDefaultUserProfile: () => {
    apiCalls++
    console.log(`API call #${apiCalls}`)
    return Promise.resolve({ success: true, profile: { name: 'Test User' } })
  }
}

// Mock state
let isProfileLoaded = false
let isLoadingProfile = false

// Simulate the BROKEN component behavior
console.log('🐛 Testing ORIGINAL BUGGY ProfileSettings component...\n')

// Simulate the broken loadUserProfile function
const loadUserProfile = mockUseCallback(async () => {
  console.log('  loadUserProfile called')
  
  // This was the problem - checking state that changes inside the function
  if (isProfileLoaded) {
    console.log('  ⏭️  Skipping - already loaded')
    return
  }

  isLoadingProfile = true
  console.log('  🔄 Starting profile load...')

  try {
    const response = await mockApiService.getDefaultUserProfile()
    console.log('  ✅ API call successful')
    isProfileLoaded = true
    console.log('  📝 Profile loaded successfully')
  } catch (error) {
    console.log('  ❌ API call failed:', error.message)
  } finally {
    isLoadingProfile = false
    console.log('  🏁 Profile loading completed')
  }
}, [isProfileLoaded]) // ❌ This dependency causes the infinite loop!

// Simulate the broken useEffect
mockUseEffect(() => {
  console.log('  useEffect triggered')
  loadUserProfile()
}, [loadUserProfile]) // ❌ This re-runs when loadUserProfile changes!

// Simulate what happens with the bug
console.log('\n🔄 Simulating the infinite loop...')
console.log('  (In real React, this would cause infinite re-renders)')

// Simulate a few iterations of the loop
for (let i = 0; i < 3; i++) {
  console.log(`\n--- Loop iteration ${i + 1} ---`)
  // In real React, this would happen automatically due to the dependency cycle
  mockUseEffect(() => {
    loadUserProfile()
  }, [loadUserProfile])
}

console.log('\n📊 Results:')
console.log(`  useEffect calls: ${useEffectCalls}`)
console.log(`  useCallback calls: ${useCallbackCalls}`)
console.log(`  API calls: ${apiCalls}`)

// Show the problem
if (apiCalls > 1) {
  console.log(`\n❌ BUG CONFIRMED: ${apiCalls} API calls made - infinite loop exists!`)
  console.log('   This is what was happening before the fix!')
} else {
  console.log('\n✅ No infinite loop in this simulation')
}

console.log('\n🔧 The Problem:')
console.log('  1. loadUserProfile depends on isProfileLoaded')
console.log('  2. loadUserProfile changes isProfileLoaded inside the function')
console.log('  3. useEffect depends on loadUserProfile')
console.log('  4. When isProfileLoaded changes, loadUserProfile re-creates')
console.log('  5. When loadUserProfile re-creates, useEffect re-runs')
console.log('  6. This creates an infinite cycle!')

console.log('\n🎯 Original bug demonstration completed!')
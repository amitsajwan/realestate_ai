import { FullConfig } from '@playwright/test'

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting E2E Test Teardown...')
  
  try {
    // Clean up any test data or temporary files
    console.log('📁 Cleaning up test artifacts...')
    
    // Remove any temporary screenshots or videos
    // (Playwright handles this automatically, but we can add custom cleanup here)
    
    console.log('✅ E2E Test Teardown complete')
  } catch (error) {
    console.error('❌ Teardown failed:', error)
    // Don't throw error in teardown to avoid masking test failures
  }
}

export default globalTeardown
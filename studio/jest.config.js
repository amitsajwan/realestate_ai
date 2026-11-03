const nextJest = require('next/jest')

const createJestConfig = nextJest({ dir: './' })

module.exports = createJestConfig({
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  testPathIgnorePatterns: ['<rootDir>/.next/', '<rootDir>/node_modules/'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    // plain TypeScript Studio shares with the site (repo root shared/)
    '^@shared/(.*)$': '<rootDir>/../shared/$1',
  },
  testMatch: ['<rootDir>/__tests__/**/*.{js,jsx,ts,tsx}'],
})

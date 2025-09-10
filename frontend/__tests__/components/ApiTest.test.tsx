import React from 'react';
import { render } from '@testing-library/react';
import { apiService } from '@/lib/api';

// Test if the API service is properly imported
describe('API Test', () => {
  test('apiService is defined', () => {
    expect(apiService).toBeDefined();
    expect(typeof apiService.getAgentProfile).toBe('function');
    expect(typeof apiService.getCurrentUser).toBe('function');
    expect(typeof apiService.createProperty).toBe('function');
    expect(typeof apiService.uploadImages).toBe('function');
    expect(typeof apiService.getAIPropertySuggestions).toBe('function');
  });
});
import { validateEmail, validatePassword, validateName, validatePhone, validateConfirmPassword, validateRequired, sanitizeInput, getFieldError, getFieldErrorClass, propertySchema, PropertyFormData } from '@/lib/validation';
import { describe, it, expect } from '@jest/globals';

describe('Validation Utility Functions', () => {

  describe('validateEmail', () => {
    it('should return valid for a correct email', () => {
      const result = validateEmail('test@example.com');
      expect(result.isValid).toBe(true);
    });

    it('should return invalid for an incorrect email', () => {
      const result = validateEmail('invalid-email');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Please enter a valid email address');
    });
  });

  describe('validatePassword', () => {
    it('should return valid for a strong password', () => {
      const result = validatePassword('Password123!');
      expect(result.isValid).toBe(true);
    });

    it('should return invalid for a weak password', () => {
      const result = validatePassword('weak');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Password must be at least 8 characters long');
    });
  });

  describe('validateName', () => {
    it('should return valid for a correct name', () => {
      const result = validateName('John Doe');
      expect(result.isValid).toBe(true);
    });

    it('should return invalid for a name that is too short', () => {
      const result = validateName('J');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Name must be at least 2 characters long');
    });
  });

  describe('validatePhone', () => {
    it('should return valid for a correct phone number', () => {
      const result = validatePhone('1234567890');
      expect(result.isValid).toBe(true);
    });

    it('should return invalid for a phone number that is too short', () => {
      const result = validatePhone('123');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Phone number must be at least 10 digits');
    });
  });

  describe('validateConfirmPassword', () => {
    it('should return valid if passwords match', () => {
      const result = validateConfirmPassword('password123', 'password123');
      expect(result.isValid).toBe(true);
    });

    it('should return invalid if passwords do not match', () => {
      const result = validateConfirmPassword('password123', 'wrongpassword');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Passwords do not match');
    });
  });

  describe('validateRequired', () => {
    it('should return valid if value is present', () => {
      const result = validateRequired('some value', 'Field');
      expect(result.isValid).toBe(true);
    });

    it('should return invalid if value is empty', () => {
      const result = validateRequired('', 'Field');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Field is required');
    });
  });

  describe('sanitizeInput', () => {
    it('should sanitize HTML characters', () => {
      const input = '<script>alert("xss")</script>';
      const sanitized = sanitizeInput(input);
      expect(sanitized).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;&#x2F;script&gt;');
    });
  });

  describe('getFieldError', () => {
    it('should return the error message for a field', () => {
      const errors = { name: { message: 'Name is required' } };
      const message = getFieldError(errors, 'name');
      expect(message).toBe('Name is required');
    });
  });

  describe('getFieldErrorClass', () => {
    it('should return the error class if field has an error', () => {
      const errors = { name: { message: 'Name is required' } };
      const className = getFieldErrorClass(errors, 'name');
      expect(className).toBe('border-red-500');
    });

    it('should return an empty string if field has no error', () => {
      const errors = {};
      const className = getFieldErrorClass(errors, 'name');
      expect(className).toBe('');
    });
  });

});

describe('Property Schema Validation - ZodError Coverage', () => {

  describe('bedrooms and bathrooms number validation', () => {
    it('should validate successfully with numeric bedrooms and bathrooms', () => {
      const validData: PropertyFormData = {
        title: 'Test Property',
        description: 'Test Description',
        location: 'Test Location',
        address: 'Test Address',
        area: 1000,
        price: '$100,000',
        bedrooms: 2,
        bathrooms: 1,
        amenities: 'Test amenities',
        status: 'available',
        propertyType: 'apartment'
      };

      const result = propertySchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    it('should successfully coerce string bedrooms to numbers', () => {
      const stringData = {
        title: 'Test Property',
        description: 'Test Description',
        location: 'Test Location',
        address: 'Test Address',
        area: 1000,
        price: '$100,000',
        bedrooms: '2', // String that should be coerced to number
        bathrooms: 1,
        amenities: 'Test amenities',
        status: 'available',
        propertyType: 'apartment'
      };

      const result = propertySchema.safeParse(stringData);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.bedrooms).toBe(2); // Should be converted to number
        expect(typeof result.data.bedrooms).toBe('number');
      }
    });

    it('should successfully coerce string bathrooms to numbers', () => {
      const stringData = {
        title: 'Test Property',
        description: 'Test Description',
        location: 'Test Location',
        address: 'Test Address',
        area: 1000,
        price: '$100,000',
        bedrooms: 2,
        bathrooms: '1', // String that should be coerced to number
        amenities: 'Test amenities',
        status: 'available',
        propertyType: 'apartment'
      };

      const result = propertySchema.safeParse(stringData);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.bathrooms).toBe(1); // Should be converted to number
        expect(typeof result.data.bathrooms).toBe('number');
      }
    });

    it('should successfully coerce both bedrooms and bathrooms strings to numbers', () => {
      const stringData = {
        title: 'Test Property',
        description: 'Test Description',
        location: 'Test Location',
        address: 'Test Address',
        area: 1000,
        price: '$100,000',
        bedrooms: '2', // String that should be coerced to number
        bathrooms: '1', // String that should be coerced to number
        amenities: 'Test amenities',
        status: 'available',
        propertyType: 'apartment'
      };

      const result = propertySchema.safeParse(stringData);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.bedrooms).toBe(2);
        expect(result.data.bathrooms).toBe(1);
        expect(typeof result.data.bedrooms).toBe('number');
        expect(typeof result.data.bathrooms).toBe('number');
      }
    });

    it('should successfully coerce string area to numbers', () => {
      const stringData = {
        title: 'Test Property',
        description: 'Test Description',
        location: 'Test Location',
        address: 'Test Address',
        area: '1000', // String that should be coerced to number
        price: '$100,000',
        bedrooms: 2,
        bathrooms: 1,
        amenities: 'Test amenities',
        status: 'available',
        propertyType: 'apartment'
      };

      const result = propertySchema.safeParse(stringData);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.area).toBe(1000); // Should be converted to number
        expect(typeof result.data.area).toBe('number');
      }
    });
  });

  describe('required field validation', () => {
    it('should fail validation when bedrooms is missing', () => {
      const invalidData = {
        title: 'Test Property',
        description: 'Test Description',
        location: 'Test Location',
        address: 'Test Address',
        area: 1000,
        price: '$100,000',
        // bedrooms is missing
        bathrooms: 1,
        amenities: 'Test amenities',
        status: 'available',
        propertyType: 'apartment'
      };

      const result = propertySchema.safeParse(invalidData);
      expect(result.success).toBe(false);
      if (!result.success) {
        const bedroomsError = result.error.issues.find((error: any) => error.path.includes('bedrooms'));
        expect(bedroomsError).toBeDefined();
        expect(bedroomsError?.code).toBe('invalid_type');
      }
    });

    it('should fail validation when bathrooms is missing', () => {
      const invalidData = {
        title: 'Test Property',
        description: 'Test Description',
        location: 'Test Location',
        address: 'Test Address',
        area: 1000,
        price: '$100,000',
        bedrooms: 2,
        // bathrooms is missing
        amenities: 'Test amenities',
        status: 'available',
        propertyType: 'apartment'
      };

      const result = propertySchema.safeParse(invalidData);
      expect(result.success).toBe(false);
      if (!result.success) {
        const bathroomsError = result.error.issues.find((error: any) => error.path.includes('bathrooms'));
        expect(bathroomsError).toBeDefined();
        expect(bathroomsError?.code).toBe('invalid_type');
      }
    });

    it('should fail validation when area is missing', () => {
      const invalidData = {
        title: 'Test Property',
        description: 'Test Description',
        location: 'Test Location',
        address: 'Test Address',
        // area is missing
        price: '$100,000',
        bedrooms: 2,
        bathrooms: 1,
        amenities: 'Test amenities',
        status: 'available',
        propertyType: 'apartment'
      };

      const result = propertySchema.safeParse(invalidData);
      expect(result.success).toBe(false);
      if (!result.success) {
        const areaError = result.error.issues.find((error: any) => error.path.includes('area'));
        expect(areaError).toBeDefined();
        expect(areaError?.code).toBe('invalid_type');
      }
    });

    it('should handle empty string coercion for bedrooms (converts to 0)', () => {
      const dataWithEmptyString = {
        title: 'Test Property',
        description: 'Test Description',
        location: 'Test Location',
        address: 'Test Address',
        area: 1000,
        price: '$100,000',
        bedrooms: '', // Empty string - z.coerce.number() converts to 0
        bathrooms: 1,
        amenities: 'Test amenities',
        status: 'available',
        propertyType: 'apartment'
      };

      const result = propertySchema.safeParse(dataWithEmptyString);
      expect(result.success).toBe(false); // Should fail because 0 < min(1)
      if (!result.success) {
        const bedroomsError = result.error.issues.find((error: any) => error.path.includes('bedrooms'));
        expect(bedroomsError).toBeDefined();
        expect(bedroomsError?.code).toBe('too_small');
      }
    });
  });

  describe('minimum value validation', () => {
    it('should fail validation when bedrooms is less than 1', () => {
      const invalidData: PropertyFormData = {
        title: 'Test Property',
        description: 'Test Description',
        location: 'Test Location',
        address: 'Test Address',
        area: 1000,
        price: '$100,000',
        bedrooms: 0, // Less than minimum
        bathrooms: 1,
        amenities: 'Test amenities',
        status: 'available',
        propertyType: 'apartment'
      };

      const result = propertySchema.safeParse(invalidData);
      expect(result.success).toBe(false);
      if (!result.success) {
        const bedroomsError = result.error.issues.find((error: any) => error.path.includes('bedrooms'));
        expect(bedroomsError).toBeDefined();
        expect(bedroomsError?.code).toBe('too_small');
      }
    });

    it('should fail validation when bathrooms is less than 1', () => {
      const invalidData: PropertyFormData = {
        title: 'Test Property',
        description: 'Test Description',
        location: 'Test Location',
        address: 'Test Address',
        area: 1000,
        price: '$100,000',
        bedrooms: 2,
        bathrooms: 0, // Less than minimum
        amenities: 'Test amenities',
        status: 'available',
        propertyType: 'apartment'
      };

      const result = propertySchema.safeParse(invalidData);
      expect(result.success).toBe(false);
      if (!result.success) {
        const bathroomsError = result.error.issues.find((error: any) => error.path.includes('bathrooms'));
        expect(bathroomsError).toBeDefined();
        expect(bathroomsError?.code).toBe('too_small');
      }
    });

    it('should fail validation when area is less than 1', () => {
      const invalidData: PropertyFormData = {
        title: 'Test Property',
        description: 'Test Description',
        location: 'Test Location',
        address: 'Test Address',
        area: 0, // Less than minimum
        price: '$100,000',
        bedrooms: 2,
        bathrooms: 1,
        amenities: 'Test amenities',
        status: 'available',
        propertyType: 'apartment'
      };

      const result = propertySchema.safeParse(invalidData);
      expect(result.success).toBe(false);
      if (!result.success) {
        const areaError = result.error.issues.find((error: any) => error.path.includes('area'));
        expect(areaError).toBeDefined();
        expect(areaError?.code).toBe('too_small');
      }
    });
  });
});
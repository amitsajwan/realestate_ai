import {
  validateField,
  validateForm,
  validateOnboardingStep,
  calculatePasswordStrength,
  useFormValidation,
  FormValidator,
  loginSchema,
  registerSchema,
  profileSchema,
  onboardingStepSchemas,
  brandingSuggestionSchema,
  profileSettingsSchema,
  validateEmail,
  validatePassword,
  validateName,
  validatePhone,
  validateCompanyName,
  validateBusinessType,
  validateTargetAudience
} from '../../lib/form-validation'
import { z } from 'zod'

describe('Form Validation', () => {
  describe('Individual Field Validators', () => {
    describe('validateEmail', () => {
      it('should validate correct email addresses', () => {
        const validEmails = [
          'test@example.com',
          'user.name@domain.co.uk',
          'user+tag@example.org',
          'user123@test-domain.com'
        ]

        validEmails.forEach(email => {
          const result = validateEmail(email)
          expect(result.isValid).toBe(true)
          expect(result.error).toBeUndefined()
        })
      })

      it('should reject invalid email addresses', () => {
        const invalidEmails = [
          'invalid-email',
          '@domain.com',
          'user@',
          'user..name@domain.com',
          'user@domain',
          ''
        ]

        invalidEmails.forEach(email => {
          const result = validateEmail(email)
          expect(result.isValid).toBe(false)
          expect(result.error).toBe('Please enter a valid email address')
        })
      })
    })

    describe('validatePassword', () => {
      it('should validate strong passwords', () => {
        const validPasswords = [
          'StrongP@ss1',
          'MySecure123!',
          'Complex#Pass9'
        ]

        validPasswords.forEach(password => {
          const result = validatePassword(password)
          expect(result.isValid).toBe(true)
          expect(result.error).toBeUndefined()
        })
      })

      it('should reject passwords that are too short', () => {
        const result = validatePassword('Short1!')
        expect(result.isValid).toBe(false)
        expect(result.error).toBe('Password must be at least 8 characters')
      })

      it('should reject passwords without lowercase letters', () => {
        const result = validatePassword('PASSWORD123!')
        expect(result.isValid).toBe(false)
        expect(result.error).toBe('Password must contain at least one lowercase letter')
      })

      it('should reject passwords without uppercase letters', () => {
        const result = validatePassword('password123!')
        expect(result.isValid).toBe(false)
        expect(result.error).toBe('Password must contain at least one uppercase letter')
      })

      it('should reject passwords without numbers', () => {
        const result = validatePassword('Password!')
        expect(result.isValid).toBe(false)
        expect(result.error).toBe('Password must contain at least one number')
      })

      it('should reject passwords without special characters', () => {
        const result = validatePassword('Password123')
        expect(result.isValid).toBe(false)
        expect(result.error).toBe('Password must contain at least one special character')
      })
    })

    describe('validateName', () => {
      it('should validate correct names', () => {
        const validNames = [
          'John',
          'Mary Jane',
          "O'Connor",
          'Jean-Pierre',
          'Smith Jr'
        ]

        validNames.forEach(name => {
          const result = validateName(name)
          expect(result.isValid).toBe(true)
          expect(result.error).toBeUndefined()
        })
      })

      it('should reject names that are too short', () => {
        const result = validateName('A')
        expect(result.isValid).toBe(false)
        expect(result.error).toBe('Name must be at least 2 characters')
      })

      it('should reject names that are too long', () => {
        const longName = 'A'.repeat(51)
        const result = validateName(longName)
        expect(result.isValid).toBe(false)
        expect(result.error).toBe('Name must be less than 50 characters')
      })

      it('should reject names with invalid characters', () => {
        const invalidNames = ['John123', 'Mary@Jane', 'Test#Name']

        invalidNames.forEach(name => {
          const result = validateName(name)
          expect(result.isValid).toBe(false)
          expect(result.error).toBe('Name can only contain letters, spaces, hyphens, and apostrophes')
        })
      })
    })

    describe('validatePhone', () => {
      it('should validate correct phone numbers', () => {
        const validPhones = [
          '+1234567890',
          '1234567890',
          '+919876543210',
          '9876543210'
        ]

        validPhones.forEach(phone => {
          const result = validatePhone(phone)
          expect(result.isValid).toBe(true)
          expect(result.error).toBeUndefined()
        })
      })

      it('should reject invalid phone numbers', () => {
        const invalidPhones = [
          '123',
          '+0123456789',
          'abc123',
          '++1234567890'
        ]

        invalidPhones.forEach(phone => {
          const result = validatePhone(phone)
          expect(result.isValid).toBe(false)
          expect(result.error).toBe('Please enter a valid phone number')
        })
      })
    })

    describe('validateCompanyName', () => {
      it('should validate correct company names', () => {
        const validNames = [
          'ABC Corp',
          'Tech Solutions Inc.',
          'Real Estate Pro'
        ]

        validNames.forEach(name => {
          const result = validateCompanyName(name)
          expect(result.isValid).toBe(true)
          expect(result.error).toBeUndefined()
        })
      })

      it('should reject company names that are too short or too long', () => {
        const shortName = 'A'
        const longName = 'A'.repeat(101)

        expect(validateCompanyName(shortName).isValid).toBe(false)
        expect(validateCompanyName(longName).isValid).toBe(false)
      })
    })

    describe('validateBusinessType', () => {
      it('should validate correct business types', () => {
        const validTypes = [
          'Real Estate',
          'Technology',
          'Healthcare'
        ]

        validTypes.forEach(type => {
          const result = validateBusinessType(type)
          expect(result.isValid).toBe(true)
          expect(result.error).toBeUndefined()
        })
      })

      it('should reject business types that are too short or too long', () => {
        const shortType = 'A'
        const longType = 'A'.repeat(51)

        expect(validateBusinessType(shortType).isValid).toBe(false)
        expect(validateBusinessType(longType).isValid).toBe(false)
      })
    })

    describe('validateTargetAudience', () => {
      it('should validate correct target audience descriptions', () => {
        const validDescriptions = [
          'First-time home buyers',
          'Luxury property investors and high-net-worth individuals'
        ]

        validDescriptions.forEach(description => {
          const result = validateTargetAudience(description)
          expect(result.isValid).toBe(true)
          expect(result.error).toBeUndefined()
        })
      })

      it('should reject descriptions that are too short or too long', () => {
        const shortDescription = 'Buy'
        const longDescription = 'A'.repeat(201)

        expect(validateTargetAudience(shortDescription).isValid).toBe(false)
        expect(validateTargetAudience(longDescription).isValid).toBe(false)
      })
    })
  })

  describe('Schema Validation', () => {
    describe('loginSchema', () => {
      it('should validate correct login data', () => {
        const validData = {
          email: 'test@example.com',
          password: 'password123'
        }

        const result = validateForm(loginSchema, validData)
        expect(result.isValid).toBe(true)
        expect(result.errors).toEqual({})
      })

      it('should reject invalid login data', () => {
        const invalidData = {
          email: 'invalid-email',
          password: ''
        }

        const result = validateForm(loginSchema, invalidData)
        expect(result.isValid).toBe(false)
        expect(result.errors.email).toBe('Please enter a valid email address')
        expect(result.errors.password).toBe('Password is required')
      })
    })

    describe('registerSchema', () => {
      it('should validate correct registration data', () => {
        const validData = {
          email: 'test@example.com',
          password: 'StrongP@ss1',
          firstName: 'John',
          lastName: 'Doe',
          phone: '+1234567890',
          confirmPassword: 'StrongP@ss1'
        }

        const result = validateForm(registerSchema, validData)
        expect(result.isValid).toBe(true)
        expect(result.errors).toEqual({})
      })

      it('should reject mismatched passwords', () => {
        const invalidData = {
          email: 'test@example.com',
          password: 'StrongP@ss1',
          firstName: 'John',
          lastName: 'Doe',
          phone: '+1234567890',
          confirmPassword: 'DifferentP@ss1'
        }

        const result = validateForm(registerSchema, invalidData)
        expect(result.isValid).toBe(false)
        expect(result.errors.confirmPassword).toBe('Passwords do not match')
      })

      it('should allow empty phone number', () => {
        const validData = {
          email: 'test@example.com',
          password: 'StrongP@ss1',
          firstName: 'John',
          lastName: 'Doe',
          phone: '',
          confirmPassword: 'StrongP@ss1'
        }

        const result = validateForm(registerSchema, validData)
        expect(result.isValid).toBe(true)
      })
    })

    describe('profileSchema', () => {
      it('should validate correct profile data', () => {
        const validData = {
          firstName: 'John',
          lastName: 'Doe',
          email: 'john@example.com',
          companyName: 'Real Estate Pro',
          businessType: 'Real Estate',
          targetAudience: 'First-time home buyers'
        }

        const result = validateForm(profileSchema, validData)
        expect(result.isValid).toBe(true)
        expect(result.errors).toEqual({})
      })

      it('should allow optional fields to be undefined', () => {
        const validData = {
          firstName: 'John',
          lastName: 'Doe',
          email: 'john@example.com'
        }

        const result = validateForm(profileSchema, validData)
        expect(result.isValid).toBe(true)
      })
    })

    describe('profileSettingsSchema', () => {
      it('should validate correct profile settings data', () => {
        const validData = {
          name: 'John Doe',
          email: 'john@example.com',
          phone: '+1234567890',
          whatsapp: '+1234567890',
          company: 'Real Estate Pro',
          experience_years: '5',
          specialization_areas: 'Residential',
          tagline: 'Your trusted real estate partner',
          social_bio: 'Experienced real estate agent',
          about: 'I help clients find their dream homes',
          address: '123 Main St',
          city: 'New York',
          state: 'NY',
          pincode: '123456',
          languages: ['English', 'Spanish']
        }

        const result = validateForm(profileSettingsSchema, validData)
        expect(result.isValid).toBe(true)
        expect(result.errors).toEqual({})
      })

      it('should reject invalid pincode', () => {
        const invalidData = {
          name: 'John Doe',
          email: 'john@example.com',
          pincode: '12345' // Only 5 digits
        }

        const result = validateForm(profileSettingsSchema, invalidData)
        expect(result.isValid).toBe(false)
        expect(result.errors.pincode).toBe('Pincode must be 6 digits')
      })

      it('should allow empty pincode', () => {
        const validData = {
          name: 'John Doe',
          email: 'john@example.com',
          pincode: ''
        }

        const result = validateForm(profileSettingsSchema, validData)
        expect(result.isValid).toBe(true)
      })
    })
  })

  describe('validateOnboardingStep', () => {
    it('should validate step 1 data', () => {
      const validData = {
        firstName: 'John',
        lastName: 'Doe',
        email: 'john@example.com'
      }

      const result = validateOnboardingStep(1, validData)
      expect(result.isValid).toBe(true)
      expect(result.errors).toEqual({})
    })

    it('should validate step 2 data', () => {
      const validData = {
        companyName: 'Real Estate Pro',
        businessType: 'Real Estate'
      }

      const result = validateOnboardingStep(2, validData)
      expect(result.isValid).toBe(true)
      expect(result.errors).toEqual({})
    })

    it('should validate step 3 data', () => {
      const validData = {
        targetAudience: 'First-time home buyers'
      }

      const result = validateOnboardingStep(3, validData)
      expect(result.isValid).toBe(true)
      expect(result.errors).toEqual({})
    })

    it('should return valid for steps without validation', () => {
      const result = validateOnboardingStep(4, {})
      expect(result.isValid).toBe(true)
      expect(result.errors).toEqual({})
    })

    it('should return valid for invalid step numbers', () => {
      const result = validateOnboardingStep(99, {})
      expect(result.isValid).toBe(true)
      expect(result.errors).toEqual({})
    })
  })

  describe('calculatePasswordStrength', () => {
    it('should calculate very weak password strength', () => {
      const result = calculatePasswordStrength('')
      expect(result.score).toBe(0)
      expect(result.label).toBe('Very Weak')
      expect(result.color).toBe('bg-gray-200')
      expect(result.feedback).toContain('At least 8 characters')
    })

    it('should calculate weak password strength', () => {
      const result = calculatePasswordStrength('password')
      expect(result.score).toBe(1)
      expect(result.label).toBe('Weak')
      expect(result.color).toBe('bg-red-500')
    })

    it('should calculate fair password strength', () => {
      const result = calculatePasswordStrength('Password')
      expect(result.score).toBe(2)
      expect(result.label).toBe('Fair')
      expect(result.color).toBe('bg-orange-500')
    })

    it('should calculate good password strength', () => {
      const result = calculatePasswordStrength('Password1')
      expect(result.score).toBe(3)
      expect(result.label).toBe('Good')
      expect(result.color).toBe('bg-yellow-500')
    })

    it('should calculate strong password strength', () => {
      const result = calculatePasswordStrength('Password1!')
      expect(result.score).toBe(4)
      expect(result.label).toBe('Strong')
      expect(result.color).toBe('bg-green-500')
    })

    it('should calculate very strong password strength', () => {
      const result = calculatePasswordStrength('StrongP@ss1')
      expect(result.score).toBe(5)
      expect(result.label).toBe('Very Strong')
      expect(result.color).toBe('bg-green-600')
      expect(result.feedback).toEqual([])
    })
  })

  describe('useFormValidation', () => {
    it('should validate individual fields', () => {
      const { validateField } = useFormValidation(loginSchema)
      
      const validResult = validateField('email', 'test@example.com')
      expect(validResult.isValid).toBe(true)
      
      const invalidResult = validateField('email', 'invalid-email')
      expect(invalidResult.isValid).toBe(false)
      expect(invalidResult.error).toBe('Please enter a valid email address')
    })

    it('should validate entire form', () => {
      const { validateForm: hookValidateForm } = useFormValidation(loginSchema)
      
      const validData = {
        email: 'test@example.com',
        password: 'password123'
      }
      
      const result = hookValidateForm(validData)
      expect(result.isValid).toBe(true)
      expect(result.errors).toEqual({})
    })
  })

  describe('FormValidator Class', () => {
    let validator: FormValidator

    beforeEach(() => {
      validator = new FormValidator(registerSchema)
    })

    it('should validate individual fields', () => {
      const isValid = validator.validateField('email', 'test@example.com')
      expect(isValid).toBe(true)
      expect(validator.getFieldError('email')).toBeUndefined()
    })

    it('should track field errors', () => {
      const isValid = validator.validateField('email', 'invalid-email')
      expect(isValid).toBe(false)
      expect(validator.getFieldError('email')).toBe('Please enter a valid email address')
      expect(validator.hasFieldError('email')).toBe(true)
    })

    it('should validate all fields', () => {
      const data = {
        email: 'test@example.com',
        password: 'password123'
      }
      
      const isValid = validator.validateAll(data)
      expect(isValid).toBe(true)
      expect(validator.getErrors()).toEqual({})
    })

    it('should track touched fields', () => {
      validator.validateField('email', 'test@example.com')
      expect(validator.isTouched('email')).toBe(true)
      expect(validator.isTouched('password')).toBe(false)
    })

    it('should reset validation state', () => {
      validator.validateField('email', 'invalid-email')
      expect(validator.hasFieldError('email')).toBe(true)
      
      validator.reset()
      expect(validator.hasFieldError('email')).toBe(false)
      expect(validator.isTouched('email')).toBe(false)
    })

    it('should manually touch fields', () => {
      validator.touch('email')
      expect(validator.isTouched('email')).toBe(true)
    })

    it('should check if field is valid', () => {
      validator.validateField('email', 'test@example.com')
      expect(validator.isFieldValid('email')).toBe(true)
      
      validator.validateField('password', '')
      expect(validator.isFieldValid('password')).toBe(false)
    })

    it('should handle invalid data types in validateAll', () => {
      const isValid = validator.validateAll(null)
      expect(isValid).toBe(false)
    })

    it('should handle fields not in schema', () => {
      const isValid = validator.validateField('nonexistentField', 'value')
      expect(isValid).toBe(false)
      expect(validator.getFieldError('nonexistentField')).toBe('Field not defined in schema')
    })

    it('should return all errors', () => {
        validator.validateField('email', 'invalid');
        validator.validateField('password', 'short');
        const errors = validator.getErrors();
        expect(errors.email).toBeDefined();
        expect(errors.password).toBeDefined();
    });

    it('should check hasFieldError correctly', () => {
        validator.validateField('email', 'invalid');
        expect(validator.hasFieldError('email')).toBe(true);
        expect(validator.hasFieldError('password')).toBe(false);
    });

  })

  describe('validateField helper', () => {
    it('should validate with custom schema', () => {
      const customSchema = z.string().min(5, 'Must be at least 5 characters')
      
      const validResult = validateField(customSchema, 'hello world')
      expect(validResult.isValid).toBe(true)
      
      const invalidResult = validateField(customSchema, 'hi')
      expect(invalidResult.isValid).toBe(false)
      expect(invalidResult.error).toBe('Must be at least 5 characters')
    })

    it('should handle validation errors gracefully', () => {
      const customSchema = z.string()
      
      const result = validateField(customSchema, 123 as any)
      expect(result.isValid).toBe(false)
      expect(result.error).toBeDefined()
    })
  })

  describe('validateForm helper', () => {
    it('should validate with custom schema', () => {
      const customSchema = z.object({
        name: z.string().min(2),
        age: z.number().min(0)
      })
      
      const validData = { name: 'John', age: 25 }
      const validResult = validateForm(customSchema, validData)
      expect(validResult.isValid).toBe(true)
      
      const invalidData = { name: 'J', age: -1 }
      const invalidResult = validateForm(customSchema, invalidData)
      expect(invalidResult.isValid).toBe(false)
      expect(invalidResult.errors).toBeDefined()
    })

    it('should handle non-zod errors', () => {
      const mockSchema = {
        parse: jest.fn().mockImplementation(() => {
          throw new Error('Non-zod error')
        })
      } as any
      
      const result = validateForm(mockSchema, {})
      expect(result.isValid).toBe(false)
      expect(result.errors.general).toBe('Validation failed')
    })
  })
})
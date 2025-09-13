'use client';

import { LoadingButton } from '@/components/LoadingStates';
import { useFormSubmission } from '@/hooks/useLoading';
import { calculatePasswordStrength, FormValidator, PasswordStrength, registerSchema } from '@/lib/form-validation';
import { LoginFormData } from '@/types/user';
import { CheckCircle, Eye, EyeOff, Lock, Mail, Phone, User, XCircle } from 'lucide-react';
import React, { useEffect, useState } from 'react';

interface RegisterFormProps {
    onSubmit: (data: any) => Promise<void>;
    onSwitchToLogin: () => void;
    isLoading?: boolean;
}

const RegisterForm: React.FC<RegisterFormProps> = ({ onSubmit, onSwitchToLogin, isLoading = false }) => {
    const [formData, setFormData] = useState<LoginFormData>({
        email: '',
        password: '',
        firstName: '',
        lastName: '',
        phone: '',
        confirmPassword: ''
    });
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [passwordStrength, setPasswordStrength] = useState<PasswordStrength>({
        score: 0,
        feedback: [],
        color: 'bg-gray-200',
        label: 'Very Weak'
    });
    const [validator] = useState(() => new FormValidator(registerSchema));
    const { submit } = useFormSubmission();

    // Update password strength when password changes
    useEffect(() => {
        if (formData.password) {
            const strength = calculatePasswordStrength(formData.password);
            setPasswordStrength(strength);
        } else {
            setPasswordStrength({
                score: 0,
                feedback: [],
                color: 'bg-gray-200',
                label: 'Very Weak'
            });
        }
    }, [formData.password]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));

        if (validator.isTouched(name)) {
            validator.validateField(name, value);
        }
    };

    const handleBlur = (field: string) => {
        validator.touch(field);
        validator.validateField(field, formData[field as keyof LoginFormData]);
    };

    const getFieldValidationIcon = (field: keyof LoginFormData) => {
        if (!validator.isTouched(field) || !formData[field]) return null;

        const hasError = validator.hasFieldError(field);
        return hasError ?
            <XCircle className="w-5 h-5 text-red-500" /> :
            <CheckCircle className="w-5 h-5 text-green-500" />;
    };

    const getFieldClassName = (field: keyof LoginFormData) => {
        const baseClass = "appearance-none relative block w-full px-3 py-3 sm:py-2 pl-10 pr-10 border placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 text-base sm:text-sm transition-all duration-200 hover-lift";

        if (validator.hasFieldError(field)) {
            return `${baseClass} border-red-300`;
        }
        if (validator.isFieldValid(field)) {
            return `${baseClass} border-green-300`;
        }
        return `${baseClass} border-gray-300`;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Only validate if user has entered something
        if (formData.email || formData.password || formData.firstName || formData.lastName) {
            if (!validator.validateAll(formData)) {
                return;
            }
        }

        const registerData = {
            email: formData.email,
            password: formData.password,
            confirmPassword: formData.confirmPassword,
            firstName: formData.firstName || '',
            lastName: formData.lastName || '',
            phone: formData.phone || undefined
        };

        await submit(async () => {
            await onSubmit(registerData);
        }, {
            errorMessage: 'Registration failed'
        });
    };

    return (
        <form className="mt-6 sm:mt-8 space-y-5 sm:space-y-6 animate-fade-in" onSubmit={handleSubmit}>
            <div className="space-y-4 sm:space-y-5">
                {/* Name Fields */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <label htmlFor="firstName" className="sr-only">
                            First Name
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <User className="h-5 w-5 text-gray-400" />
                            </div>
                            <input
                                id="firstName"
                                name="firstName"
                                type="text"
                                autoComplete="given-name"
                                required
                                className={getFieldClassName('firstName')}
                                placeholder="First Name"
                                value={formData.firstName}
                                onChange={handleChange}
                                onBlur={() => handleBlur('firstName')}
                                aria-describedby={validator.hasFieldError('firstName') ? 'firstName-error' : undefined}
                            />
                            <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                                {getFieldValidationIcon('firstName')}
                            </div>
                        </div>
                        {validator.hasFieldError('firstName') && (
                            <p id="firstName-error" className="mt-1 text-sm text-red-600" role="alert">
                                {validator.getFieldError('firstName')}
                            </p>
                        )}
                    </div>

                    <div>
                        <label htmlFor="lastName" className="sr-only">
                            Last Name
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <User className="h-5 w-5 text-gray-400" />
                            </div>
                            <input
                                id="lastName"
                                name="lastName"
                                type="text"
                                autoComplete="family-name"
                                required
                                className={getFieldClassName('lastName')}
                                placeholder="Last Name"
                                value={formData.lastName}
                                onChange={handleChange}
                                onBlur={() => handleBlur('lastName')}
                                aria-describedby={validator.hasFieldError('lastName') ? 'lastName-error' : undefined}
                            />
                            <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                                {getFieldValidationIcon('lastName')}
                            </div>
                        </div>
                        {validator.hasFieldError('lastName') && (
                            <p id="lastName-error" className="mt-1 text-sm text-red-600" role="alert">
                                {validator.getFieldError('lastName')}
                            </p>
                        )}
                    </div>
                </div>

                {/* Phone Field */}
                <div>
                    <label htmlFor="phone" className="sr-only">
                        Phone Number
                    </label>
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Phone className="h-5 w-5 text-gray-400" />
                        </div>
                        <input
                            id="phone"
                            name="phone"
                            type="tel"
                            autoComplete="tel"
                            className={getFieldClassName('phone')}
                            placeholder="Phone Number (Optional)"
                            value={formData.phone}
                            onChange={handleChange}
                            onBlur={() => handleBlur('phone')}
                            aria-describedby={validator.hasFieldError('phone') ? 'phone-error' : undefined}
                        />
                        <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                            {getFieldValidationIcon('phone')}
                        </div>
                    </div>
                    {validator.hasFieldError('phone') && (
                        <p id="phone-error" className="mt-1 text-sm text-red-600" role="alert">
                            {validator.getFieldError('phone')}
                        </p>
                    )}
                </div>

                {/* Email Field */}
                <div>
                    <label htmlFor="email" className="sr-only">
                        Email address
                    </label>
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Mail className="h-5 w-5 text-gray-400" />
                        </div>
                        <input
                            id="email"
                            name="email"
                            type="email"
                            autoComplete="email"
                            required
                            className={getFieldClassName('email')}
                            placeholder="Email address"
                            value={formData.email}
                            onChange={handleChange}
                            onBlur={() => handleBlur('email')}
                            aria-describedby={validator.hasFieldError('email') ? 'email-error' : undefined}
                        />
                        <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                            {getFieldValidationIcon('email')}
                        </div>
                    </div>
                    {validator.hasFieldError('email') && (
                        <p id="email-error" className="mt-1 text-sm text-red-600" role="alert">
                            {validator.getFieldError('email')}
                        </p>
                    )}
                </div>

                {/* Password Field */}
                <div>
                    <label htmlFor="password" className="sr-only">
                        Password
                    </label>
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Lock className="h-5 w-5 text-gray-400" />
                        </div>
                        <input
                            id="password"
                            name="password"
                            type={showPassword ? 'text' : 'password'}
                            autoComplete="new-password"
                            required
                            className={getFieldClassName('password')}
                            placeholder="Password"
                            value={formData.password}
                            onChange={handleChange}
                            onBlur={() => handleBlur('password')}
                            aria-describedby={validator.hasFieldError('password') ? 'password-error' : undefined}
                        />
                        <button
                            type="button"
                            className="absolute inset-y-0 right-0 pr-3 flex items-center min-w-[44px] min-h-[44px] justify-center hover-glow click-shrink"
                            onClick={() => setShowPassword(!showPassword)}
                            aria-label={showPassword ? 'Hide password' : 'Show password'}
                        >
                            {showPassword ? (
                                <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                            ) : (
                                <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                            )}
                        </button>
                    </div>
                    {validator.hasFieldError('password') && (
                        <p id="password-error" className="mt-1 text-sm text-red-600" role="alert">
                            {validator.getFieldError('password')}
                        </p>
                    )}

                    {/* Password Strength Indicator */}
                    {formData.password && (
                        <div className="mt-3 p-3 bg-gray-50 rounded-lg border animate-fade-in">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-gray-700">Password Strength:</span>
                                <span className={`text-sm font-semibold px-2 py-1 rounded-full text-xs ${passwordStrength.score >= 4 ? 'text-green-700 bg-green-100' :
                                        passwordStrength.score >= 3 ? 'text-yellow-700 bg-yellow-100' : 'text-red-700 bg-red-100'
                                    }`}>
                                    {passwordStrength.label}
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                                <div
                                    className={`h-2 rounded-full transition-all duration-500 ease-out ${passwordStrength.color}`}
                                    style={{ width: `${(passwordStrength.score / 5) * 100}%` }}
                                ></div>
                            </div>
                            {passwordStrength.feedback.length > 0 && (
                                <div className="mt-2">
                                    <p className="text-xs font-medium text-gray-700 mb-1">Requirements:</p>
                                    <ul className="text-xs text-gray-600 space-y-1">
                                        {passwordStrength.feedback.map((item, index) => (
                                            <li key={index} className="flex items-center">
                                                <span className="w-1 h-1 bg-gray-400 rounded-full mr-2"></span>
                                                {item}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Confirm Password Field */}
                <div>
                    <label htmlFor="confirmPassword" className="sr-only">
                        Confirm Password
                    </label>
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Lock className="h-5 w-5 text-gray-400" />
                        </div>
                        <input
                            id="confirmPassword"
                            name="confirmPassword"
                            type={showConfirmPassword ? 'text' : 'password'}
                            autoComplete="new-password"
                            required
                            className={getFieldClassName('confirmPassword')}
                            placeholder="Confirm Password"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            onBlur={() => handleBlur('confirmPassword')}
                            aria-describedby={validator.hasFieldError('confirmPassword') ? 'confirmPassword-error' : undefined}
                        />
                        <button
                            type="button"
                            className="absolute inset-y-0 right-0 pr-3 flex items-center min-w-[44px] min-h-[44px] justify-center hover-glow click-shrink"
                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                            aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                        >
                            {showConfirmPassword ? (
                                <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                            ) : (
                                <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                            )}
                        </button>
                    </div>
                    {validator.hasFieldError('confirmPassword') && (
                        <p id="confirmPassword-error" className="mt-1 text-sm text-red-600" role="alert">
                            {validator.getFieldError('confirmPassword')}
                        </p>
                    )}
                </div>
            </div>

            <div>
                <LoadingButton
                    type="submit"
                    isLoading={isLoading}
                    disabled={false}
                    className="group relative w-full flex justify-center py-3 sm:py-2 px-4 border border-transparent text-base sm:text-sm font-medium rounded-lg text-white min-h-[48px] bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 hover-lift click-shrink transition-all duration-200 ease-in-out"
                >
                    Create account
                </LoadingButton>
            </div>
        </form>
    );
};

export default RegisterForm;

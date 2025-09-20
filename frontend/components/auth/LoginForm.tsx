'use client';

import { LoadingButton } from '@/components/LoadingStates';
import { useFormSubmission } from '@/hooks/useLoading';
import { LoginFormData } from '@/lib/auth/types';
import { FormValidator, loginSchema } from '@/lib/form-validation';
import { CheckCircle, Eye, EyeOff, Lock, Mail, XCircle } from 'lucide-react';
import React, { useEffect, useState } from 'react';

interface LoginFormProps {
    onSubmit: (email: string, password: string) => Promise<void>;
    isLoading?: boolean;
}

const LoginForm: React.FC<LoginFormProps> = ({ onSubmit, isLoading = false }) => {
    const [formData, setFormData] = useState<LoginFormData>({
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        phone: '',
        confirmPassword: ''
    });
    const [showPassword, setShowPassword] = useState(false);
    const [validator] = useState(() => new FormValidator(loginSchema));
    const { submit } = useFormSubmission();
    const [isClient, setIsClient] = useState(false);

    useEffect(() => {
        setIsClient(true);
    }, []);

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

        // Always return the same class to prevent hydration mismatch
        return `${baseClass} border-gray-300`;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Only validate if user has entered something
        if (formData.email || formData.password) {
            if (!validator.validateAll(formData)) {
                return;
            }
        }

        await submit(async () => {
            await onSubmit(formData.email, formData.password);
        }, {
            errorMessage: 'Login failed'
        });
    };

    if (!isClient) {
        return <div>Loading...</div>;
    }

    return (
        <form className="mt-6 sm:mt-8 space-y-5 sm:space-y-6 animate-fade-in" onSubmit={handleSubmit}>
            <div className="space-y-4 sm:space-y-5">
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
                            aria-describedby="email-error"
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
                            autoComplete="current-password"
                            required
                            className={getFieldClassName('password')}
                            placeholder="Password"
                            value={formData.password}
                            onChange={handleChange}
                            onBlur={() => handleBlur('password')}
                            aria-describedby="password-error"
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
                </div>
            </div>

            <div>
                <LoadingButton
                    type="submit"
                    isLoading={isLoading}
                    disabled={false}
                    className="group relative w-full flex justify-center py-3 sm:py-2 px-4 border border-transparent text-base sm:text-sm font-medium rounded-lg text-white min-h-[48px] bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 hover-lift click-shrink transition-all duration-200 ease-in-out"
                >
                    Sign in
                </LoadingButton>
            </div>
        </form>
    );
};

export default LoginForm;

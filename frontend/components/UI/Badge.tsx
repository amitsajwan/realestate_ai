import React from 'react';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
    variant?: 'default' | 'secondary' | 'destructive' | 'outline';
    children: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({ 
    children, 
    variant = 'default', 
    className = '', 
    ...props 
}) => {
    const getVariantClasses = (variant: string) => {
        switch (variant) {
            case 'secondary':
                return 'bg-gray-100 text-gray-800';
            case 'destructive':
                return 'bg-red-100 text-red-800';
            case 'outline':
                return 'border border-gray-200 text-gray-800';
            default:
                return 'bg-blue-100 text-blue-800';
        }
    };

    return (
        <span 
            className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getVariantClasses(variant)} ${className}`}
            {...props}
        >
            {children}
        </span>
    );
};

export default Badge;
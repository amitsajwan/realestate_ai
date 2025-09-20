import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
}

interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
}

interface CardBodyProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
}

interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({ children, className = '', ...props }) => {
    return (
        <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`} {...props}>
            {children}
        </div>
    );
};

export const CardHeader: React.FC<CardHeaderProps> = ({ children, className = '', ...props }) => {
    return (
        <div className={`px-6 py-4 border-b border-gray-200 ${className}`} {...props}>
            {children}
        </div>
    );
};

export const CardBody: React.FC<CardBodyProps> = ({ children, className = '', ...props }) => {
    return (
        <div className={`px-6 py-4 ${className}`} {...props}>
            {children}
        </div>
    );
};

export const CardFooter: React.FC<CardFooterProps> = ({ children, className = '', ...props }) => {
    return (
        <div className={`px-6 py-4 border-t border-gray-200 ${className}`} {...props}>
            {children}
        </div>
    );
};

export default Card;
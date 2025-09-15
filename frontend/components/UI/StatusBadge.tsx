import React from 'react';
import { PostStatus } from '../../types/post';

interface StatusBadgeProps {
    status: PostStatus;
    size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
    const getStatusConfig = (status: PostStatus) => {
        switch (status) {
            case 'draft':
                return {
                    label: 'Draft',
                    className: 'bg-gray-100 text-gray-800',
                    icon: '📝'
                };
            case 'published':
                return {
                    label: 'Published',
                    className: 'bg-green-100 text-green-800',
                    icon: '✅'
                };
            case 'scheduled':
                return {
                    label: 'Scheduled',
                    className: 'bg-blue-100 text-blue-800',
                    icon: '⏰'
                };
            case 'archived':
                return {
                    label: 'Archived',
                    className: 'bg-yellow-100 text-yellow-800',
                    icon: '📦'
                };
            default:
                return {
                    label: 'Unknown',
                    className: 'bg-gray-100 text-gray-800',
                    icon: '❓'
                };
        }
    };

    const config = getStatusConfig(status);
    const sizeClasses = {
        sm: 'px-2 py-1 text-xs',
        md: 'px-2.5 py-1.5 text-sm',
        lg: 'px-3 py-2 text-base'
    };

    return (
        <span className={`inline-flex items-center rounded-full font-medium ${config.className} ${sizeClasses[size]}`}>
            <span className="mr-1">{config.icon}</span>
            {config.label}
        </span>
    );
};

export default StatusBadge;

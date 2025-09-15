import React from 'react';

interface ChannelBadgeProps {
    channel: string;
    size?: 'sm' | 'md' | 'lg';
}

export const ChannelBadge: React.FC<ChannelBadgeProps> = ({ channel, size = 'sm' }) => {
    const getChannelConfig = (channel: string) => {
        switch (channel.toLowerCase()) {
            case 'facebook':
                return {
                    label: 'Facebook',
                    className: 'bg-blue-100 text-blue-800',
                    icon: '📘'
                };
            case 'instagram':
                return {
                    label: 'Instagram',
                    className: 'bg-pink-100 text-pink-800',
                    icon: '📷'
                };
            case 'linkedin':
                return {
                    label: 'LinkedIn',
                    className: 'bg-blue-100 text-blue-800',
                    icon: '💼'
                };
            case 'website':
                return {
                    label: 'Website',
                    className: 'bg-gray-100 text-gray-800',
                    icon: '🌐'
                };
            case 'email':
                return {
                    label: 'Email',
                    className: 'bg-green-100 text-green-800',
                    icon: '📧'
                };
            case 'twitter':
                return {
                    label: 'Twitter',
                    className: 'bg-sky-100 text-sky-800',
                    icon: '🐦'
                };
            case 'youtube':
                return {
                    label: 'YouTube',
                    className: 'bg-red-100 text-red-800',
                    icon: '📺'
                };
            default:
                return {
                    label: channel.charAt(0).toUpperCase() + channel.slice(1),
                    className: 'bg-gray-100 text-gray-800',
                    icon: '📱'
                };
        }
    };

    const config = getChannelConfig(channel);
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

export default ChannelBadge;

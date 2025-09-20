import React from 'react';

interface ChannelBadgeProps {
    channel: string;
    className?: string;
}

export const ChannelBadge: React.FC<ChannelBadgeProps> = ({ channel, className = '' }) => {
    const getChannelColor = (channel: string) => {
        switch (channel.toLowerCase()) {
            case 'facebook':
                return 'bg-blue-600 text-white';
            case 'instagram':
                return 'bg-pink-500 text-white';
            case 'linkedin':
                return 'bg-blue-700 text-white';
            case 'twitter':
                return 'bg-blue-400 text-white';
            default:
                return 'bg-gray-500 text-white';
        }
    };

    return (
        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getChannelColor(channel)} ${className}`}>
            {channel}
        </span>
    );
};

export default ChannelBadge;

'use client'

import { Checkbox } from '@/components/UI';
import { Channel, ChannelSelectorProps } from '@/types/social_publishing';

const SUPPORTED_CHANNELS = [
    {
        id: 'facebook' as Channel,
        name: 'Facebook',
        icon: '📘',
        description: 'Facebook page posts',
        available: true
    },
    {
        id: 'instagram' as Channel,
        name: 'Instagram',
        icon: '📷',
        description: 'Instagram posts',
        available: true
    }
];

export default function ChannelSelector({
    selectedChannels,
    onChannelChange
}: ChannelSelectorProps) {

    const handleChannelToggle = (channel: Channel, checked: boolean) => {
        if (checked) {
            onChannelChange([...selectedChannels, channel]);
        } else {
            onChannelChange(selectedChannels.filter(ch => ch !== channel));
        }
    };

    return (
        <div className="space-y-4">
            <div>
                <h3 className="text-lg font-semibold text-primary mb-3">
                    Select Channels
                </h3>
                <p className="text-sm text-secondary mb-4">
                    Choose social media platforms where content will be published.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {SUPPORTED_CHANNELS.map((channel) => {
                    const isSelected = selectedChannels.includes(channel.id);
                    const isDisabled = !channel.available;

                    return (
                        <div
                            key={channel.id}
                            className={`relative p-4 border-2 rounded-lg transition-all ${isSelected
                                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                                } ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                            onClick={() => !isDisabled && handleChannelToggle(channel.id, !isSelected)}
                        >
                            <div className="flex items-center space-x-3">
                                <Checkbox
                                    checked={isSelected}
                                    onChange={(e) => !isDisabled && handleChannelToggle(channel.id, e.target.checked)}
                                    disabled={isDisabled}
                                    className="w-4 h-4"
                                />
                                <span className="text-2xl">{channel.icon}</span>
                                <div>
                                    <div className="font-medium text-primary">{channel.name}</div>
                                    <div className="text-sm text-secondary">{channel.description}</div>
                                </div>
                            </div>

                            {!channel.available && (
                                <div className="absolute top-2 right-2">
                                    <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-500 px-2 py-1 rounded">
                                        Coming Soon
                                    </span>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {selectedChannels.length > 0 && (
                <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <p className="text-sm text-green-700 dark:text-green-300">
                        <strong>{selectedChannels.length}</strong> channel{selectedChannels.length > 1 ? 's' : ''} selected.
                        Content will be generated for: {selectedChannels.map(channel =>
                            SUPPORTED_CHANNELS.find(c => c.id === channel)?.name
                        ).join(', ')}
                    </p>
                </div>
            )}
        </div>
    );
}

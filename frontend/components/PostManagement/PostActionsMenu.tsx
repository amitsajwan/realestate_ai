import React, { useState } from 'react';
import { Post } from '../../types/post';

interface PostActionsMenuProps {
    post: Post;
    onEdit: () => void;
    onDelete: () => void;
    onPublish: (channels: string[]) => void;
    isPublishing?: boolean;
}

const channels = [
    { id: 'facebook', name: 'Facebook', icon: '📘' },
    { id: 'instagram', name: 'Instagram', icon: '📷' },
    { id: 'linkedin', name: 'LinkedIn', icon: '💼' },
    { id: 'website', name: 'Website', icon: '🌐' },
    { id: 'email', name: 'Email', icon: '📧' }
];

export const PostActionsMenu: React.FC<PostActionsMenuProps> = ({
    post,
    onEdit,
    onDelete,
    onPublish,
    isPublishing = false
}) => {
    const [showMenu, setShowMenu] = useState(false);
    const [showPublishMenu, setShowPublishMenu] = useState(false);
    const [selectedChannels, setSelectedChannels] = useState<string[]>([]);

    const handlePublish = () => {
        if (selectedChannels.length > 0) {
            onPublish(selectedChannels);
            setShowPublishMenu(false);
            setShowMenu(false);
        }
    };

    const toggleChannel = (channelId: string) => {
        setSelectedChannels(prev =>
            prev.includes(channelId)
                ? prev.filter(id => id !== channelId)
                : [...prev, channelId]
        );
    };

    const canPublish = post.status === 'draft' || post.status === 'scheduled';
    const canEdit = post.status === 'draft' || post.status === 'scheduled';

    return (
        <div className="relative">
            <button
                onClick={() => setShowMenu(!showMenu)}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
            >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                </svg>
            </button>

            {showMenu && (
                <>
                    <div
                        className="fixed inset-0 z-10"
                        onClick={() => setShowMenu(false)}
                    />
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-20">
                        <div className="py-1">
                            {canEdit && (
                                <button
                                    onClick={() => {
                                        onEdit();
                                        setShowMenu(false);
                                    }}
                                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                >
                                    <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                    </svg>
                                    Edit
                                </button>
                            )}

                            {canPublish && (
                                <button
                                    onClick={() => {
                                        setShowPublishMenu(true);
                                        setShowMenu(false);
                                    }}
                                    disabled={isPublishing}
                                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                                >
                                    <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                    </svg>
                                    {isPublishing ? 'Publishing...' : 'Publish'}
                                </button>
                            )}

                            <button
                                onClick={() => {
                                    onDelete();
                                    setShowMenu(false);
                                }}
                                className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                            >
                                <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                                Delete
                            </button>
                        </div>
                    </div>
                </>
            )}

            {showPublishMenu && (
                <>
                    <div
                        className="fixed inset-0 z-10"
                        onClick={() => setShowPublishMenu(false)}
                    />
                    <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-20">
                        <div className="p-4">
                            <h3 className="text-sm font-medium text-gray-900 mb-3">Select Channels</h3>

                            <div className="space-y-2">
                                {channels.map((channel) => (
                                    <label
                                        key={channel.id}
                                        className="flex items-center space-x-3 cursor-pointer"
                                    >
                                        <input
                                            type="checkbox"
                                            checked={selectedChannels.includes(channel.id)}
                                            onChange={() => toggleChannel(channel.id)}
                                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                        />
                                        <span className="text-lg">{channel.icon}</span>
                                        <span className="text-sm text-gray-700">{channel.name}</span>
                                    </label>
                                ))}
                            </div>

                            <div className="flex items-center justify-end space-x-2 mt-4">
                                <button
                                    onClick={() => setShowPublishMenu(false)}
                                    className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handlePublish}
                                    disabled={selectedChannels.length === 0 || isPublishing}
                                    className="px-4 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                                >
                                    {isPublishing ? 'Publishing...' : 'Publish'}
                                </button>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default PostActionsMenu;

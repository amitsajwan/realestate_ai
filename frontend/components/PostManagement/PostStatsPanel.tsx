import React from 'react';

interface PostStatsPanelProps {
    stats: {
        draft: number;
        published: number;
        scheduled: number;
        archived: number;
    };
}

export const PostStatsPanel: React.FC<PostStatsPanelProps> = ({ stats }) => {
    const total = stats.draft + stats.published + stats.scheduled + stats.archived;

    const statItems = [
        {
            label: 'Draft',
            count: stats.draft,
            color: 'bg-gray-100 text-gray-800',
            icon: '📝'
        },
        {
            label: 'Published',
            count: stats.published,
            color: 'bg-green-100 text-green-800',
            icon: '✅'
        },
        {
            label: 'Scheduled',
            count: stats.scheduled,
            color: 'bg-blue-100 text-blue-800',
            icon: '⏰'
        },
        {
            label: 'Archived',
            count: stats.archived,
            color: 'bg-yellow-100 text-yellow-800',
            icon: '📦'
        }
    ];

    return (
        <div className="space-y-4">
            <div>
                <h3 className="text-lg font-medium text-gray-900">Post Statistics</h3>
                <p className="text-sm text-gray-600">Overview of your posts</p>
            </div>

            <div className="space-y-3">
                {statItems.map((item) => (
                    <div key={item.label} className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                            <span className="text-lg">{item.icon}</span>
                            <span className="text-sm font-medium text-gray-700">{item.label}</span>
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${item.color}`}>
                            {item.count}
                        </span>
                    </div>
                ))}
            </div>

            <div className="pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Total Posts</span>
                    <span className="text-lg font-semibold text-gray-900">{total}</span>
                </div>
            </div>

            {total > 0 && (
                <div className="space-y-2">
                    <div className="text-xs text-gray-500">Distribution</div>
                    <div className="space-y-1">
                        {statItems.map((item) => {
                            const percentage = total > 0 ? (item.count / total) * 100 : 0;
                            return (
                                <div key={item.label} className="flex items-center space-x-2">
                                    <div className="w-16 text-xs text-gray-600">{item.label}</div>
                                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                                        <div
                                            className={`h-2 rounded-full ${item.label === 'Draft' ? 'bg-gray-400' :
                                                item.label === 'Published' ? 'bg-green-400' :
                                                    item.label === 'Scheduled' ? 'bg-blue-400' :
                                                        'bg-yellow-400'
                                                }`}
                                            style={{ width: `${percentage}%` }}
                                        />
                                    </div>
                                    <div className="w-8 text-xs text-gray-600 text-right">
                                        {Math.round(percentage)}%
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {total === 0 && (
                <div className="text-center py-6">
                    <div className="text-4xl text-gray-300 mb-2">📝</div>
                    <p className="text-sm text-gray-500">No posts yet</p>
                    <p className="text-xs text-gray-400">Create your first post to get started</p>
                </div>
            )}
        </div>
    );
};

export default PostStatsPanel;

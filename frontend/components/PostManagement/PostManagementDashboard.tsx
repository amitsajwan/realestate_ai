import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { usePostManagementStore } from '../../store/postManagementStore';
import { Post, PostFilters } from '../../types/post';
import PostCard from './PostCard';
import PostCreationWizard from './PostCreationWizard';
import PostFiltersPanel from './PostFiltersPanel';
import PostStatsPanel from './PostStatsPanel';

interface PostManagementDashboardProps {
    propertyId?: string;
    agentId?: string;
    onClose?: () => void;
}

export const PostManagementDashboard: React.FC<PostManagementDashboardProps> = ({
    propertyId,
    agentId,
    onClose
}) => {
    const [showCreateWizard, setShowCreateWizard] = useState(false);
    const [selectedPost, setSelectedPost] = useState<Post | null>(null);
    const [filters, setFilters] = useState<PostFilters>({
        property_id: propertyId,
        agent_id: agentId,
        skip: 0,
        limit: 20
    });
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [sortBy, setSortBy] = useState<'created_at' | 'updated_at' | 'title'>('created_at');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

    const {
        posts,
        templates,
        loading,
        error,
        fetchPosts,
        createPost,
        updatePost,
        deletePost,
        fetchTemplates
    } = usePostManagementStore();

    useEffect(() => {
        loadData();
    }, [filters]);

    const loadData = async () => {
        try {
            await Promise.all([
                fetchPosts(filters),
                fetchTemplates()
            ]);
        } catch (error) {
            console.error('Failed to load data:', error);
        }
    };

    const handleCreatePost = async (postData: any) => {
        try {
            await createPost(postData);
            setShowCreateWizard(false);
            await loadData();
        } catch (error) {
            console.error('Failed to create post:', error);
        }
    };

    const handleUpdatePost = async (postId: string, updates: any) => {
        try {
            await updatePost(postId, updates);
            await loadData();
        } catch (error) {
            console.error('Failed to update post:', error);
        }
    };

    const handleDeletePost = async (postId: string) => {
        try {
            if (window.confirm('Are you sure you want to delete this post?')) {
                await deletePost(postId);
                await loadData();
            }
        } catch (error) {
            console.error('Failed to delete post:', error);
        }
    };

    const handlePublishPost = async (postId: string, channels: string[]) => {
        try {
            await api.posts.publish(postId, channels);
            await loadData();
        } catch (error) {
            console.error('Failed to publish post:', error);
        }
    };

    const handleFilterChange = (newFilters: Partial<PostFilters>) => {
        setFilters(prev => ({ ...prev, ...newFilters, skip: 0 }));
    };

    const handleSortChange = (field: 'created_at' | 'updated_at' | 'title') => {
        if (sortBy === field) {
            setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
        } else {
            setSortBy(field);
            setSortOrder('desc');
        }
    };

    const sortedPosts = [...posts].sort((a, b) => {
        let aValue = a[sortBy];
        let bValue = b[sortBy];

        if (sortBy === 'created_at' || sortBy === 'updated_at') {
            aValue = new Date(aValue).getTime();
            bValue = new Date(bValue).getTime();
        }

        if (sortOrder === 'asc') {
            return aValue > bValue ? 1 : -1;
        } else {
            return aValue < bValue ? 1 : -1;
        }
    });

    const getStatusCounts = () => {
        const counts = {
            draft: 0,
            published: 0,
            scheduled: 0,
            archived: 0
        };

        posts.forEach(post => {
            counts[post.status as keyof typeof counts]++;
        });

        return counts;
    };

    if (loading && posts.length === 0) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div className="post-management-dashboard bg-gray-50 min-h-screen">
            {/* Header */}
            <div className="bg-white shadow-sm border-b">
                <div className="px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Post Management</h1>
                            <p className="text-gray-600 mt-1">
                                Create, manage, and publish posts for your properties
                            </p>
                        </div>
                        <div className="flex items-center space-x-3">
                            <button
                                onClick={() => setShowCreateWizard(true)}
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                <span className="mr-2">+</span>
                                Create Post
                            </button>
                            {onClose && (
                                <button
                                    onClick={onClose}
                                    className="text-gray-500 hover:text-gray-700"
                                >
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            <div className="flex">
                {/* Sidebar */}
                <div className="w-80 bg-white shadow-sm min-h-screen">
                    <div className="p-6">
                        <PostStatsPanel stats={getStatusCounts()} />
                        <PostFiltersPanel
                            filters={filters}
                            onFilterChange={handleFilterChange}
                            templates={templates}
                        />
                    </div>
                </div>

                {/* Main Content */}
                <div className="flex-1 p-6">
                    {/* Toolbar */}
                    <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                                <div className="flex items-center space-x-2">
                                    <span className="text-sm text-gray-600">View:</span>
                                    <button
                                        onClick={() => setViewMode('grid')}
                                        className={`p-2 rounded ${viewMode === 'grid' ? 'bg-blue-100 text-blue-600' : 'text-gray-500'}`}
                                    >
                                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                            <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                                        </svg>
                                    </button>
                                    <button
                                        onClick={() => setViewMode('list')}
                                        className={`p-2 rounded ${viewMode === 'list' ? 'bg-blue-100 text-blue-600' : 'text-gray-500'}`}
                                    >
                                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                                        </svg>
                                    </button>
                                </div>
                            </div>

                            <div className="flex items-center space-x-4">
                                <div className="flex items-center space-x-2">
                                    <span className="text-sm text-gray-600">Sort by:</span>
                                    <select
                                        value={sortBy}
                                        onChange={(e) => handleSortChange(e.target.value as any)}
                                        className="border border-gray-300 rounded px-3 py-1 text-sm"
                                    >
                                        <option value="created_at">Created Date</option>
                                        <option value="updated_at">Updated Date</option>
                                        <option value="title">Title</option>
                                    </select>
                                    <button
                                        onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
                                        className="p-1 text-gray-500 hover:text-gray-700"
                                    >
                                        {sortOrder === 'asc' ? (
                                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
                                            </svg>
                                        ) : (
                                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                                            </svg>
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Posts Grid/List */}
                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                            <div className="flex">
                                <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                </svg>
                                <div className="ml-3">
                                    <h3 className="text-sm font-medium text-red-800">Error loading posts</h3>
                                    <p className="text-sm text-red-700 mt-1">{error}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {sortedPosts.length === 0 ? (
                        <div className="text-center py-12">
                            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <h3 className="mt-2 text-sm font-medium text-gray-900">No posts found</h3>
                            <p className="mt-1 text-sm text-gray-500">
                                Get started by creating a new post for your property.
                            </p>
                            <div className="mt-6">
                                <button
                                    onClick={() => setShowCreateWizard(true)}
                                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                                >
                                    Create your first post
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className={viewMode === 'grid'
                            ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
                            : 'space-y-4'
                        }>
                            {sortedPosts.map((post) => (
                                <PostCard
                                    key={post.id}
                                    post={post}
                                    viewMode={viewMode}
                                    onEdit={(post) => setSelectedPost(post)}
                                    onDelete={(postId) => handleDeletePost(postId)}
                                    onPublish={(postId, channels) => handlePublishPost(postId, channels)}
                                />
                            ))}
                        </div>
                    )}

                    {/* Load More */}
                    {posts.length >= (filters.limit || 20) && (
                        <div className="text-center mt-8">
                            <button
                                onClick={() => setFilters(prev => ({ ...prev, skip: (prev.skip || 0) + (prev.limit || 20) }))}
                                disabled={loading}
                                className="bg-white border border-gray-300 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                            >
                                {loading ? 'Loading...' : 'Load More'}
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Modals */}
            {showCreateWizard && (
                <PostCreationWizard
                    propertyId={propertyId}
                    onPostCreated={handleCreatePost}
                    onCancel={() => setShowCreateWizard(false)}
                />
            )}

            {selectedPost && (
                <PostEditor
                    post={selectedPost}
                    onPostUpdated={(post) => handleUpdatePost(post.id, post)}
                    onCancel={() => setSelectedPost(null)}
                />
            )}
        </div>
    );
};

export default PostManagementDashboard;

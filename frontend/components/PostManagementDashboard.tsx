"use client";

import React, { useState, useEffect } from 'react';
import { PlusIcon, CalendarIcon, ChartBarIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline';

interface Post {
  _id: string;
  property_title: string;
  property_location: string;
  property_price: string;
  content: string;
  language: string;
  channels: string[];
  status: 'draft' | 'scheduled' | 'published';
  created_at: string;
  scheduled_time?: string;
  published_at?: string;
}

interface PostManagementDashboardProps {
  userId: string;
}

export const PostManagementDashboard: React.FC<PostManagementDashboardProps> = ({ userId }) => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [selectedPost, setSelectedPost] = useState<Post | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'draft' | 'scheduled' | 'published'>('all');

  // Load posts on component mount
  useEffect(() => {
    loadPosts();
  }, [userId, filter]);

  const loadPosts = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/posts?status=${filter === 'all' ? '' : filter}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load posts');
      }

      const data = await response.json();
      setPosts(data.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreatePost = () => {
    setIsCreating(true);
    setSelectedPost(null);
  };

  const handleEditPost = (post: Post) => {
    setSelectedPost(post);
    setIsCreating(false);
  };

  const handleDeletePost = async (postId: string) => {
    if (!confirm('Are you sure you want to delete this post?')) {
      return;
    }

    try {
      const response = await fetch(`/api/posts/${postId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete post');
      }

      // Reload posts
      await loadPosts();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handlePublishPost = async (postId: string) => {
    try {
      const response = await fetch(`/api/posts/publish`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ post_id: postId })
      });

      if (!response.ok) {
        throw new Error('Failed to publish post');
      }

      // Reload posts
      await loadPosts();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'scheduled':
        return 'bg-yellow-100 text-yellow-800';
      case 'published':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'draft':
        return <PencilIcon className="h-4 w-4" />;
      case 'scheduled':
        return <CalendarIcon className="h-4 w-4" />;
      case 'published':
        return <ChartBarIcon className="h-4 w-4" />;
      default:
        return <PencilIcon className="h-4 w-4" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Post Management</h1>
            <p className="mt-2 text-gray-600">Manage your property posts and social media content</p>
          </div>
          <button
            onClick={handleCreatePost}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Create New Post
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { key: 'all', label: 'All Posts', count: posts.length },
              { key: 'draft', label: 'Drafts', count: posts.filter(p => p.status === 'draft').length },
              { key: 'scheduled', label: 'Scheduled', count: posts.filter(p => p.status === 'scheduled').length },
              { key: 'published', label: 'Published', count: posts.filter(p => p.status === 'published').length }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setFilter(tab.key as any)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  filter === tab.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label} ({tab.count})
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Posts Grid */}
      {posts.length === 0 ? (
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400">
            <PencilIcon className="h-12 w-12" />
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No posts found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {filter === 'all' 
              ? 'Get started by creating a new post.'
              : `No ${filter} posts found.`
            }
          </p>
          <div className="mt-6">
            <button
              onClick={handleCreatePost}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Create New Post
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {posts.map((post) => (
            <div key={post._id} className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(post.status)}`}>
                      {getStatusIcon(post.status)}
                      <span className="ml-1 capitalize">{post.status}</span>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleEditPost(post)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDeletePost(post._id)}
                      className="text-gray-400 hover:text-red-600"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                <div className="mt-4">
                  <h3 className="text-lg font-medium text-gray-900 truncate">
                    {post.property_title}
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    {post.property_location} • {post.property_price}
                  </p>
                  <p className="mt-2 text-sm text-gray-600 line-clamp-3">
                    {post.content}
                  </p>
                </div>

                <div className="mt-4">
                  <div className="flex flex-wrap gap-1">
                    {post.channels.map((channel) => (
                      <span
                        key={channel}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {channel}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mt-4 flex justify-between items-center">
                  <div className="text-xs text-gray-500">
                    {post.status === 'scheduled' && post.scheduled_time
                      ? `Scheduled: ${new Date(post.scheduled_time).toLocaleDateString()}`
                      : post.status === 'published' && post.published_at
                      ? `Published: ${new Date(post.published_at).toLocaleDateString()}`
                      : `Created: ${new Date(post.created_at).toLocaleDateString()}`
                    }
                  </div>
                  {post.status === 'draft' && (
                    <button
                      onClick={() => handlePublishPost(post._id)}
                      className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700"
                    >
                      Publish
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Post Editor Modal */}
      {(isCreating || selectedPost) && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {isCreating ? 'Create New Post' : 'Edit Post'}
              </h3>
              {/* Post Editor Component would go here */}
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setIsCreating(false);
                    setSelectedPost(null);
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    // Handle save logic
                    setIsCreating(false);
                    setSelectedPost(null);
                    loadPosts();
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  {isCreating ? 'Create Post' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
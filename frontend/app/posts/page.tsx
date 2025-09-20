'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

interface Post {
  id: string;
  title: string;
  content: string;
  property_id: string;
  language: string;
  channels: string[];
  status: string;
  created_at: string;
}

export default function PostsPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPosts();
  }, []);

  const fetchPosts = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/v1/enhanced-posts/posts/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPosts(data);
      } else {
        setError('Failed to fetch posts');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const publishPost = async (postId: string) => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/v1/enhanced-posts/posts/${postId}/publish`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ channels: ['facebook', 'instagram'] }),
      });

      if (response.ok) {
        // Refresh posts
        fetchPosts();
      } else {
        setError('Failed to publish post');
      }
    } catch (err) {
      setError('Network error');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading posts...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">Posts</h1>
          <Link
            href="/posts/create"
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
          >
            Create Post
          </Link>
        </div>

        {error && (
          <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {posts.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 text-lg mb-4">No posts found</div>
            <Link
              href="/posts/create"
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-md"
            >
              Create your first post
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {posts.map((post) => (
              <div key={post.id} className="bg-gray-800 rounded-lg shadow-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-semibold text-white">
                    {post.title}
                  </h3>
                  <span className={`px-2 py-1 text-xs rounded-full ${post.status === 'published'
                      ? 'bg-green-900 text-green-300'
                      : 'bg-yellow-900 text-yellow-300'
                    }`}>
                    {post.status}
                  </span>
                </div>

                <p className="text-gray-300 mb-4 line-clamp-3">
                  {post.content}
                </p>

                <div className="flex items-center justify-between text-sm text-gray-400 mb-4">
                  <div>
                    <span className="font-medium">Language:</span> {post.language}
                  </div>
                  <div>
                    <span className="font-medium">Channels:</span> {post.channels.join(', ')}
                  </div>
                  <div>
                    <span className="font-medium">Created:</span> {new Date(post.created_at).toLocaleDateString()}
                  </div>
                </div>

                <div className="flex space-x-2">
                  <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm">
                    Edit
                  </button>
                  {post.status !== 'published' && (
                    <button
                      onClick={() => publishPost(post.id)}
                      className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm"
                    >
                      Publish
                    </button>
                  )}
                  <button className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm">
                    View
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
import { create } from 'zustand';
import { api } from '../lib/api';
import { Post, PostCreateRequest, PostFilters, PostUpdateRequest, Template } from '../types/post';

interface PostManagementState {
    posts: Post[];
    templates: Template[];
    loading: boolean;
    error: string | null;

    // Actions
    fetchPosts: (filters: PostFilters) => Promise<void>;
    fetchTemplates: (filters?: any) => Promise<void>;
    createPost: (postData: PostCreateRequest) => Promise<Post>;
    updatePost: (postId: string, updates: PostUpdateRequest) => Promise<Post>;
    deletePost: (postId: string) => Promise<void>;
    getPost: (postId: string) => Promise<Post>;
    publishPost: (postId: string, channels: string[]) => Promise<void>;
    unpublishPost: (postId: string, channels: string[]) => Promise<void>;
    getPostAnalytics: (postId: string) => Promise<any>;
    clearError: () => void;
}

export const usePostManagementStore = create<PostManagementState>((set, get) => ({
    posts: [],
    templates: [],
    loading: false,
    error: null,

    fetchPosts: async (filters: PostFilters) => {
        set({ loading: true, error: null });
        try {
            const posts = await api.posts.get(filters);
            set({ posts, loading: false });
        } catch (error: any) {
            set({ error: error.message || 'Failed to fetch posts', loading: false });
            throw error;
        }
    },

    fetchTemplates: async (filters = {}) => {
        try {
            const templates = await api.templates.get(filters);
            set({ templates });
        } catch (error: any) {
            console.error('Failed to fetch templates:', error);
            // Don't set error for templates as it's not critical
        }
    },

    createPost: async (postData: PostCreateRequest) => {
        set({ loading: true, error: null });
        try {
            const newPost = await api.posts.create(postData);
            set(state => ({
                posts: [newPost, ...state.posts],
                loading: false
            }));
            return newPost;
        } catch (error: any) {
            set({ error: error.message || 'Failed to create post', loading: false });
            throw error;
        }
    },

    updatePost: async (postId: string, updates: PostUpdateRequest) => {
        set({ loading: true, error: null });
        try {
            const updatedPost = await api.posts.update(postId, updates);
            set(state => ({
                posts: state.posts.map(p => p.id === postId ? updatedPost : p),
                loading: false
            }));
            return updatedPost;
        } catch (error: any) {
            set({ error: error.message || 'Failed to update post', loading: false });
            throw error;
        }
    },

    deletePost: async (postId: string) => {
        set({ loading: true, error: null });
        try {
            await api.posts.delete(postId);
            set(state => ({
                posts: state.posts.filter(p => p.id !== postId),
                loading: false
            }));
        } catch (error: any) {
            set({ error: error.message || 'Failed to delete post', loading: false });
            throw error;
        }
    },

    getPost: async (postId: string) => {
        set({ loading: true, error: null });
        try {
            const post = await api.posts.getById(postId);
            set({ loading: false });
            return post;
        } catch (error: any) {
            set({ error: error.message || 'Failed to get post', loading: false });
            throw error;
        }
    },

    publishPost: async (postId: string, channels: string[]) => {
        set({ loading: true, error: null });
        try {
            await api.posts.publish(postId, channels);
            // Update the post status to published
            set(state => ({
                posts: state.posts.map(p =>
                    p.id === postId
                        ? { ...p, status: 'published' as const, published_at: new Date().toISOString() }
                        : p
                ),
                loading: false
            }));
        } catch (error: any) {
            set({ error: error.message || 'Failed to publish post', loading: false });
            throw error;
        }
    },

    unpublishPost: async (postId: string, channels: string[]) => {
        set({ loading: true, error: null });
        try {
            await api.posts.unpublish(postId, channels);
            // Update the post status to draft
            set(state => ({
                posts: state.posts.map(p =>
                    p.id === postId
                        ? { ...p, status: 'draft' as const, published_at: undefined }
                        : p
                ),
                loading: false
            }));
        } catch (error: any) {
            set({ error: error.message || 'Failed to unpublish post', loading: false });
            throw error;
        }
    },

    getPostAnalytics: async (postId: string) => {
        try {
            const analytics = await api.posts.getAnalytics(postId);
            return analytics;
        } catch (error: any) {
            console.error('Failed to get post analytics:', error);
            throw error;
        }
    },

    clearError: () => {
        set({ error: null });
    }
}));

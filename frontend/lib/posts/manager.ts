/**
 * Posts Manager
 * =============
 * Centralized state management for posts
 */

import { logger } from '../logger';
import { postsAPI } from './api';
import {
    AIPostGenerationRequest,
    AIPostGenerationResponse,
    Post,
    PostCreate,
    PostUpdate
} from './types';

export interface PostsState {
    posts: Post[];
    currentPost: Post | null;
    isLoading: boolean;
    error: string | null;
    totalCount: number;
}

export interface PostsResult {
    success: boolean;
    data?: Post | Post[];
    error?: string;
}

export class PostsManager {
    private state: PostsState = {
        posts: [],
        currentPost: null,
        isLoading: false,
        error: null,
        totalCount: 0
    };

    private subscribers: Set<(state: PostsState) => void> = new Set();

    /**
     * Get current state
     */
    getState(): PostsState {
        return { ...this.state };
    }

    /**
     * Subscribe to state changes
     */
    subscribe(callback: (state: PostsState) => void): () => void {
        this.subscribers.add(callback);
        return () => this.subscribers.delete(callback);
    }

    /**
     * Update state and notify subscribers
     */
    private setState(newState: Partial<PostsState>): void {
        this.state = { ...this.state, ...newState };
        this.subscribers.forEach(callback => callback(this.state));
    }

    /**
     * Load all posts
     */
    async loadPosts(skip: number = 0, limit: number = 100): Promise<PostsResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await postsAPI.getPosts(skip, limit);

            if (response.success && response.data) {
                this.setState({
                    posts: response.data,
                    totalCount: response.total || response.data.length,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to load posts');
            }
        } catch (error) {
            logger.error('[PostsManager] Load posts error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Load posts by property ID
     */
    async loadPostsByProperty(propertyId: string): Promise<PostsResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await postsAPI.getPostsByProperty(propertyId);

            if (response.success && response.data) {
                this.setState({
                    posts: response.data,
                    totalCount: response.total || response.data.length,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to load posts by property');
            }
        } catch (error) {
            logger.error('[PostsManager] Load posts by property error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Load a specific post
     */
    async loadPost(postId: string): Promise<PostsResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await postsAPI.getPost(postId);

            if (response.success && response.data) {
                this.setState({
                    currentPost: response.data,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to load post');
            }
        } catch (error) {
            logger.error('[PostsManager] Load post error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Create a new post
     */
    async createPost(postData: PostCreate): Promise<PostsResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await postsAPI.createPost(postData);

            if (response.success && response.data) {
                // Add to posts list
                const currentState = this.getState();
                this.setState({
                    posts: [response.data!, ...currentState.posts],
                    totalCount: currentState.totalCount + 1,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to create post');
            }
        } catch (error) {
            logger.error('[PostsManager] Create post error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Update an existing post
     */
    async updatePost(postId: string, postData: PostUpdate): Promise<PostsResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await postsAPI.updatePost(postId, postData);

            if (response.success && response.data) {
                // Update in posts list
                const currentState = this.getState();
                this.setState({
                    posts: currentState.posts.map((p: Post) =>
                        p.id === postId ? response.data! : p
                    ),
                    currentPost: currentState.currentPost?.id === postId ? response.data! : currentState.currentPost,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to update post');
            }
        } catch (error) {
            logger.error('[PostsManager] Update post error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Delete a post
     */
    async deletePost(postId: string): Promise<PostsResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await postsAPI.deletePost(postId);

            if (response.success) {
                // Remove from posts list
                const currentState = this.getState();
                this.setState({
                    posts: currentState.posts.filter((p: Post) => p.id !== postId),
                    totalCount: currentState.totalCount - 1,
                    currentPost: currentState.currentPost?.id === postId ? null : currentState.currentPost,
                    isLoading: false,
                    error: null
                });
                return { success: true };
            } else {
                throw new Error(response.error || 'Failed to delete post');
            }
        } catch (error) {
            logger.error('[PostsManager] Delete post error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Publish a post
     */
    async publishPost(postId: string): Promise<PostsResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await postsAPI.publishPost(postId);

            if (response.success && response.data) {
                // Update post status in list
                const currentState = this.getState();
                this.setState({
                    posts: currentState.posts.map((p: Post) =>
                        p.id === postId ? { ...p, status: 'published' as any, publishedAt: response.data?.publishedAt } : p
                    ),
                    currentPost: currentState.currentPost?.id === postId ?
                        { ...currentState.currentPost, status: 'published' as any, publishedAt: response.data?.publishedAt } :
                        currentState.currentPost,
                    isLoading: false,
                    error: null
                });
                return { success: true };
            } else {
                throw new Error(response.error || 'Failed to publish post');
            }
        } catch (error) {
            logger.error('[PostsManager] Publish post error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Generate AI post content
     */
    async generateAIPost(generationData: AIPostGenerationRequest): Promise<AIPostGenerationResponse> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await postsAPI.generateAIPost(generationData);

            this.setState({ isLoading: false, error: null });
            return response;
        } catch (error) {
            logger.error('[PostsManager] Generate AI post error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Clear current post
     */
    clearCurrentPost(): void {
        this.setState({ currentPost: null });
    }

    /**
     * Clear error
     */
    clearError(): void {
        this.setState({ error: null });
    }
}

export const postsManager = new PostsManager();

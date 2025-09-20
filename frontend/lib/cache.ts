/**
 * Simple Client-Side Cache
 * ========================
 * Implements a time-based cache for API responses
 */

interface CacheEntry<T> {
    data: T;
    timestamp: number;
    ttl: number;
}

export class CacheManager {
    private static instance: CacheManager;
    private cache: Map<string, CacheEntry<any>>;
    private defaultTTL: number = 5 * 60 * 1000; // 5 minutes

    private constructor() {
        this.cache = new Map();
    }

    static getInstance(): CacheManager {
        if (!CacheManager.instance) {
            CacheManager.instance = new CacheManager();
        }
        return CacheManager.instance;
    }

    /**
     * Generate cache key from method, path, and params
     */
    private generateKey(method: string, path: string, params?: any): string {
        const paramStr = params ? JSON.stringify(params) : '';
        return `${method}:${path}:${paramStr}`;
    }

    /**
     * Get cached data if valid
     */
    get<T>(method: string, path: string, params?: any): T | null {
        const key = this.generateKey(method, path, params);
        const entry = this.cache.get(key);

        if (!entry) return null;

        const now = Date.now();
        if (now - entry.timestamp > entry.ttl) {
            this.cache.delete(key);
            return null;
        }

        return entry.data as T;
    }

    /**
     * Set cache data
     */
    set<T>(method: string, path: string, data: T, params?: any, ttl?: number): void {
        const key = this.generateKey(method, path, params);
        this.cache.set(key, {
            data,
            timestamp: Date.now(),
            ttl: ttl || this.defaultTTL
        });
    }

    /**
     * Clear specific cache entry
     */
    clear(method: string, path: string, params?: any): void {
        const key = this.generateKey(method, path, params);
        this.cache.delete(key);
    }

    /**
     * Clear all cache entries matching a pattern
     */
    clearPattern(pattern: string): void {
        const keys = Array.from(this.cache.keys());
        keys.forEach(key => {
            if (key.includes(pattern)) {
                this.cache.delete(key);
            }
        });
    }

    /**
     * Clear all cache
     */
    clearAll(): void {
        this.cache.clear();
    }

    /**
     * Get cache size
     */
    size(): number {
        return this.cache.size;
    }
}

// Export singleton instance
export const cacheManager = CacheManager.getInstance();

/**
 * React Hook for cached API calls
 */
import { useState, useEffect, useCallback } from 'react';

interface UseCachedDataOptions {
    ttl?: number;
    refetchOnMount?: boolean;
    refetchOnFocus?: boolean;
}

export function useCachedData<T>(
    fetcher: () => Promise<T>,
    cacheKey: { method: string; path: string; params?: any },
    options: UseCachedDataOptions = {}
) {
    const { ttl = 5 * 60 * 1000, refetchOnMount = true, refetchOnFocus = false } = options;
    const [data, setData] = useState<T | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const fetchData = useCallback(async (forceRefresh: boolean = false) => {
        try {
            // Check cache first
            if (!forceRefresh) {
                const cached = cacheManager.get<T>(
                    cacheKey.method,
                    cacheKey.path,
                    cacheKey.params
                );
                if (cached) {
                    setData(cached);
                    return cached;
                }
            }

            // Fetch fresh data
            setIsLoading(true);
            setError(null);
            const freshData = await fetcher();
            
            // Update cache
            cacheManager.set(
                cacheKey.method,
                cacheKey.path,
                freshData,
                cacheKey.params,
                ttl
            );

            setData(freshData);
            return freshData;
        } catch (err) {
            setError(err instanceof Error ? err : new Error('Unknown error'));
            throw err;
        } finally {
            setIsLoading(false);
        }
    }, [fetcher, cacheKey.method, cacheKey.path, cacheKey.params, ttl]);

    useEffect(() => {
        if (refetchOnMount) {
            fetchData();
        }
    }, []);

    useEffect(() => {
        if (!refetchOnFocus) return;

        const handleFocus = () => {
            fetchData();
        };

        window.addEventListener('focus', handleFocus);
        return () => window.removeEventListener('focus', handleFocus);
    }, [fetchData, refetchOnFocus]);

    const refetch = useCallback(() => {
        return fetchData(true);
    }, [fetchData]);

    return { data, isLoading, error, refetch };
}

/**
 * HOC to wrap API calls with caching
 */
export function withCache<T extends (...args: any[]) => Promise<any>>(
    fn: T,
    getCacheKey: (...args: Parameters<T>) => { method: string; path: string; params?: any },
    ttl?: number
): T {
    return (async (...args: Parameters<T>) => {
        const cacheKey = getCacheKey(...args);
        
        // Check cache
        const cached = cacheManager.get(
            cacheKey.method,
            cacheKey.path,
            cacheKey.params
        );
        
        if (cached) {
            return cached;
        }

        // Call original function
        const result = await fn(...args);

        // Cache result
        cacheManager.set(
            cacheKey.method,
            cacheKey.path,
            result,
            cacheKey.params,
            ttl
        );

        return result;
    }) as T;
}
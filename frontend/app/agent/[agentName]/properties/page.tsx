'use client'

import { Property } from '@/lib/properties';
import {
  EyeIcon,
  FunnelIcon,
  HeartIcon,
  HomeIcon,
  MagnifyingGlassIcon,
  MapPinIcon,
  ShareIcon,
  SparklesIcon,
  StarIcon
} from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useEffect, useState } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface PropertyFilters {
  location: string;
  min_price: number | null;
  max_price: number | null;
  property_type: string;
  min_bedrooms: number | null;
  min_bathrooms: number | null;
  min_area: number | null;
  max_area: number | null;
  features: string[];
  sort_by: string;
  sort_order: string;
}

export default function AgentPropertiesPage({ params }: { params: { agentName: string } }) {
  const [properties, setProperties] = useState<Property[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<PropertyFilters>({
    location: '',
    min_price: null,
    max_price: null,
    property_type: '',
    min_bedrooms: null,
    min_bathrooms: null,
    min_area: null,
    max_area: null,
    features: [],
    sort_by: 'created_at',
    sort_order: 'desc'
  });

  const agentName = params.agentName.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

  useEffect(() => {
    loadProperties();
  }, [currentPage, filters]);

  const loadProperties = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/api/v1/agent/public/${params.agentName}/properties?page=${currentPage}&limit=12`
      );

      if (!response.ok) {
        throw new Error('Failed to load properties');
      }

      const data = await response.json();
      setProperties(data.properties || []);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterChange = (key: keyof PropertyFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setFilters({
      location: '',
      min_price: null,
      max_price: null,
      property_type: '',
      min_bedrooms: null,
      min_bathrooms: null,
      min_area: null,
      max_area: null,
      features: [],
      sort_by: 'created_at',
      sort_order: 'desc'
    });
    setCurrentPage(1);
  };

  const formatPrice = (price: number) => {
    if (price >= 10000000) {
      return `₹${(price / 10000000).toFixed(1)}Cr`;
    } else if (price >= 100000) {
      return `₹${(price / 100000).toFixed(1)}L`;
    } else {
      return `₹${price.toLocaleString()}`;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Loading Properties</h2>
          <p className="text-gray-600">Finding the perfect properties for you...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto">
          <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <HomeIcon className="w-10 h-10 text-red-500" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Oops! Something went wrong</h1>
          <p className="text-gray-600 mb-8">{error}</p>
          <button
            onClick={loadProperties}
            className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Hero Header */}
      <header className="relative bg-gradient-to-r from-blue-900 via-blue-800 to-indigo-900 text-white overflow-hidden">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/30 to-purple-600/30"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="flex items-center justify-between">
            <div>
              <Link href="/" className="text-4xl font-bold text-white hover:text-blue-200 transition-colors">
                PropertyAI
              </Link>
              <p className="text-blue-100 mt-3 text-xl">
                Premium Properties by {agentName}
              </p>
              <div className="flex items-center mt-4 space-x-6">
                <div className="flex items-center text-blue-200">
                  <StarIcon className="w-5 h-5 mr-2" />
                  <span>Premium Real Estate</span>
                </div>
                <div className="flex items-center text-blue-200">
                  <SparklesIcon className="w-5 h-5 mr-2" />
                  <span>AI-Powered Insights</span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-6">
              <Link
                href={`/agent/${params.agentName}`}
                className="text-white/90 hover:text-white font-medium transition-colors"
              >
                Agent Profile
              </Link>
              <Link
                href={`/agent/${params.agentName}/posts`}
                className="text-white/90 hover:text-white font-medium transition-colors"
              >
                Posts
              </Link>
              <Link
                href={`/agent/${params.agentName}/contact`}
                className="bg-white/20 backdrop-blur-sm text-white px-8 py-3 rounded-full hover:bg-white/30 transition-all duration-300 font-medium shadow-lg hover:shadow-xl"
              >
                Contact Agent
              </Link>
            </div>
          </div>
        </div>
        {/* Decorative elements */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-white/10 to-transparent rounded-full -translate-y-48 translate-x-48"></div>
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-gradient-to-tr from-white/5 to-transparent rounded-full translate-y-32 -translate-x-32"></div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Search and Filters */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-8 mb-12">
          <div className="flex flex-col lg:flex-row gap-6">
            {/* Search Bar */}
            <div className="flex-1">
              <div className="relative group">
                <MagnifyingGlassIcon className="w-6 h-6 absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                <input
                  type="text"
                  placeholder="Search by location, property type, or features..."
                  value={filters.location}
                  onChange={(e) => handleFilterChange('location', e.target.value)}
                  className="w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300 text-lg bg-white/50 backdrop-blur-sm"
                />
              </div>
            </div>

            {/* Filter Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              <FunnelIcon className="w-5 h-5 mr-2" />
              Advanced Filters
            </button>

            {/* Sort */}
            <select
              value={filters.sort_by}
              onChange={(e) => handleFilterChange('sort_by', e.target.value)}
              className="px-6 py-4 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300 text-lg bg-white/50 backdrop-blur-sm"
            >
              <option value="created_at">Newest First</option>
              <option value="price">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
              <option value="area">Area: Small to Large</option>
            </select>
          </div>
        </div>

        {/* Results Count */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <h2 className="text-3xl font-bold text-gray-900">
              Available Properties
            </h2>
            <p className="text-gray-600 text-lg">
              {properties.length} {properties.length === 1 ? 'property' : 'properties'} found
            </p>
          </div>
        </div>

        {/* Properties Grid */}
        {properties.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {properties.map((property, index) => (
              <motion.div
                key={property.id}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="group bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-500 overflow-hidden border border-gray-100 hover:border-blue-200"
              >
                <Link href={`/agent/${params.agentName}/properties/${property.id}`}>
                  <div className="relative">
                    {property.images && property.images.length > 0 ? (
                      <div className="aspect-w-16 aspect-h-12 relative overflow-hidden">
                        <img
                          src={property.images[0]}
                          alt={property.title}
                          className="w-full h-64 object-cover group-hover:scale-110 transition-transform duration-500"
                        />
                      </div>
                    ) : (
                      <div className="aspect-w-16 aspect-h-12 bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center">
                        <HomeIcon className="w-16 h-16 text-blue-400" />
                      </div>
                    )}

                    {/* Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

                    {/* Action buttons */}
                    <div className="absolute top-4 right-4 flex space-x-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      <button className="w-10 h-10 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center hover:bg-white transition-colors">
                        <HeartIcon className="w-5 h-5 text-gray-600" />
                      </button>
                      <button className="w-10 h-10 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center hover:bg-white transition-colors">
                        <ShareIcon className="w-5 h-5 text-gray-600" />
                      </button>
                    </div>

                    {/* Price badge */}
                    <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg px-3 py-1">
                      <span className="text-lg font-bold text-blue-600">
                        {formatPrice(property.price)}
                      </span>
                    </div>
                  </div>

                  <div className="p-6">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors line-clamp-2">
                        {property.title}
                      </h3>
                      <span className="bg-blue-100 text-blue-800 text-sm font-medium px-3 py-1 rounded-full">
                        {property.propertyType}
                      </span>
                    </div>

                    <div className="flex items-center text-gray-600 mb-4">
                      <MapPinIcon className="w-5 h-5 mr-2 text-blue-500" />
                      <span className="text-sm">{property.location}</span>
                    </div>

                    <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                      {property.bedrooms > 0 && (
                        <div className="flex items-center">
                          <HomeIcon className="w-4 h-4 mr-1" />
                          <span>{property.bedrooms} bed{property.bedrooms !== 1 ? 's' : ''}</span>
                        </div>
                      )}
                      {property.bathrooms > 0 && (
                        <div className="flex items-center">
                          <span className="mr-1">🛁</span>
                          <span>{property.bathrooms} bath{property.bathrooms !== 1 ? 's' : ''}</span>
                        </div>
                      )}
                      {(property.areaSqft || 0) > 0 && (
                        <div className="flex items-center">
                          <span className="mr-1">📐</span>
                          <span>{property.areaSqft} sq ft</span>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center text-yellow-500">
                        <StarIcon className="w-4 h-4 fill-current" />
                        <StarIcon className="w-4 h-4 fill-current" />
                        <StarIcon className="w-4 h-4 fill-current" />
                        <StarIcon className="w-4 h-4 fill-current" />
                        <StarIcon className="w-4 h-4 fill-current" />
                        <span className="ml-2 text-sm text-gray-600">Premium</span>
                      </div>
                      <div className="flex items-center text-gray-500 text-sm">
                        <EyeIcon className="w-4 h-4 mr-1" />
                        <span>View Details</span>
                      </div>
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-20">
            <div className="w-24 h-24 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full flex items-center justify-center mx-auto mb-8">
              <HomeIcon className="w-12 h-12 text-blue-400" />
            </div>
            <h3 className="text-3xl font-bold text-gray-900 mb-4">No Properties Found</h3>
            <p className="text-gray-600 mb-8 text-lg max-w-md mx-auto">
              We couldn't find any properties matching your criteria. Try adjusting your search or clear the filters.
            </p>
            <button
              onClick={clearFilters}
              className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              Clear All Filters
            </button>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-16 flex justify-center">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="px-6 py-3 border-2 border-gray-200 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 hover:border-gray-300 transition-all duration-300 font-medium"
              >
                Previous
              </button>

              <div className="flex items-center space-x-2">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const page = i + 1;
                  return (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`w-12 h-12 rounded-xl font-medium transition-all duration-300 ${currentPage === page
                        ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg'
                        : 'text-gray-600 hover:bg-gray-100'
                        }`}
                    >
                      {page}
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className="px-6 py-3 border-2 border-gray-200 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 hover:border-gray-300 transition-all duration-300 font-medium"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
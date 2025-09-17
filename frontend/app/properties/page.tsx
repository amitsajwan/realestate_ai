'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Property {
  id: string;
  title: string;
  property_type: string;
  price: number;
  location: string;
  bedrooms: number;
  bathrooms: number;
  area_sqft: number;
  status: string;
  created_at: string;
}

export default function PropertiesPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchProperties();
  }, []);

  const fetchProperties = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/v1/properties/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setProperties(data);
      } else {
        setError('Failed to fetch properties');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading properties...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">Properties</h1>
          <Link
            href="/properties/create"
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
          >
            Add Property
          </Link>
        </div>

        {error && (
          <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {properties.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 text-lg mb-4">No properties found</div>
            <Link
              href="/properties/create"
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-md"
            >
              Create your first property
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {properties.map((property) => (
              <div key={property.id} className="bg-gray-800 rounded-lg shadow-lg overflow-hidden">
                <div className="p-6">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-xl font-semibold text-white truncate">
                      {property.title}
                    </h3>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      property.status === 'active' 
                        ? 'bg-green-900 text-green-300' 
                        : 'bg-gray-700 text-gray-300'
                    }`}>
                      {property.status}
                    </span>
                  </div>
                  
                  <p className="text-gray-400 text-sm mb-2">{property.location}</p>
                  
                  <div className="text-2xl font-bold text-blue-400 mb-4">
                    {formatPrice(property.price)}
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 text-sm text-gray-300 mb-4">
                    <div>
                      <span className="font-medium">Type:</span>
                      <br />
                      {property.property_type}
                    </div>
                    <div>
                      <span className="font-medium">Bedrooms:</span>
                      <br />
                      {property.bedrooms}
                    </div>
                    <div>
                      <span className="font-medium">Bathrooms:</span>
                      <br />
                      {property.bathrooms}
                    </div>
                  </div>
                  
                  {property.area_sqft && (
                    <div className="text-sm text-gray-400 mb-4">
                      {property.area_sqft.toLocaleString()} sq ft
                    </div>
                  )}
                  
                  <div className="flex space-x-2">
                    <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm">
                      Edit
                    </button>
                    <button className="flex-1 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm">
                      View
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
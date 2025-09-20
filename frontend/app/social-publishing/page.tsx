'use client'

import { SocialPublishingWorkflow } from '@/components/social_publishing';
import { PropertyContext } from '@/types/social_publishing';

// Mock properties data for testing
const mockProperties: PropertyContext[] = [
    {
        id: 'prop-1',
        title: 'Beautiful 3BHK Apartment',
        description: 'Spacious 3BHK apartment in prime location with modern amenities',
        price: 7500000,
        location: 'Bandra West, Mumbai',
        propertyType: 'Apartment',
        bedrooms: 3,
        bathrooms: 2,
        areaSqft: 1200,
        amenities: ['Swimming Pool', 'Gym', 'Parking', 'Security', 'Garden'],
        features: ['Balcony', 'Modular Kitchen', 'Wooden Flooring', 'AC'],
        images: ['image1.jpg', 'image2.jpg', 'image3.jpg']
    },
    {
        id: 'prop-2',
        title: 'Luxury 4BHK Villa',
        description: 'Premium villa with private garden and modern facilities',
        price: 15000000,
        location: 'Juhu, Mumbai',
        propertyType: 'Villa',
        bedrooms: 4,
        bathrooms: 3,
        areaSqft: 2500,
        amenities: ['Private Garden', 'Swimming Pool', 'Gym', 'Parking', 'Security'],
        features: ['Terrace', 'Study Room', 'Home Theater', 'AC'],
        images: ['villa1.jpg', 'villa2.jpg', 'villa3.jpg']
    },
    {
        id: 'prop-3',
        title: 'Modern 2BHK Flat',
        description: 'Contemporary 2BHK flat perfect for young professionals',
        price: 4500000,
        location: 'Andheri West, Mumbai',
        propertyType: 'Apartment',
        bedrooms: 2,
        bathrooms: 2,
        areaSqft: 800,
        amenities: ['Gym', 'Parking', 'Security', 'Lift'],
        features: ['Balcony', 'Modular Kitchen', 'Tiles Flooring'],
        images: ['flat1.jpg', 'flat2.jpg']
    }
];

export default function SocialPublishingPage() {
    const handleRefresh = () => {
        console.log('Refreshing data...');
        // Add your refresh logic here
    };

    return (
        <div className="min-h-screen">
            <SocialPublishingWorkflow
                properties={mockProperties}
                onRefresh={handleRefresh}
            />
        </div>
    );
}

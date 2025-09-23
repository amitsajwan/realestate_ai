'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function PostsPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the main page with Property Marketing Hub section
    router.replace('/?section=property-marketing-hub');
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <p className="text-gray-600">Redirecting to Property Marketing Hub...</p>
      </div>
    </div>
  );
}
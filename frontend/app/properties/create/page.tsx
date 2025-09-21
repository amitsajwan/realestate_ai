'use client';

import { useRouter } from 'next/navigation';
import GenAIPropertyForm from '@/components/GenAIPropertyForm';

export default function CreatePropertyPage() {
  const router = useRouter();

  const handleSuccess = () => {
    // Redirect to properties list after successful creation
    router.push('/properties');
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <GenAIPropertyForm onSuccess={handleSuccess} />
    </div>
  );
}
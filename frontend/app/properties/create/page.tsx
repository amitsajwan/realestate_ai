'use client';

import GenAIPropertyForm from '@/components/GenAIPropertyForm';
import { useRouter } from 'next/navigation';

export default function CreatePropertyPage() {
  const router = useRouter();

  const handleSuccess = () => {
    // Redirect to dashboard after successful creation
    router.push('/');
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <GenAIPropertyForm onSuccess={handleSuccess} />
    </div>
  );
}
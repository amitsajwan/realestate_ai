'use client';

import React, { useState } from 'react';
import { Button, Card, CardBody, CardHeader } from '@/components/UI';

export default function UXDemo() {
  const [isLoading, setIsLoading] = useState(false);
  const [showShimmer, setShowShimmer] = useState(false);

  const handleDemoAction = () => {
    setIsLoading(true);
    setShowShimmer(true);
    
    setTimeout(() => {
      setIsLoading(false);
      setShowShimmer(false);
    }, 3000);
  };

  return (
    <div className="space-y-8 p-8">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Enhanced UX Features Demo
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Experience the new micro-interactions and polish
        </p>
      </div>

      {/* Interactive Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card className="card-hover">
          <CardHeader>
            <h3 className="text-lg font-semibold">Hover Effects</h3>
          </CardHeader>
          <CardBody>
            <p className="text-gray-600 dark:text-gray-400">
              Hover over this card to see the smooth lift animation and enhanced shadow.
            </p>
          </CardBody>
        </Card>

        <Card className="card-hover">
          <CardHeader>
            <h3 className="text-lg font-semibold">Loading States</h3>
          </CardHeader>
          <CardBody>
            <Button 
              onClick={handleDemoAction}
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? 'Loading...' : 'Trigger Demo'}
            </Button>
            {showShimmer && (
              <div className="mt-4 h-4 shimmer rounded"></div>
            )}
          </CardBody>
        </Card>

        <Card className="card-hover">
          <CardHeader>
            <h3 className="text-lg font-semibold">Animations</h3>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              <div className="float">
                <div className="w-8 h-8 bg-blue-500 rounded-full mx-auto"></div>
              </div>
              <Button 
                onClick={() => {
                  const element = document.querySelector('.bounce-demo');
                  element?.classList.add('bounce-in');
                  setTimeout(() => {
                    element?.classList.remove('bounce-in');
                  }, 600);
                }}
                className="w-full"
              >
                Bounce Demo
              </Button>
              <div className="bounce-demo w-full h-8 bg-green-500 rounded"></div>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Enhanced Input Demo */}
      <Card className="card-hover">
        <CardHeader>
          <h3 className="text-lg font-semibold">Enhanced Inputs</h3>
        </CardHeader>
        <CardBody>
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Enhanced input with focus effects"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg input-enhanced dark:bg-gray-800 dark:text-white"
            />
            <input
              type="email"
              placeholder="Email input with validation"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg input-enhanced dark:bg-gray-800 dark:text-white"
            />
          </div>
        </CardBody>
      </Card>

      {/* Notification Demo */}
      <Card className="card-hover">
        <CardHeader>
          <h3 className="text-lg font-semibold">Notification System</h3>
        </CardHeader>
        <CardBody>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Check the notification bell in the navigation for interactive notifications.
          </p>
          <div className="flex items-center space-x-4">
            <div className="w-3 h-3 bg-green-500 rounded-full pulse-notification"></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Pulse notification indicator
            </span>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
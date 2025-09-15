"use client";

import React, { useState } from 'react';
import { 
  PlusIcon, 
  DocumentTextIcon, 
  ChartBarIcon, 
  CogIcon,
  XMarkIcon,
  SparklesIcon,
  BuildingOfficeIcon,
  UsersIcon
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';

interface QuickAction {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  href?: string;
  onClick?: () => void;
  color: string;
  description: string;
}

interface QuickActionsPanelProps {
  onActionClick?: (actionId: string) => void;
}

export const QuickActionsPanel: React.FC<QuickActionsPanelProps> = ({ 
  onActionClick 
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const quickActions: QuickAction[] = [
    {
      id: 'add-property',
      label: 'Add Property',
      icon: BuildingOfficeIcon,
      href: '/dashboard?section=property-form',
      color: 'bg-blue-500',
      description: 'Create a new property listing'
    },
    {
      id: 'create-post',
      label: 'Create Post',
      icon: DocumentTextIcon,
      href: '/dashboard?section=ai-content',
      color: 'bg-green-500',
      description: 'Generate AI content for social media'
    },
    {
      id: 'view-analytics',
      label: 'Analytics',
      icon: ChartBarIcon,
      href: '/dashboard?section=analytics',
      color: 'bg-purple-500',
      description: 'View performance metrics'
    },
    {
      id: 'manage-team',
      label: 'Team',
      icon: UsersIcon,
      href: '/dashboard?section=team-management',
      color: 'bg-orange-500',
      description: 'Manage team members'
    },
    {
      id: 'ai-tools',
      label: 'AI Tools',
      icon: SparklesIcon,
      href: '/dashboard?section=ai-content',
      color: 'bg-indigo-500',
      description: 'Access AI-powered features'
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: CogIcon,
      href: '/dashboard?section=profile',
      color: 'bg-gray-500',
      description: 'Configure your preferences'
    }
  ];

  const handleActionClick = (action: QuickAction) => {
    if (action.onClick) {
      action.onClick();
    } else if (action.href) {
      window.location.href = action.href;
    }
    
    if (onActionClick) {
      onActionClick(action.id);
    }
    
    setIsOpen(false);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Floating Action Button */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-14 h-14 rounded-full shadow-lg flex items-center justify-center text-white transition-all duration-200 ${
          isOpen ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-600 hover:bg-blue-700'
        }`}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        aria-label={isOpen ? 'Close quick actions' : 'Open quick actions'}
      >
        {isOpen ? (
          <XMarkIcon className="h-6 w-6" />
        ) : (
          <PlusIcon className="h-6 w-6" />
        )}
      </motion.button>

      {/* Quick Actions Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            transition={{ duration: 0.2 }}
            className="absolute bottom-16 right-0 w-64 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-gray-200 dark:border-slate-700 overflow-hidden"
          >
            <div className="p-4">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                Quick Actions
              </h3>
              <div className="space-y-2">
                {quickActions.map((action, index) => (
                  <motion.button
                    key={action.id}
                    onClick={() => handleActionClick(action)}
                    className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors text-left group"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    whileHover={{ x: 4 }}
                  >
                    <div className={`w-8 h-8 rounded-lg ${action.color} flex items-center justify-center flex-shrink-0`}>
                      <action.icon className="h-4 w-4 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                        {action.label}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {action.description}
                      </p>
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import {
  HomeIcon,
  PhoneIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline';

interface AgentNavigationProps {
  agent: {
    agent_name: string;
    slug: string;
    phone?: string;
    email?: string;
  };
}

export default function AgentNavigation({ agent }: AgentNavigationProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const pathname = usePathname();

  const navItems = [
    {
      name: 'Properties',
      href: `/agent/${agent.slug}`,
      icon: HomeIcon,
      isActive: pathname === `/agent/${agent.slug}`
    },
    {
      name: 'Contact',
      href: `/agent/${agent.slug}/contact`,
      icon: PhoneIcon,
      isActive: pathname === `/agent/${agent.slug}/contact`
    }
  ];

  return (
    <nav className="bg-white border-b border-gray-100 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Brand & Agent Info */}
          <div className="flex items-center space-x-4">
            <Link href="/" className="flex items-center space-x-3 group">
              <div className="w-8 h-8 bg-slate-900 rounded-lg flex items-center justify-center group-hover:bg-slate-700 transition-colors">
                <HomeIcon className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-slate-900">PropertyAI</span>
            </Link>
            <span className="hidden md:block text-gray-400">|</span>
            <div className="hidden md:block">
              <h1 className="text-lg font-semibold text-gray-900">{agent.agent_name}</h1>
              <p className="text-sm text-gray-500">Real Estate Professional</p>
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    item.isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
            
            {/* Primary CTA */}
            <Link
              href={`/agent/${agent.slug}/contact`}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              Get In Touch
            </Link>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-600 hover:text-gray-900 p-2 rounded-md"
            >
              {isMenuOpen ? (
                <XMarkIcon className="h-6 w-6" />
              ) : (
                <Bars3Icon className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden border-t border-gray-100">
            <div className="px-2 pt-2 pb-3 space-y-1">
              {/* Agent Info for Mobile */}
              <div className="px-3 py-2 border-b border-gray-100 mb-2">
                <h2 className="font-semibold text-gray-900">{agent.agent_name}</h2>
                <p className="text-sm text-gray-500">Real Estate Professional</p>
              </div>

              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center space-x-3 px-3 py-3 rounded-md text-base font-medium transition-colors ${
                      item.isActive
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                    onClick={() => setIsMenuOpen(false)}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
              
              {/* Mobile CTA */}
              <Link
                href={`/agent/${agent.slug}/contact`}
                className="flex items-center justify-center space-x-2 mx-3 mt-4 bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                onClick={() => setIsMenuOpen(false)}
              >
                <PhoneIcon className="w-5 h-5" />
                <span>Get In Touch</span>
              </Link>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}


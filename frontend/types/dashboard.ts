export interface DashboardStats {
  total_properties: number;
  active_listings: number;
  total_leads: number;
  total_users: number;
  total_views: number;
  monthly_leads: number;
  revenue: string;
}

export interface DashboardWidget {
  id: string;
  title: string;
  description: string;
  component: string;
  enabled: boolean;
  order: number;
  type: 'stats' | 'chart' | 'list' | 'custom';
  category: 'overview' | 'analytics' | 'content' | 'properties';
  size: 'small' | 'medium' | 'large';
  content?: any;
  settings?: Record<string, any>;
}
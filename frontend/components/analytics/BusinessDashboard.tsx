'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardBody as CardContent, CardHeader, CardTitle } from '@/components/UI/Card';
import { Button } from '@/components/UI/Button';
import { Badge } from '@/components/UI/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/UI/Tabs';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Area, AreaChart
} from 'recharts';
import { 
  TrendingUp, TrendingDown, Users, Home, DollarSign, 
  Target, Calendar, Filter, Download, RefreshCw, Sparkles
} from 'lucide-react';
import AIInsightsPanel from './AIInsightsPanel';

interface BusinessMetrics {
  totalProperties: number;
  totalUsers: number;
  totalRevenue: number;
  conversionRate: number;
  avgPropertyPrice: number;
  propertiesThisMonth: number;
  usersThisMonth: number;
  revenueThisMonth: number;
}

interface PropertyAnalytics {
  id: string;
  title: string;
  price: number;
  views: number;
  inquiries: number;
  conversionRate: number;
  daysOnMarket: number;
  status: 'active' | 'sold' | 'pending';
  createdAt: string;
}

interface UserAnalytics {
  id: string;
  email: string;
  propertiesViewed: number;
  propertiesInquired: number;
  conversionRate: number;
  lastActive: string;
  userType: 'buyer' | 'seller' | 'agent';
}

interface RevenueData {
  month: string;
  revenue: number;
  properties: number;
  users: number;
}

interface PropertyPerformanceData {
  name: string;
  views: number;
  inquiries: number;
  price: number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export default function BusinessDashboard() {
  const [metrics, setMetrics] = useState<BusinessMetrics | null>(null);
  const [propertyAnalytics, setPropertyAnalytics] = useState<PropertyAnalytics[]>([]);
  const [userAnalytics, setUserAnalytics] = useState<UserAnalytics[]>([]);
  const [revenueData, setRevenueData] = useState<RevenueData[]>([]);
  const [propertyPerformance, setPropertyPerformance] = useState<PropertyPerformanceData[]>([]);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState('30d');
  const [selectedMetric, setSelectedMetric] = useState('all');

  useEffect(() => {
    fetchBusinessData();
  }, [dateRange, selectedMetric]);

  const fetchBusinessData = async () => {
    setLoading(true);
    try {
      // Fetch business metrics
      const metricsResponse = await fetch(`/api/v1/analytics/business-metrics?range=${dateRange}`);
      const metricsData = await metricsResponse.json();
      setMetrics(metricsData);

      // Fetch property analytics
      const propertiesResponse = await fetch(`/api/v1/analytics/properties?range=${dateRange}`);
      const propertiesData = await propertiesResponse.json();
      setPropertyAnalytics(propertiesData);

      // Fetch user analytics
      const usersResponse = await fetch(`/api/v1/analytics/users?range=${dateRange}`);
      const usersData = await usersResponse.json();
      setUserAnalytics(usersData);

      // Fetch revenue data
      const revenueResponse = await fetch(`/api/v1/analytics/revenue?range=${dateRange}`);
      const revenueData = await revenueResponse.json();
      setRevenueData(revenueData);

      // Fetch property performance data
      const performanceResponse = await fetch(`/api/v1/analytics/property-performance?range=${dateRange}`);
      const performanceData = await performanceResponse.json();
      setPropertyPerformance(performanceData);

    } catch (error) {
      console.error('Error fetching business data:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportData = async (type: string) => {
    try {
      const response = await fetch(`/api/v1/analytics/export?type=${type}&range=${dateRange}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        },
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `business-analytics-${type}-${dateRange}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading business analytics...</span>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">No business data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Business Dashboard</h1>
          <p className="text-muted-foreground">Comprehensive analytics for your real estate platform</p>
        </div>
        <div className="flex items-center space-x-2">
          <select 
            value={dateRange} 
            onChange={(e) => setDateRange(e.target.value)}
            className="px-3 py-2 border rounded-md"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="1y">Last year</option>
          </select>
          <Button onClick={() => exportData('all')} variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export All
          </Button>
          <Button onClick={fetchBusinessData} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Properties</CardTitle>
            <Home className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totalProperties.toLocaleString()}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
              +{metrics.propertiesThisMonth} this month
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totalUsers.toLocaleString()}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
              +{metrics.usersThisMonth} this month
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${metrics.totalRevenue.toLocaleString()}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
              +${metrics.revenueThisMonth.toLocaleString()} this month
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.conversionRate.toFixed(1)}%</div>
            <div className="flex items-center text-xs text-muted-foreground">
              <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
              Above industry average
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts and Analytics */}
      <Tabs defaultValue="revenue" className="space-y-4">
        <TabsList>
          <TabsTrigger value="revenue">Revenue Trends</TabsTrigger>
          <TabsTrigger value="properties">Property Performance</TabsTrigger>
          <TabsTrigger value="users">User Analytics</TabsTrigger>
          <TabsTrigger value="conversion">Conversion Analysis</TabsTrigger>
          <TabsTrigger value="ai-insights" className="flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            AI Insights
          </TabsTrigger>
        </TabsList>

        <TabsContent value="revenue" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Revenue & Growth Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Area 
                    type="monotone" 
                    dataKey="revenue" 
                    stroke="#8884d8" 
                    fill="#8884d8" 
                    fillOpacity={0.6}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="properties" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Top Performing Properties</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={propertyPerformance.slice(0, 5)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="views" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Property Status Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Active', value: propertyAnalytics.filter(p => p.status === 'active').length },
                        { name: 'Sold', value: propertyAnalytics.filter(p => p.status === 'sold').length },
                        { name: 'Pending', value: propertyAnalytics.filter(p => p.status === 'pending').length },
                      ]}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label
                    >
                      {[0, 1, 2].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Property Performance Table</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Property</th>
                      <th className="text-left p-2">Price</th>
                      <th className="text-left p-2">Views</th>
                      <th className="text-left p-2">Inquiries</th>
                      <th className="text-left p-2">Conversion</th>
                      <th className="text-left p-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {propertyAnalytics.slice(0, 10).map((property) => (
                      <tr key={property.id} className="border-b">
                        <td className="p-2 font-medium">{property.title}</td>
                        <td className="p-2">${property.price.toLocaleString()}</td>
                        <td className="p-2">{property.views}</td>
                        <td className="p-2">{property.inquiries}</td>
                        <td className="p-2">
                          <Badge variant={property.conversionRate > 5 ? "default" : "secondary"}>
                            {property.conversionRate.toFixed(1)}%
                          </Badge>
                        </td>
                        <td className="p-2">
                          <Badge variant={
                            property.status === 'sold' ? 'default' :
                            property.status === 'pending' ? 'secondary' : 'outline'
                          }>
                            {property.status}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="users" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>User Type Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Buyers', value: userAnalytics.filter(u => u.userType === 'buyer').length },
                        { name: 'Sellers', value: userAnalytics.filter(u => u.userType === 'seller').length },
                        { name: 'Agents', value: userAnalytics.filter(u => u.userType === 'agent').length },
                      ]}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label
                    >
                      {[0, 1, 2].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>User Engagement Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={revenueData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="users" stroke="#8884d8" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="conversion" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Conversion Funnel Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                  <div>
                    <h3 className="font-semibold">Property Views</h3>
                    <p className="text-sm text-muted-foreground">Total property page visits</p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">
                      {propertyAnalytics.reduce((sum, p) => sum + p.views, 0).toLocaleString()}
                    </div>
                    <div className="text-sm text-green-600">100%</div>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                  <div>
                    <h3 className="font-semibold">Inquiries Generated</h3>
                    <p className="text-sm text-muted-foreground">Users who contacted about properties</p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">
                      {propertyAnalytics.reduce((sum, p) => sum + p.inquiries, 0).toLocaleString()}
                    </div>
                    <div className="text-sm text-green-600">
                      {((propertyAnalytics.reduce((sum, p) => sum + p.inquiries, 0) / 
                        propertyAnalytics.reduce((sum, p) => sum + p.views, 0)) * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                  <div>
                    <h3 className="font-semibold">Properties Sold</h3>
                    <p className="text-sm text-muted-foreground">Successful transactions</p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">
                      {propertyAnalytics.filter(p => p.status === 'sold').length}
                    </div>
                    <div className="text-sm text-green-600">
                      {((propertyAnalytics.filter(p => p.status === 'sold').length / 
                        propertyAnalytics.length) * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ai-insights" className="space-y-4">
          <AIInsightsPanel 
            performanceData={{
              posts: propertyAnalytics.length,
              views: propertyAnalytics.reduce((sum, p) => sum + p.views, 0),
              likes: propertyAnalytics.reduce((sum, p) => sum + p.inquiries, 0),
              shares: propertyAnalytics.reduce((sum, p) => sum + p.views * 0.1, 0), // Estimated
              comments: propertyAnalytics.reduce((sum, p) => sum + p.inquiries * 0.3, 0), // Estimated
              engagement_rate: metrics.conversionRate
            }}
            userId="current-user"
          />
        </TabsContent>
      </Tabs>

      {/* Export Options */}
      <Card>
        <CardHeader>
          <CardTitle>Export Analytics Data</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => exportData('revenue')} variant="outline">
              Export Revenue Data
            </Button>
            <Button onClick={() => exportData('properties')} variant="outline">
              Export Property Analytics
            </Button>
            <Button onClick={() => exportData('users')} variant="outline">
              Export User Analytics
            </Button>
            <Button onClick={() => exportData('performance')} variant="outline">
              Export Performance Data
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
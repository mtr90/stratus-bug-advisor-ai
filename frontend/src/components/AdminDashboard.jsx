import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { 
  Settings, 
  Activity, 
  BarChart3, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Eye,
  EyeOff,
  ExternalLink,
  RefreshCw,
  LogOut
} from 'lucide-react';
import AdminLogin from './AdminLogin';

const AdminDashboard = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [config, setConfig] = useState({
    claude_api_key: '',
    admin_username: 'admin'
  });
  const [showApiKey, setShowApiKey] = useState(false);
  const [systemStatus, setSystemStatus] = useState({
    database: { status: 'unknown', message: 'Checking...' },
    claude_api: { status: 'unknown', message: 'Checking...' },
    cache: { status: 'unknown', message: 'Checking...' }
  });
  const [stats, setStats] = useState({
    total_queries: 0,
    success_rate: 0,
    avg_response_time: 0,
    knowledge_entries: 0,
    recent_activity: []
  });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  // Check authentication status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  // Load data when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      loadConfig();
      loadSystemStatus();
      loadStats();
    }
  }, [isAuthenticated]);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch('/api/admin/config', {
        credentials: 'include'
      });
      if (response.ok) {
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.log('Not authenticated');
    }
  };

  const handleLogin = (success) => {
    if (success) {
      setIsAuthenticated(true);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/admin/logout', {
        method: 'POST',
        credentials: 'include'
      });
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/admin/config', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setConfig(prev => ({
          ...prev,
          admin_username: data.admin_username || 'admin'
        }));
      }
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  };

  const loadSystemStatus = async () => {
    try {
      const response = await fetch('/api/admin/status', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setSystemStatus(data);
      }
    } catch (error) {
      console.error('Failed to load system status:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch('/api/admin/stats', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const saveConfig = async () => {
    setLoading(true);
    setMessage('');
    
    try {
      const response = await fetch('/api/admin/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          claude_api_key: config.claude_api_key
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        setMessage('Configuration saved successfully!');
        setTimeout(() => setMessage(''), 3000);
        loadSystemStatus(); // Refresh status after saving
      } else {
        setMessage(data.error || 'Failed to save configuration');
      }
    } catch (error) {
      setMessage('Failed to save configuration');
    } finally {
      setLoading(false);
    }
  };

  const testClaudeConnection = async () => {
    setLoading(true);
    setMessage('');
    
    try {
      const response = await fetch('/api/admin/test-claude', {
        method: 'POST',
        credentials: 'include'
      });

      const data = await response.json();
      
      if (response.ok) {
        setMessage(`✅ ${data.message}`);
      } else {
        setMessage(`❌ ${data.message}`);
      }
    } catch (error) {
      setMessage('❌ Failed to test Claude connection');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <RefreshCw className="w-4 h-4 text-gray-500 animate-spin" />;
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      healthy: 'bg-green-900 text-green-300 border-green-700',
      warning: 'bg-yellow-900 text-yellow-300 border-yellow-700',
      error: 'bg-red-900 text-red-300 border-red-700',
      unknown: 'bg-gray-900 text-gray-300 border-gray-700'
    };
    
    return (
      <Badge className={`${variants[status]} capitalize`}>
        {status}
      </Badge>
    );
  };

  if (!isAuthenticated) {
    return <AdminLogin onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Admin Dashboard</h1>
            <p className="text-slate-400">STRATUS Bug Advisor System Management</p>
          </div>
          <Button 
            onClick={handleLogout}
            variant="outline" 
            className="border-slate-600 text-slate-300 hover:bg-slate-800"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </Button>
        </div>

        {/* Message Alert */}
        {message && (
          <Alert className={`mb-6 ${message.includes('successfully') || message.includes('✅') 
            ? 'bg-green-900/20 border-green-800' 
            : 'bg-red-900/20 border-red-800'}`}>
            <AlertDescription className={message.includes('successfully') || message.includes('✅') 
              ? 'text-green-400' 
              : 'text-red-400'}>
              {message}
            </AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="config" className="space-y-6">
          <TabsList className="bg-slate-800 border-slate-700">
            <TabsTrigger value="config" className="data-[state=active]:bg-slate-700">
              <Settings className="w-4 h-4 mr-2" />
              Configuration
            </TabsTrigger>
            <TabsTrigger value="status" className="data-[state=active]:bg-slate-700">
              <Activity className="w-4 h-4 mr-2" />
              System Status
            </TabsTrigger>
            <TabsTrigger value="analytics" className="data-[state=active]:bg-slate-700">
              <BarChart3 className="w-4 h-4 mr-2" />
              Analytics
            </TabsTrigger>
          </TabsList>

          {/* Configuration Tab */}
          <TabsContent value="config">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Claude API Configuration</CardTitle>
                <CardDescription className="text-slate-400">
                  Configure your Claude API key for AI-powered bug analysis
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="claude-key" className="text-slate-300">Claude API Key</Label>
                  <div className="relative">
                    <Input
                      id="claude-key"
                      type={showApiKey ? "text" : "password"}
                      placeholder="sk-ant-api03-..."
                      value={config.claude_api_key}
                      onChange={(e) => setConfig(prev => ({ ...prev, claude_api_key: e.target.value }))}
                      className="pr-10 bg-slate-700 border-slate-600 text-white placeholder-slate-400"
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-3 top-3 text-slate-400 hover:text-slate-300"
                    >
                      {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="text-sm text-slate-500">
                    Get your API key from{' '}
                    <a 
                      href="https://console.anthropic.com/" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 inline-flex items-center"
                    >
                      Anthropic Console
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </a>
                  </p>
                </div>

                <div className="flex gap-3">
                  <Button 
                    onClick={saveConfig}
                    disabled={loading}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    {loading ? 'Saving...' : 'Save Configuration'}
                  </Button>
                  <Button 
                    onClick={testClaudeConnection}
                    disabled={loading || !config.claude_api_key}
                    variant="outline"
                    className="border-slate-600 text-slate-300 hover:bg-slate-700"
                  >
                    Test Connection
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* System Status Tab */}
          <TabsContent value="status">
            <div className="grid gap-6 md:grid-cols-3">
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-300">Database</CardTitle>
                  {getStatusIcon(systemStatus.database?.status)}
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    {getStatusBadge(systemStatus.database?.status)}
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    {systemStatus.database?.message}
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-300">Claude API</CardTitle>
                  {getStatusIcon(systemStatus.claude_api?.status)}
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    {getStatusBadge(systemStatus.claude_api?.status)}
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    {systemStatus.claude_api?.message}
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-300">Cache (Redis)</CardTitle>
                  {getStatusIcon(systemStatus.cache?.status)}
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    {getStatusBadge(systemStatus.cache?.status)}
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    {systemStatus.cache?.message}
                  </p>
                </CardContent>
              </Card>
            </div>

            <Card className="bg-slate-800 border-slate-700 mt-6">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white">System Health</CardTitle>
                  <Button 
                    onClick={loadSystemStatus}
                    variant="outline"
                    size="sm"
                    className="border-slate-600 text-slate-300 hover:bg-slate-700"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Refresh
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-slate-400">
                  All systems are monitored in real-time. Check individual component status above.
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-300">Total Queries</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">{stats.total_queries}</div>
                  <p className="text-xs text-slate-500">All time</p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-300">Success Rate</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">{stats.success_rate}%</div>
                  <p className="text-xs text-slate-500">Last 30 days</p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-300">Avg Response Time</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">{stats.avg_response_time}ms</div>
                  <p className="text-xs text-slate-500">Last 24 hours</p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-300">Knowledge Entries</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">{stats.knowledge_entries}</div>
                  <p className="text-xs text-slate-500">Total entries</p>
                </CardContent>
              </Card>
            </div>

            <Card className="bg-slate-800 border-slate-700 mt-6">
              <CardHeader>
                <CardTitle className="text-white">Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                {stats.recent_activity.length > 0 ? (
                  <div className="space-y-2">
                    {stats.recent_activity.map((activity, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-slate-700 rounded">
                        <span className="text-slate-300">{activity.description}</span>
                        <span className="text-slate-500 text-sm">{activity.timestamp}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-400">No recent activity to display.</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AdminDashboard;

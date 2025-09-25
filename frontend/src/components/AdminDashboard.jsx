import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { 
  Settings, 
  Key, 
  Database, 
  Activity, 
  Users, 
  BarChart3,
  CheckCircle, 
  AlertCircle, 
  Loader2,
  Save,
  TestTube,
  RefreshCw,
  Eye,
  EyeOff
} from 'lucide-react'

export default function AdminDashboard() {
  const [apiKey, setApiKey] = useState('')
  const [showApiKey, setShowApiKey] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [message, setMessage] = useState(null)
  const [systemStatus, setSystemStatus] = useState(null)
  const [stats, setStats] = useState({
    totalQueries: 0,
    successfulQueries: 0,
    avgResponseTime: 0,
    knowledgeEntries: 0
  })

  // Load current configuration
  useEffect(() => {
    loadConfiguration()
    loadSystemStatus()
    loadStats()
  }, [])

  const loadConfiguration = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/config')
      if (response.ok) {
        const data = await response.json()
        setApiKey(data.claude_api_key ? '••••••••••••••••' : '')
      }
    } catch (error) {
      console.error('Failed to load configuration:', error)
    }
  }

  const loadSystemStatus = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/status')
      if (response.ok) {
        const data = await response.json()
        setSystemStatus(data)
      }
    } catch (error) {
      console.error('Failed to load system status:', error)
      setSystemStatus({
        database: 'error',
        claude_api: 'error',
        redis: 'warning'
      })
    }
  }

  const loadStats = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/stats')
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const saveConfiguration = async () => {
    if (!apiKey || apiKey === '••••••••••••••••') {
      setMessage({ type: 'error', text: 'Please enter a valid Claude API key' })
      return
    }

    setIsLoading(true)
    setMessage(null)

    try {
      const response = await fetch('http://localhost:5000/api/admin/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          claude_api_key: apiKey
        })
      })

      const data = await response.json()

      if (response.ok) {
        setMessage({ type: 'success', text: 'Configuration saved successfully!' })
        setApiKey('••••••••••••••••')
        setShowApiKey(false)
        loadSystemStatus()
      } else {
        setMessage({ type: 'error', text: data.message || 'Failed to save configuration' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to connect to the server' })
    } finally {
      setIsLoading(false)
    }
  }

  const testApiConnection = async () => {
    setIsTesting(true)
    setMessage(null)

    try {
      const response = await fetch('http://localhost:5000/api/admin/test-claude', {
        method: 'POST'
      })

      const data = await response.json()

      if (response.ok) {
        setMessage({ type: 'success', text: 'Claude API connection successful!' })
        loadSystemStatus()
      } else {
        setMessage({ type: 'error', text: data.message || 'Claude API test failed' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to test API connection' })
    } finally {
      setIsTesting(false)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
    }
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'healthy':
        return <Badge className="bg-green-500/10 text-green-400 border-green-500/20">Healthy</Badge>
      case 'warning':
        return <Badge className="bg-yellow-500/10 text-yellow-400 border-yellow-500/20">Warning</Badge>
      case 'error':
        return <Badge className="bg-red-500/10 text-red-400 border-red-500/20">Error</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Admin Dashboard</h2>
          <p className="text-muted-foreground">Configure API settings, view analytics, and manage the system</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            loadSystemStatus()
            loadStats()
          }}
          className="flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </Button>
      </div>

      {message && (
        <Alert className={`${
          message.type === 'success' 
            ? 'border-green-500/20 bg-green-500/10 text-green-400' 
            : 'border-red-500/20 bg-red-500/10 text-red-400'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle className="h-4 w-4" />
          ) : (
            <AlertCircle className="h-4 w-4" />
          )}
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="configuration" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="configuration" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Configuration
          </TabsTrigger>
          <TabsTrigger value="status" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            System Status
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Analytics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="configuration" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="w-5 h-5" />
                Claude API Configuration
              </CardTitle>
              <CardDescription>
                Configure your Claude API key to enable AI-powered bug analysis
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="apiKey">Claude API Key</Label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Input
                      id="apiKey"
                      type={showApiKey ? "text" : "password"}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="sk-ant-api03-..."
                      className="pr-10"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3"
                      onClick={() => setShowApiKey(!showApiKey)}
                    >
                      {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </Button>
                  </div>
                  <Button
                    onClick={saveConfiguration}
                    disabled={isLoading}
                    className="bg-primary hover:bg-primary/90"
                  >
                    {isLoading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Save className="w-4 h-4" />
                    )}
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground">
                  Get your API key from{' '}
                  <a 
                    href="https://console.anthropic.com/" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    Anthropic Console
                  </a>
                </p>
              </div>

              <div className="flex gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={testApiConnection}
                  disabled={isTesting}
                  className="flex items-center gap-2"
                >
                  {isTesting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <TestTube className="w-4 h-4" />
                  )}
                  Test Connection
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="status" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Database className="w-4 h-4" />
                    Database
                  </span>
                  {systemStatus && getStatusIcon(systemStatus.database)}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {systemStatus && getStatusBadge(systemStatus.database)}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Key className="w-4 h-4" />
                    Claude API
                  </span>
                  {systemStatus && getStatusIcon(systemStatus.claude_api)}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {systemStatus && getStatusBadge(systemStatus.claude_api)}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Activity className="w-4 h-4" />
                    Cache (Redis)
                  </span>
                  {systemStatus && getStatusIcon(systemStatus.redis)}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {systemStatus && getStatusBadge(systemStatus.redis)}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Queries</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-foreground">{stats.totalQueries}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Success Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-foreground">
                  {stats.totalQueries > 0 
                    ? Math.round((stats.successfulQueries / stats.totalQueries) * 100)
                    : 0
                  }%
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Avg Response Time</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-foreground">{stats.avgResponseTime}ms</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Knowledge Entries</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-foreground">{stats.knowledgeEntries}</div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Latest bug analysis requests and system events</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No recent activity to display</p>
                <p className="text-sm">Activity logs will appear here once the system is in use</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

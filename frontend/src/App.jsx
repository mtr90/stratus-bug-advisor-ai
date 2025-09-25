import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { 
  Bug, 
  Search, 
  Loader2, 
  CheckCircle, 
  AlertCircle, 
  FileText, 
  Settings, 
  Moon, 
  Sun,
  Database,
  Code,
  TestTube,
  History,
  Target,
  Wrench
} from 'lucide-react'
import './App.css'
import AdminDashboard from './components/AdminDashboard.jsx'

// Product configurations
const PRODUCTS = [
  {
    id: 'allocator',
    name: 'Allocator',
    description: 'TTS tickets, geocoding issues, batch processing',
    icon: Target,
    color: 'bg-blue-500',
    examples: [
      'TTS-2298 match code 3 geocoding error',
      'Batch allocation timeout during processing',
      'Address standardization failing for bulk imports'
    ]
  },
  {
    id: 'formsplus',
    name: 'FormsPlus',
    description: 'ClickUp tickets, form tree, validation issues',
    icon: FileText,
    color: 'bg-green-500',
    examples: [
      'Form tree navigation not loading properly',
      'Field validation rules not applying correctly',
      'Dynamic form generation throwing errors'
    ]
  },
  {
    id: 'premium_tax',
    name: 'Premium Tax',
    description: 'Tax calculations, e-filing, compliance',
    icon: Database,
    color: 'bg-orange-500',
    examples: [
      'Tax calculation discrepancy in quarterly filing',
      'E-filing service returning validation errors',
      'Rate table updates not reflecting in calculations'
    ]
  },
  {
    id: 'municipal',
    name: 'Municipal',
    description: 'Municipal codes, rates, jurisdiction mapping',
    icon: Code,
    color: 'bg-purple-500',
    examples: [
      'Municipal code lookup returning incorrect rates',
      'Jurisdiction boundary mapping issues',
      'Data import failing for new municipal codes'
    ]
  }
]

function App() {
  const [selectedProduct, setSelectedProduct] = useState('')
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [response, setResponse] = useState(null)
  const [error, setError] = useState(null)
  const [isDark, setIsDark] = useState(true)
  const [activeTab, setActiveTab] = useState('analyzer')

  // Theme toggle
  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
  }, [isDark])

  // Handle query submission
  const handleSubmit = async () => {
    if (!selectedProduct || !query.trim()) {
      setError('Please select a product and enter a bug description')
      return
    }

    setIsLoading(true)
    setError(null)
    setResponse(null)

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          product: selectedProduct
        })
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.message || 'Failed to analyze bug')
      }

      setResponse(data)
    } catch (err) {
      console.error('API Error:', err)
      setError(err.message || 'Failed to connect to the analysis service. Please ensure the backend is running.')
    } finally {
      setIsLoading(false)
    }
  }

  // Handle example query
  const handleExampleClick = (example) => {
    setQuery(example)
  }

  // Format response sections
  const formatResponse = (text) => {
    if (!text) return ''
    
    // Split by sections and format
    const sections = text.split('##').filter(section => section.trim())
    
    return sections.map((section, index) => {
      const lines = section.trim().split('\n')
      const title = lines[0].trim()
      const content = lines.slice(1).join('\n').trim()
      
      const getSectionIcon = (title) => {
        if (title.toLowerCase().includes('root cause')) return Target
        if (title.toLowerCase().includes('solutions')) return Wrench
        if (title.toLowerCase().includes('files')) return FileText
        if (title.toLowerCase().includes('testing')) return TestTube
        if (title.toLowerCase().includes('historical')) return History
        return Bug
      }
      
      const Icon = getSectionIcon(title)
      
      return (
        <div key={index} className="mb-6 opacity-0 animate-in fade-in duration-500" style={{ animationDelay: `${index * 100}ms` }}>
          <div className="flex items-center gap-2 mb-3">
            <Icon className="w-5 h-5 text-primary" />
            <h3 className="text-lg font-semibold text-primary">{title}</h3>
          </div>
          <div className="pl-7 text-foreground/90 whitespace-pre-wrap leading-relaxed">
            {content}
          </div>
        </div>
      )
    })
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-slate-700 to-slate-800 rounded-lg flex items-center justify-center">
                <Bug className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-foreground">STRATUS Bug Advisor</h1>
                <p className="text-sm text-muted-foreground">AI-Powered Bug Resolution System</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsDark(!isDark)}
                className="w-9 h-9"
              >
                {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setActiveTab('admin')}
                className="w-9 h-9"
              >
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-8">
            <TabsTrigger value="analyzer" className="flex items-center gap-2">
              <Bug className="w-4 h-4" />
              Bug Analyzer
            </TabsTrigger>
            <TabsTrigger value="admin" className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Admin Dashboard
            </TabsTrigger>
          </TabsList>

          <TabsContent value="analyzer" className="space-y-8">
            {/* Product Selection */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-foreground mb-4">Select STRATUS Product</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {PRODUCTS.map((product) => {
                  const Icon = product.icon
                  return (
                    <Card
                      key={product.id}
                      className={`cursor-pointer transition-all duration-300 hover:shadow-lg hover:scale-105 ${
                        selectedProduct === product.id 
                          ? 'ring-2 ring-primary bg-primary/5' 
                          : 'hover:border-primary/50'
                      }`}
                      onClick={() => setSelectedProduct(product.id)}
                    >
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 ${product.color} rounded-lg flex items-center justify-center`}>
                            <Icon className="w-5 h-5 text-white" />
                          </div>
                          <div>
                            <CardTitle className="text-lg">{product.name}</CardTitle>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <CardDescription className="text-sm">
                          {product.description}
                        </CardDescription>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            </div>

            {/* Query Input */}
            {selectedProduct && (
              <div className="space-y-4 opacity-0 animate-in fade-in duration-500">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-foreground">Describe Your Bug</h2>
                  <Badge variant="secondary" className="text-xs">
                    {PRODUCTS.find(p => p.id === selectedProduct)?.name}
                  </Badge>
                </div>
                
                <Textarea
                  placeholder={`Describe your ${PRODUCTS.find(p => p.id === selectedProduct)?.name} issue in detail. Include error messages, steps to reproduce, and any relevant ticket numbers...`}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="min-h-[120px] text-base resize-none"
                  maxLength={2000}
                />
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    {query.length}/2000 characters
                  </span>
                  <Button
                    onClick={handleSubmit}
                    disabled={isLoading || !query.trim()}
                    className="bg-primary hover:bg-primary/90 text-primary-foreground"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Search className="w-4 h-4 mr-2" />
                        Analyze Bug
                      </>
                    )}
                  </Button>
                </div>

                {/* Example Queries */}
                <div className="space-y-2">
                  <p className="text-sm font-medium text-muted-foreground">Quick Examples:</p>
                  <div className="flex flex-wrap gap-2">
                    {PRODUCTS.find(p => p.id === selectedProduct)?.examples.map((example, index) => (
                      <Button
                        key={index}
                        variant="outline"
                        size="sm"
                        onClick={() => handleExampleClick(example)}
                        className="text-xs h-8"
                      >
                        {example}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <Alert className="border-red-500/20 bg-red-500/10 text-red-400 opacity-0 animate-in fade-in duration-300">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Response Display */}
            {response && (
              <div className="space-y-6 opacity-0 animate-in fade-in duration-500">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-foreground">AI Analysis Results</h2>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="bg-green-500/10 text-green-400 border-green-500/20">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Success
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      {response.response_time_ms}ms
                    </Badge>
                    {response.confidence && (
                      <Badge variant="outline" className="text-xs">
                        {Math.round(response.confidence * 100)}% confidence
                      </Badge>
                    )}
                  </div>
                </div>

                <Card className="bg-card border border-border shadow-lg">
                  <CardContent className="p-6">
                    <div className="response-content">
                      {formatResponse(response.solution)}
                    </div>
                  </CardContent>
                </Card>

                {/* Feedback */}
                <div className="flex items-center justify-center gap-4 pt-4">
                  <p className="text-sm text-muted-foreground">Was this analysis helpful?</p>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" className="text-green-600 border-green-600 hover:bg-green-50 dark:hover:bg-green-950">
                      👍 Yes
                    </Button>
                    <Button variant="outline" size="sm" className="text-red-600 border-red-600 hover:bg-red-50 dark:hover:bg-red-950">
                      👎 No
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="admin" className="space-y-8">
            <AdminDashboard />
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-card/30 mt-16">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <p>© 2024 STRATUS Bug Advisor. AI-powered bug resolution system.</p>
            <div className="flex items-center gap-4">
              <span>v1.0.0</span>
              <span>•</span>
              <span>Powered by Claude AI</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App

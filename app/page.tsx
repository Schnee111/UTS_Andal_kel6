"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Search, Globe, Clock, BarChart3, Route, ExternalLink, Loader2, Settings } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"

interface SearchResult {
  url: string
  title: string
  content_snippet: string
  similarity_score: number
  route: Array<{ url: string; title: string }>
  last_crawled: string
}

interface CrawlStatus {
  status: string
  pages_crawled: number
  total_pages: number
  current_url?: string
  progress_percentage: number
  start_time?: string
  estimated_completion?: string
}

interface SearchHistory {
  id: number
  query: string
  results_count: number
  searched_at: string
  execution_time: number
  cached: boolean
}

interface Stats {
  total_pages: number
  total_searches: number
  cached_queries: number
  crawl_status: string
  last_crawl: string
  database_size: string
  index_size: number
}

interface Config {
  seed_urls: string[]
  max_pages: number
  max_depth: number
  crawl_delay: number
  user_agent: string
  allowed_domains: string[]
  cache_enabled: boolean
  cache_ttl: number
}

export default function SearchEngine() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [isCrawling, setIsCrawling] = useState(false)
  const [crawlStatus, setCrawlStatus] = useState<CrawlStatus | null>(null)
  const [searchHistory, setSearchHistory] = useState<SearchHistory[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [selectedRoute, setSelectedRoute] = useState<Array<{ url: string; title: string }>>([])
  const [cached, setCached] = useState(false)
  const [config, setConfig] = useState<Config | null>(null)
  const [showSettings, setShowSettings] = useState(false)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

  useEffect(() => {
    fetchConfig()
    fetchStats()
    fetchSearchHistory()

    // Poll crawl status if crawling
    const interval = setInterval(() => {
      if (isCrawling) {
        fetchCrawlStatus()
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [isCrawling])

  const fetchConfig = async () => {
    try {
      const response = await fetch(`${API_BASE}/config`)
      const data = await response.json()
      setConfig(data)
    } catch (error) {
      console.error("Error fetching config:", error)
    }
  }

  const updateConfig = async (newConfig: Partial<Config>) => {
    try {
      const response = await fetch(`${API_BASE}/config`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newConfig),
      })
      if (response.ok) {
        fetchConfig()
      }
    } catch (error) {
      console.error("Error updating config:", error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/stats`)
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error("Error fetching stats:", error)
    }
  }

  const fetchSearchHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/history`)
      const data = await response.json()
      setSearchHistory(data)
    } catch (error) {
      console.error("Error fetching history:", error)
    }
  }

  const fetchCrawlStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/crawl/status`)
      const data = await response.json()
      setCrawlStatus(data)

      if (data.status === "completed" || data.status === "idle") {
        setIsCrawling(false)
        fetchStats()
      }
    } catch (error) {
      console.error("Error fetching crawl status:", error)
    }
  }

  const startCrawl = async () => {
    try {
      setIsCrawling(true)
      const response = await fetch(`${API_BASE}/crawl/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        throw new Error("Failed to start crawling")
      }

      fetchCrawlStatus()
    } catch (error) {
      console.error("Error starting crawl:", error)
      setIsCrawling(false)
    }
  }

  const stopCrawl = async () => {
    try {
      await fetch(`${API_BASE}/crawl/stop`, {
        method: "POST",
      })
      setIsCrawling(false)
      fetchCrawlStatus()
    } catch (error) {
      console.error("Error stopping crawl:", error)
    }
  }

  const clearCache = async () => {
    try {
      await fetch(`${API_BASE}/cache/clear`, {
        method: "POST",
      })
      fetchStats()
    } catch (error) {
      console.error("Error clearing cache:", error)
    }
  }

  const performSearch = async () => {
    if (!query.trim()) return

    setIsSearching(true)
    try {
      const response = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query,
          limit: 10,
        }),
      })

      const data = await response.json()
      setResults(data.results)
      setCached(data.cached)
      fetchSearchHistory()
      fetchStats()
    } catch (error) {
      console.error("Error performing search:", error)
    } finally {
      setIsSearching(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      performSearch()
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Globe className="h-8 w-8 text-blue-600" />
            <h1 className="text-4xl font-bold text-gray-900">Internal Web Search Engine</h1>
          </div>
          <p className="text-gray-600">Mesin pencari internal dengan algoritma BFS/DFS dan caching</p>
        </div>

        <Tabs defaultValue="search" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="search">Pencarian</TabsTrigger>
            <TabsTrigger value="crawl">Crawling</TabsTrigger>
            <TabsTrigger value="history">Riwayat</TabsTrigger>
            <TabsTrigger value="stats">Statistik</TabsTrigger>
            <TabsTrigger value="settings">Pengaturan</TabsTrigger>
          </TabsList>

          {/* Search Tab */}
          <TabsContent value="search" className="space-y-6">
            {/* Search Box */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                      placeholder="Masukkan kata kunci pencarian..."
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      onKeyPress={handleKeyPress}
                      className="pl-10"
                    />
                  </div>
                  <Button onClick={performSearch} disabled={isSearching || !query.trim()}>
                    {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                    Cari
                  </Button>
                </div>
                {cached && (
                  <Alert className="mt-4">
                    <AlertDescription>🚀 Hasil dari cache - pencarian lebih cepat!</AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>

            {/* Search Results */}
            {results.length > 0 && (
              <div className="space-y-4">
                <h2 className="text-xl font-semibold">Hasil Pencarian ({results.length} halaman ditemukan)</h2>
                {results.map((result, index) => (
                  <Card key={index} className="hover:shadow-md transition-shadow">
                    <CardContent className="pt-4">
                      <div className="space-y-2">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h3 className="text-lg font-medium text-blue-600 hover:underline">
                              <a href={result.url} target="_blank" rel="noopener noreferrer">
                                {result.title}
                              </a>
                            </h3>
                            <p className="text-sm text-gray-500">{result.url}</p>
                            <p className="text-xs text-gray-400">
                              Terakhir di-crawl: {new Date(result.last_crawled).toLocaleDateString("id-ID")}
                            </p>
                          </div>
                          <Badge variant="secondary">Score: {(result.similarity_score * 100).toFixed(1)}%</Badge>
                        </div>
                        <p className="text-gray-700">{result.content_snippet}</p>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" onClick={() => window.open(result.url, "_blank")}>
                            <ExternalLink className="h-4 w-4 mr-1" />
                            Buka Halaman
                          </Button>
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button variant="outline" size="sm" onClick={() => setSelectedRoute(result.route)}>
                                <Route className="h-4 w-4 mr-1" />
                                Lihat Rute Link
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-2xl">
                              <DialogHeader>
                                <DialogTitle>Rute Tautan ke Halaman</DialogTitle>
                                <DialogDescription>Jalur navigasi dari halaman awal ke halaman hasil</DialogDescription>
                              </DialogHeader>
                              <div className="space-y-2 max-h-96 overflow-y-auto">
                                {selectedRoute.map((step, stepIndex) => (
                                  <div key={stepIndex} className="flex items-center gap-2 p-2 border rounded">
                                    <Badge variant="outline">{stepIndex + 1}</Badge>
                                    <div className="flex-1">
                                      <p className="font-medium">{step.title}</p>
                                      <p className="text-sm text-gray-500">{step.url}</p>
                                    </div>
                                    {stepIndex < selectedRoute.length - 1 && <div className="text-gray-400">→</div>}
                                  </div>
                                ))}
                              </div>
                            </DialogContent>
                          </Dialog>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {results.length === 0 && query && !isSearching && (
              <Card>
                <CardContent className="pt-6 text-center">
                  <p className="text-gray-500">Tidak ada hasil ditemukan untuk "{query}"</p>
                  <p className="text-sm text-gray-400 mt-2">
                    Coba kata kunci yang berbeda atau jalankan crawling terlebih dahulu
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Crawl Tab */}
          <TabsContent value="crawl" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Kontrol Crawling</CardTitle>
                <CardDescription>Kelola proses crawling halaman web</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Button onClick={startCrawl} disabled={isCrawling} className="flex-1">
                    {isCrawling ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Crawling Berjalan...
                      </>
                    ) : (
                      <>
                        <Globe className="h-4 w-4 mr-2" />
                        Mulai Crawling
                      </>
                    )}
                  </Button>
                  {isCrawling && (
                    <Button onClick={stopCrawl} variant="destructive">
                      Stop
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Crawl Status */}
            {crawlStatus && (
              <Card>
                <CardHeader>
                  <CardTitle>Status Crawling</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>Status:</span>
                      <Badge variant={crawlStatus.status === "crawling" ? "default" : "secondary"}>
                        {crawlStatus.status}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Progress:</span>
                      <span>
                        {crawlStatus.pages_crawled} / {crawlStatus.total_pages} (
                        {crawlStatus.progress_percentage.toFixed(1)}%)
                      </span>
                    </div>
                    {crawlStatus.current_url && (
                      <div className="flex justify-between">
                        <span>URL Saat Ini:</span>
                        <span className="text-sm text-gray-500 truncate max-w-xs">{crawlStatus.current_url}</span>
                      </div>
                    )}
                    {crawlStatus.start_time && (
                      <div className="flex justify-between">
                        <span>Mulai:</span>
                        <span className="text-sm">{new Date(crawlStatus.start_time).toLocaleString("id-ID")}</span>
                      </div>
                    )}
                    {crawlStatus.estimated_completion && (
                      <div className="flex justify-between">
                        <span>Perkiraan Selesai:</span>
                        <span className="text-sm">
                          {new Date(crawlStatus.estimated_completion).toLocaleString("id-ID")}
                        </span>
                      </div>
                    )}
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                        style={{
                          width: `${crawlStatus.progress_percentage}%`,
                        }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Riwayat Pencarian
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {searchHistory.map((item, index) => (
                    <div key={index} className="flex justify-between items-center p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">{item.query}</p>
                        <div className="flex gap-4 text-sm text-gray-500">
                          <span>{item.results_count} hasil</span>
                          <span>{item.execution_time}ms</span>
                          <span>{new Date(item.searched_at).toLocaleString("id-ID")}</span>
                          {item.cached && (
                            <Badge variant="outline" className="text-xs">
                              Cached
                            </Badge>
                          )}
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setQuery(item.query)
                          performSearch()
                        }}
                      >
                        Cari Lagi
                      </Button>
                    </div>
                  ))}
                  {searchHistory.length === 0 && (
                    <p className="text-gray-500 text-center py-4">Belum ada riwayat pencarian</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Stats Tab */}
          <TabsContent value="stats" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Total Halaman</p>
                      <p className="text-2xl font-bold">{stats?.total_pages || 0}</p>
                    </div>
                    <Globe className="h-8 w-8 text-blue-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Total Pencarian</p>
                      <p className="text-2xl font-bold">{stats?.total_searches || 0}</p>
                    </div>
                    <Search className="h-8 w-8 text-green-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Query Ter-cache</p>
                      <p className="text-2xl font-bold">{stats?.cached_queries || 0}</p>
                    </div>
                    <BarChart3 className="h-8 w-8 text-purple-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Ukuran Database</p>
                      <p className="text-lg font-bold">{stats?.database_size || "0 MB"}</p>
                    </div>
                    <Badge variant={stats?.crawl_status === "crawling" ? "default" : "secondary"}>
                      {stats?.crawl_status || "idle"}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </div>

            {stats && (
              <Card>
                <CardHeader>
                  <CardTitle>Informasi Detail</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between">
                    <span>Crawl Terakhir:</span>
                    <span>
                      {stats.last_crawl ? new Date(stats.last_crawl).toLocaleString("id-ID") : "Belum pernah"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Ukuran Index:</span>
                    <span>{stats.index_size} kata unik</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Status Cache:</span>
                    <Badge variant={config?.cache_enabled ? "default" : "secondary"}>
                      {config?.cache_enabled ? "Aktif" : "Nonaktif"}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            )}

            <div className="flex gap-2">
              <Button onClick={clearCache} variant="outline">
                Bersihkan Cache
              </Button>
              <Button onClick={fetchStats} variant="outline">
                Refresh Statistik
              </Button>
            </div>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            {config && (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Settings className="h-5 w-5" />
                      Konfigurasi Crawling
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="seed-urls">Seed URLs (satu per baris)</Label>
                      <Textarea
                        id="seed-urls"
                        value={config.seed_urls.join("\n")}
                        onChange={(e) =>
                          setConfig({
                            ...config,
                            seed_urls: e.target.value.split("\n").filter((url) => url.trim()),
                          })
                        }
                        placeholder="https://www.upi.edu&#10;https://example.com"
                        rows={4}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="max-pages">Maksimal Halaman</Label>
                        <Input
                          id="max-pages"
                          type="number"
                          value={config.max_pages}
                          onChange={(e) =>
                            setConfig({
                              ...config,
                              max_pages: Number.parseInt(e.target.value),
                            })
                          }
                        />
                      </div>
                      <div>
                        <Label htmlFor="max-depth">Kedalaman Maksimal</Label>
                        <Input
                          id="max-depth"
                          type="number"
                          value={config.max_depth}
                          onChange={(e) =>
                            setConfig({
                              ...config,
                              max_depth: Number.parseInt(e.target.value),
                            })
                          }
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="crawl-delay">Delay Crawl (detik)</Label>
                        <Input
                          id="crawl-delay"
                          type="number"
                          step="0.1"
                          value={config.crawl_delay}
                          onChange={(e) =>
                            setConfig({
                              ...config,
                              crawl_delay: Number.parseFloat(e.target.value),
                            })
                          }
                        />
                      </div>
                      <div>
                        <Label htmlFor="cache-ttl">TTL Cache (detik)</Label>
                        <Input
                          id="cache-ttl"
                          type="number"
                          value={config.cache_ttl}
                          onChange={(e) =>
                            setConfig({
                              ...config,
                              cache_ttl: Number.parseInt(e.target.value),
                            })
                          }
                        />
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="user-agent">User Agent</Label>
                      <Input
                        id="user-agent"
                        value={config.user_agent}
                        onChange={(e) =>
                          setConfig({
                            ...config,
                            user_agent: e.target.value,
                          })
                        }
                        placeholder="InternalSearchBot/1.0"
                      />
                    </div>
                    <div>
                      <Label htmlFor="allowed-domains">Domain yang Diizinkan (satu per baris)</Label>
                      <Textarea
                        id="allowed-domains"
                        value={config.allowed_domains.join("\n")}
                        onChange={(e) =>
                          setConfig({
                            ...config,
                            allowed_domains: e.target.value.split("\n").filter((domain) => domain.trim()),
                          })
                        }
                        placeholder="upi.edu&#10;example.com"
                        rows={3}
                      />
                    </div>
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="cache-enabled"
                        checked={config.cache_enabled}
                        onCheckedChange={(checked) =>
                          setConfig({
                            ...config,
                            cache_enabled: checked,
                          })
                        }
                      />
                      <Label htmlFor="cache-enabled">Aktifkan Cache</Label>
                    </div>
                    <Button onClick={() => updateConfig(config)} className="w-full">
                      Simpan Konfigurasi
                    </Button>
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

"use client"

import type React from "react"

import { useState, useEffect } from "react"
import {
  Search,
  Globe,
  Clock,
  BarChart3,
  Route,
  ExternalLink,
  Loader2,
  Settings,
  Filter,
  ChevronLeft,
  ChevronRight,
  Play,
  Square,
  RefreshCw,
  Trash2,
} from "lucide-react"
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface SearchResult {
  url: string
  title: string
  content_snippet: string
  similarity_score: number
  route: Array<{ url: string; title: string }>
  last_crawled: string
  domain?: string
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
  domain_filter?: string
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
  domains?: string[]
  domain_stats?: Record<string, number>
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
  crawl_algorithm: string
}

export default function SearchEngine() {
  const [query, setQuery] = useState("")
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [allPages, setAllPages] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [isCrawling, setIsCrawling] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [crawlStatus, setCrawlStatus] = useState<CrawlStatus | null>(null)
  const [searchHistory, setSearchHistory] = useState<SearchHistory[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [selectedRoute, setSelectedRoute] = useState<Array<{ url: string; title: string }>>([])
  const [cached, setCached] = useState(false)
  const [config, setConfig] = useState<Config | null>(null)
  const [activeTab, setActiveTab] = useState("crawl")
  const [domainFilter, setDomainFilter] = useState<string>("all")
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(10)
  const [showResults, setShowResults] = useState(false)
  const [availableDomains, setAvailableDomains] = useState<string[]>([])
  const [isRefreshingStats, setIsRefreshingStats] = useState(false)
  const [isClearingCache, setIsClearingCache] = useState(false)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

  useEffect(() => {
    fetchConfig()
    fetchStats()
    fetchSearchHistory()
    fetchDomains()

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
      if (response.ok) {
        const data = await response.json()
        setConfig(data)
        console.log("Config loaded:", data)
      } else {
        console.error("Failed to fetch config:", response.status)
      }
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
        const result = await response.json()
        console.log("Config updated:", result)
        fetchConfig()
        alert("Konfigurasi berhasil disimpan!")
      } else {
        console.error("Failed to update config:", response.status)
      }
    } catch (error) {
      console.error("Error updating config:", error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/stats`)
      if (response.ok) {
        const data = await response.json()
        setStats(data)
        if (data.domains) {
          setAvailableDomains(data.domains)
        }
      }
    } catch (error) {
      console.error("Error fetching stats:", error)
    }
  }

  const fetchDomains = async () => {
    try {
      const response = await fetch(`${API_BASE}/domains`)
      if (response.ok) {
        const data = await response.json()
        setAvailableDomains(data.domains || [])
      }
    } catch (error) {
      console.error("Error fetching domains:", error)
    }
  }

  const fetchSearchHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/history`)
      if (response.ok) {
        const data = await response.json()
        setSearchHistory(data)
      }
    } catch (error) {
      console.error("Error fetching history:", error)
    }
  }

  const fetchCrawlStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/crawl/status`)
      if (response.ok) {
        const data = await response.json()
        setCrawlStatus(data)

        if (data.status === "completed" || data.status === "idle") {
          setIsCrawling(false)
          fetchStats()
          fetchDomains()

          // Automatically fetch all pages when crawling completes
          if (data.status === "completed") {
            fetchAllPages()
            setShowResults(true)
          }
        }
      }
    } catch (error) {
      console.error("Error fetching crawl status:", error)
    }
  }

  const startCrawl = async () => {
    try {
      setIsCrawling(true)
      setShowResults(false)
      const response = await fetch(`${API_BASE}/crawl/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          algorithm: config?.crawl_algorithm || "BFS",
          max_pages: config?.max_pages || 50,
          max_depth: config?.max_depth || 3,
        }),
      })

      if (response.ok) {
        const result = await response.json()
        console.log("Crawl started:", result)
        fetchCrawlStatus()
      } else {
        console.error("Failed to start crawling:", response.status)
        setIsCrawling(false)
      }
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

  const fetchAllPages = async () => {
    try {
      setIsExporting(true)
      // Gunakan endpoint search biasa dengan query kosong untuk mendapatkan semua halaman
      const response = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: "", // Query kosong untuk mendapatkan semua halaman
          limit: 1000, // Ambil banyak hasil
          domain_filter: null,
        }),
      })

      if (response.ok) {
        const data = await response.json()

        if (data && data.results) {
          // Transform data untuk menambahkan domain
          const transformedPages = data.results.map((page: any) => ({
            ...page,
            domain: page.domain || extractDomain(page.url),
          }))

          setAllPages(transformedPages)
          console.log(`Loaded ${transformedPages.length} pages`)
        }
      }
    } catch (error) {
      console.error("Error fetching all pages:", error)
    } finally {
      setIsExporting(false)
    }
  }

  const extractDomain = (url: string): string => {
    try {
      const urlObj = new URL(url)
      return urlObj.hostname.replace("www.", "")
    } catch {
      return "unknown"
    }
  }

  const performSearch = async () => {
    setIsSearching(true)
    try {
      const response = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query.trim(),
          limit: 100,
          domain_filter: domainFilter === "all" ? null : domainFilter,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setSearchResults(data.results || [])
        setCached(data.cached || false)
        fetchSearchHistory()
        fetchStats()
      }
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

  const clearHistory = async () => {
    try {
      await fetch(`${API_BASE}/history/clear`, {
        method: "POST",
      })
      setSearchHistory([])
    } catch (error) {
      console.error("Error clearing history:", error)
    }
  }

  const deleteHistoryItem = async (id: number) => {
    try {
      await fetch(`${API_BASE}/history/${id}`, {
        method: "DELETE",
      })
      fetchSearchHistory()
    } catch (error) {
      console.error("Error deleting history item:", error)
    }
  }

  const handleRefreshStats = async () => {
    setIsRefreshingStats(true)
    try {
      await fetchStats()
      await fetchDomains()
      console.log("Stats refreshed successfully")
    } catch (error) {
      console.error("Error refreshing stats:", error)
    } finally {
      setIsRefreshingStats(false)
    }
  }

  const handleClearCache = async () => {
    setIsClearingCache(true)
    try {
      const response = await fetch(`${API_BASE}/cache/clear`, {
        method: "POST",
      })

      if (response.ok) {
        const result = await response.json()
        console.log("Cache cleared:", result.message)
        await fetchStats() // Refresh stats after clearing cache
        alert("Cache berhasil dibersihkan!")
      } else {
        console.error("Failed to clear cache:", response.status)
        alert("Gagal membersihkan cache")
      }
    } catch (error) {
      console.error("Error clearing cache:", error)
      alert("Error saat membersihkan cache")
    } finally {
      setIsClearingCache(false)
    }
  }

  // Get results to display (search results if searching, all pages if not)
  const displayResults = query.trim() ? searchResults : allPages

  // Apply domain filter
  const filteredResults = displayResults.filter((page) => {
    if (domainFilter === "all") return true
    return page.domain === domainFilter
  })

  // Pagination
  const totalPages = Math.ceil(filteredResults.length / itemsPerPage)
  const paginatedResults = filteredResults.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)

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

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="crawl">Crawling & Search</TabsTrigger>
            <TabsTrigger value="history">Riwayat</TabsTrigger>
            <TabsTrigger value="stats">Statistik</TabsTrigger>
            <TabsTrigger value="settings">Pengaturan</TabsTrigger>
          </TabsList>

          {/* Crawl & Search Tab */}
          <TabsContent value="crawl" className="space-y-6">
            {/* Crawl Control */}
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
                        <Play className="h-4 w-4 mr-2" />
                        Mulai Crawling
                      </>
                    )}
                  </Button>
                  {isCrawling && (
                    <Button onClick={stopCrawl} variant="destructive">
                      <Square className="h-4 w-4 mr-2" />
                      Stop
                    </Button>
                  )}
                </div>

                {config && (
                  <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                    <p>
                      <strong>Algoritma:</strong> {config.crawl_algorithm}
                    </p>
                    <p>
                      <strong>Max Halaman:</strong> {config.max_pages}
                    </p>
                    <p>
                      <strong>Max Kedalaman:</strong> {config.max_depth}
                    </p>
                    <p>
                      <strong>Seed URLs:</strong> {config.seed_urls.join(", ")}
                    </p>
                  </div>
                )}

                {/* Crawl Status */}
                {crawlStatus && (
                  <div className="space-y-3 border-t pt-4">
                    <div className="flex justify-between items-center">
                      <span>Status:</span>
                      <Badge variant={crawlStatus.status === "crawling" ? "default" : "secondary"}>
                        {crawlStatus.status === "crawling"
                          ? "Sedang Crawling"
                          : crawlStatus.status === "completed"
                            ? "Selesai"
                            : "Idle"}
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
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                        style={{
                          width: `${crawlStatus.progress_percentage}%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Search Section - Only show after crawling or if there are pages */}
            {(showResults || allPages.length > 0 || searchResults.length > 0) && (
              <Card>
                <CardHeader>
                  <CardTitle>Pencarian Hasil Crawling</CardTitle>
                  <CardDescription>Cari dalam halaman yang telah di-crawl</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-col gap-4">
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                        <Input
                          placeholder="Cari dalam hasil crawling... (kosongkan untuk melihat semua)"
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                          onKeyPress={handleKeyPress}
                          className="pl-10"
                        />
                      </div>
                      <Button onClick={performSearch} disabled={isSearching}>
                        {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                        Cari
                      </Button>
                    </div>

                    <div className="flex items-center gap-4">
                      {availableDomains && availableDomains.length > 0 && (
                        <div className="flex items-center gap-2">
                          <Label htmlFor="domain-filter" className="whitespace-nowrap">
                            Filter Domain:
                          </Label>
                          <Select value={domainFilter} onValueChange={setDomainFilter}>
                            <SelectTrigger id="domain-filter" className="w-48">
                              <SelectValue placeholder="Semua Domain" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="all">Semua Domain</SelectItem>
                              {availableDomains.map((domain, index) => (
                                <SelectItem key={index} value={domain}>
                                  {domain}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      )}

                      <Button variant="outline" onClick={fetchAllPages} disabled={isExporting}>
                        {isExporting ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <Filter className="h-4 w-4 mr-2" />
                        )}
                        Refresh Data
                      </Button>
                    </div>
                  </div>

                  {cached && (
                    <Alert>
                      <AlertDescription>🚀 Hasil dari cache - pencarian lebih cepat!</AlertDescription>
                    </Alert>
                  )}

                  {/* Results count */}
                  <div className="text-sm text-gray-500">
                    Menampilkan {paginatedResults.length} dari {filteredResults.length} halaman
                    {query.trim() && ` untuk "${query}"`}
                    {domainFilter !== "all" && ` di domain "${domainFilter}"`}
                  </div>

                  {/* Results list */}
                  <div className="space-y-4">
                    {paginatedResults.length > 0 ? (
                      paginatedResults.map((result, index) => (
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
                                  <div className="flex gap-2 items-center">
                                    <p className="text-xs text-gray-400">
                                      Terakhir di-crawl: {new Date(result.last_crawled).toLocaleDateString("id-ID")}
                                    </p>
                                    {result.domain && (
                                      <Badge variant="outline" className="text-xs">
                                        {result.domain}
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                                {query.trim() && (
                                  <Badge variant="secondary">
                                    Score: {(result.similarity_score * 100).toFixed(1)}%
                                  </Badge>
                                )}
                              </div>
                              <p className="text-gray-700">{result.content_snippet}</p>
                              <div className="flex gap-2">
                                <Button variant="outline" size="sm" onClick={() => window.open(result.url, "_blank")}>
                                  <ExternalLink className="h-4 w-4 mr-1" />
                                  Buka Halaman
                                </Button>
                                {result.route && result.route.length > 0 && (
                                  <Dialog>
                                    <DialogTrigger asChild>
                                      <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setSelectedRoute(result.route)}
                                      >
                                        <Route className="h-4 w-4 mr-1" />
                                        Lihat Rute Link
                                      </Button>
                                    </DialogTrigger>
                                    <DialogContent className="max-w-2xl">
                                      <DialogHeader>
                                        <DialogTitle>Rute Tautan ke Halaman</DialogTitle>
                                        <DialogDescription>
                                          Jalur navigasi dari halaman awal ke halaman hasil
                                        </DialogDescription>
                                      </DialogHeader>
                                      <div className="space-y-2 max-h-96 overflow-y-auto">
                                        {selectedRoute.map((step, stepIndex) => (
                                          <div key={stepIndex} className="flex items-center gap-2 p-2 border rounded">
                                            <Badge variant="outline">{stepIndex + 1}</Badge>
                                            <div className="flex-1">
                                              <p className="font-medium">{step.title}</p>
                                              <p className="text-sm text-gray-500">{step.url}</p>
                                            </div>
                                            {stepIndex < selectedRoute.length - 1 && (
                                              <div className="text-gray-400">→</div>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    </DialogContent>
                                  </Dialog>
                                )}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))
                    ) : (
                      <div className="text-center py-8">
                        {allPages.length === 0 ? (
                          <>
                            <p className="text-gray-500">Belum ada halaman yang di-crawl</p>
                            <p className="text-sm text-gray-400 mt-2">
                              Jalankan crawling terlebih dahulu untuk melihat hasilnya
                            </p>
                          </>
                        ) : query.trim() ? (
                          <p className="text-gray-500">Tidak ada hasil ditemukan untuk "{query}"</p>
                        ) : (
                          <p className="text-gray-500">Tidak ada hasil yang sesuai dengan filter</p>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Pagination */}
                  {filteredResults.length > 0 && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Label htmlFor="items-per-page">Tampilkan:</Label>
                        <Select
                          value={itemsPerPage.toString()}
                          onValueChange={(value) => {
                            setItemsPerPage(Number(value))
                            setCurrentPage(1)
                          }}
                        >
                          <SelectTrigger id="items-per-page" className="w-20">
                            <SelectValue placeholder="10" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="5">5</SelectItem>
                            <SelectItem value="10">10</SelectItem>
                            <SelectItem value="20">20</SelectItem>
                            <SelectItem value="50">50</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                          disabled={currentPage === 1}
                        >
                          <ChevronLeft className="h-4 w-4" />
                        </Button>
                        <span className="text-sm">
                          Halaman {currentPage} dari {totalPages}
                        </span>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
                          disabled={currentPage === totalPages}
                        >
                          <ChevronRight className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Algorithm Comparison */}
            <Card>
              <CardHeader>
                <CardTitle>Perbandingan Algoritma</CardTitle>
                <CardDescription>Perbedaan antara BFS dan DFS</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="border rounded-lg p-4">
                    <h3 className="font-bold text-lg mb-2">BFS (Breadth-First Search)</h3>
                    <ul className="list-disc pl-5 space-y-1 text-sm">
                      <li>Menjelajahi semua halaman di level yang sama sebelum ke level berikutnya</li>
                      <li>Ideal untuk website dengan struktur hierarkis yang jelas</li>
                      <li>Memberikan cakupan yang merata di seluruh website</li>
                      <li>Menggunakan lebih banyak memori (menyimpan semua node di level saat ini)</li>
                    </ul>
                  </div>
                  <div className="border rounded-lg p-4">
                    <h3 className="font-bold text-lg mb-2">DFS (Depth-First Search)</h3>
                    <ul className="list-disc pl-5 space-y-1 text-sm">
                      <li>Menjelajahi sedalam mungkin sebelum backtrack ke cabang lain</li>
                      <li>Ideal untuk website dengan konten yang saling terkait erat</li>
                      <li>Lebih efisien untuk eksplorasi mendalam pada topik tertentu</li>
                      <li>Menggunakan lebih sedikit memori (hanya menyimpan path saat ini)</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history" className="space-y-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    Riwayat Pencarian
                  </CardTitle>
                </div>
                <Button variant="outline" size="sm" onClick={clearHistory}>
                  Hapus Semua
                </Button>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {searchHistory.length > 0 ? (
                    searchHistory.map((item, index) => (
                      <div key={index} className="flex justify-between items-center p-3 border rounded-lg">
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{item.query || "(Query kosong)"}</p>
                            {item.domain_filter && (
                              <Badge variant="outline" className="text-xs">
                                Domain: {item.domain_filter}
                              </Badge>
                            )}
                          </div>
                          <div className="flex gap-4 text-sm text-gray-500">
                            <span>{item.results_count} hasil</span>
                            <span>{item.execution_time.toFixed(1)}ms</span>
                            <span>{new Date(item.searched_at).toLocaleString("id-ID")}</span>
                            {item.cached && (
                              <Badge variant="outline" className="text-xs">
                                Cached
                              </Badge>
                            )}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setQuery(item.query)
                              setDomainFilter(item.domain_filter || "all")
                              setActiveTab("crawl")
                              setTimeout(() => performSearch(), 100)
                            }}
                          >
                            Cari Lagi
                          </Button>
                          <Button variant="outline" size="sm" onClick={() => deleteHistoryItem(item.id)}>
                            Hapus
                          </Button>
                        </div>
                      </div>
                    ))
                  ) : (
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

                  <div className="border-t my-4"></div>

                  <div>
                    <h3 className="font-medium mb-2">Domain yang Tersedia:</h3>
                    <div className="flex flex-wrap gap-2">
                      {availableDomains && availableDomains.length > 0 ? (
                        availableDomains.map((domain, index) => (
                          <Badge key={index} variant="outline">
                            {domain}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-gray-500">Tidak ada domain</span>
                      )}
                    </div>
                  </div>

                  {stats.domain_stats && Object.keys(stats.domain_stats).length > 0 && (
                    <div>
                      <h3 className="font-medium mb-2 mt-4">Statistik per Domain:</h3>
                      <div className="space-y-2">
                        {Object.entries(stats.domain_stats).map(([domain, count]) => (
                          <div key={domain} className="flex justify-between items-center">
                            <span className="text-sm">{domain}</span>
                            <Badge variant="secondary">{count} halaman</Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            <div className="flex gap-2">
              <Button onClick={handleClearCache} variant="outline" disabled={isClearingCache}>
                {isClearingCache ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Membersihkan...
                  </>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4 mr-2" />
                    Bersihkan Cache
                  </>
                )}
              </Button>
              <Button onClick={handleRefreshStats} variant="outline" disabled={isRefreshingStats}>
                {isRefreshingStats ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Memuat...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh Statistik
                  </>
                )}
              </Button>
            </div>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            {config ? (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="h-5 w-5" />
                    Konfigurasi Crawling
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="crawl-algorithm">Algoritma Crawling</Label>
                    <Select
                      value={config.crawl_algorithm}
                      onValueChange={(value) =>
                        setConfig({
                          ...config,
                          crawl_algorithm: value,
                        })
                      }
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Pilih algoritma" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="BFS">
                          <div className="flex flex-col">
                            <span className="font-medium">BFS (Breadth-First Search)</span>
                            <span className="text-xs text-gray-500">Crawling melebar terlebih dahulu</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="DFS">
                          <div className="flex flex-col">
                            <span className="font-medium">DFS (Depth-First Search)</span>
                            <span className="text-xs text-gray-500">Crawling mendalam terlebih dahulu</span>
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-gray-500 mt-1">
                      {config.crawl_algorithm === "BFS"
                        ? "BFS akan mengeksplorasi semua halaman di level yang sama sebelum ke level berikutnya"
                        : "DFS akan mengeksplorasi sedalam mungkin sebelum backtrack ke cabang lain"}
                    </p>
                  </div>

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
            ) : (
              <Card>
                <CardContent className="pt-6 text-center">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
                  <p>Memuat konfigurasi...</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'
import PostGrid from '../components/PostGrid'
import StatsCards from '../components/StatsCards'
import PostDetailModal from '../components/PostDetailModal'

const Overview = () => {
  const location = useLocation()
  const { isAuthenticated } = useAuth()
  const [posts, setPosts] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    author: '',
    keyword: location.state?.search || '',
    group_id: '',
    date_from: '',
    date_to: '',
    sort_by: 'created_at',
    order: 'desc',
  })
  const [groups, setGroups] = useState([])
  const [exportLoading, setExportLoading] = useState(false)
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    pages: 0,
  })
  const [selectedPost, setSelectedPost] = useState(null)
  const [filtersOpen, setFiltersOpen] = useState(true)

  useEffect(() => {
    if (isAuthenticated) {
      fetchStats()
      fetchGroups()
    }
  }, [isAuthenticated])

  const fetchGroups = async () => {
    try {
      const response = await api.get('/groups')
      setGroups(response.data.groups || [])
    } catch (error) {
      console.error('Error fetching groups:', error)
    }
  }

  // Update filters when location state changes (from search)
  useEffect(() => {
    if (location.state?.search !== undefined && location.state.search !== filters.keyword) {
      setFilters(prev => ({ ...prev, keyword: location.state.search }))
      setPagination(prev => ({ ...prev, page: 1 }))
      setPosts([])
    }
  }, [location.state?.search])

  useEffect(() => {
    if (isAuthenticated) {
      fetchPosts()
    }
  }, [isAuthenticated, filters, pagination.page])

  const fetchPosts = async () => {
    try {
      setLoading(true)
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        ...filters,
      }
      
      Object.keys(params).forEach(key => {
        if (params[key] === '') {
          delete params[key]
        }
      })

      const response = await api.get('/posts', { params })
      const { posts: fetchedPosts, pagination: paginationData } = response.data
      
      if (pagination.page === 1) {
        setPosts(fetchedPosts)
      } else {
        setPosts(prev => [...prev, ...fetchedPosts])
      }
      
      setPagination(prev => ({
        ...prev,
        ...paginationData,
        page: paginationData.page || prev.page
      }))
    } catch (error) {
      console.error('Error fetching posts:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await api.get('/stats')
      setStats(response.data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters)
    setPagination(prev => ({ ...prev, page: 1 }))
    setPosts([])
  }

  const handleLoadMore = () => {
    if (pagination.page < pagination.pages && !loading) {
      setPagination(prev => ({ ...prev, page: prev.page + 1 }))
    }
  }

  const handlePostClick = (post) => {
    setSelectedPost(post)
  }

  const handleCloseModal = () => {
    setSelectedPost(null)
  }

  const handleExport = async (format) => {
    try {
      setExportLoading(true)
      const params = {
        format,
        ...filters,
      }
      
      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (params[key] === '') {
          delete params[key]
        }
      })

      const response = await api.get('/posts/export', {
        params,
        responseType: 'blob',
      })

      // Create blob URL and trigger download
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      
      const extension = format === 'xlsx' || format === 'xls' ? 'xlsx' : format
      link.download = `posts_export_${new Date().toISOString().split('T')[0]}.${extension}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export error:', error)
      alert('Failed to export data. Please try again.')
    } finally {
      setExportLoading(false)
    }
  }

  const handleFilterUpdate = (key, value) => {
    handleFilterChange({ ...filters, [key]: value })
  }

  const handleClearFilters = () => {
    handleFilterChange({
      author: '',
      keyword: '',
      group_id: '',
      date_from: '',
      date_to: '',
      sort_by: 'created_at',
      order: 'desc',
    })
  }

  return (
    <div className="h-full">
      <div className="h-full overflow-y-auto">
        <div className="p-4 md:p-6 lg:p-8">
          <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
            <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Overview</h1>
            
            <div className="flex items-center gap-3">
              {/* Export Buttons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleExport('json')}
                  disabled={exportLoading}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition font-medium text-sm disabled:opacity-50"
                  title="Export as JSON"
                >
                  {exportLoading ? 'Exporting...' : 'Export JSON'}
                </button>
                <button
                  onClick={() => handleExport('csv')}
                  disabled={exportLoading}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition font-medium text-sm disabled:opacity-50"
                  title="Export as CSV"
                >
                  CSV
                </button>
                <button
                  onClick={() => handleExport('xlsx')}
                  disabled={exportLoading}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition font-medium text-sm disabled:opacity-50"
                  title="Export as Excel"
                >
                  Excel
                </button>
              </div>
            </div>
          </div>

          {stats && <StatsCards stats={stats} />}
          
          {/* Inline Filters Section */}
          <div className="mb-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              {/* Filter Header with Toggle */}
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Filters</h2>
                <button
                  onClick={() => setFiltersOpen(!filtersOpen)}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition"
                >
                  <span>{filtersOpen ? 'Hide' : 'Show'} Filters</span>
                  <svg
                    className={`w-5 h-5 transition-transform ${filtersOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              </div>

              {/* Filter Controls */}
              {filtersOpen && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
                    {/* Sort By */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Sort By
                      </label>
                      <select
                        value={filters.sort_by}
                        onChange={(e) => handleFilterUpdate('sort_by', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                      >
                        <option value="created_at">Date</option>
                        <option value="reactions">Reactions</option>
                        <option value="comments">Comments</option>
                      </select>
                    </div>

                    {/* Order */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Order
                      </label>
                      <select
                        value={filters.order}
                        onChange={(e) => handleFilterUpdate('order', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                      >
                        <option value="desc">Descending</option>
                        <option value="asc">Ascending</option>
                      </select>
                    </div>

                    {/* Filter by Group */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Filter by Group
                      </label>
                      <select
                        value={filters.group_id || ''}
                        onChange={(e) => handleFilterUpdate('group_id', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                      >
                        <option value="">All Groups</option>
                        {groups.map((group) => (
                          <option key={group.group_id} value={group.group_id}>
                            {group.group_name || `Group ${group.group_id}`} ({group.post_count})
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Filter by Author */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Filter by Author
                      </label>
                      <input
                        type="text"
                        value={filters.author}
                        onChange={(e) => handleFilterUpdate('author', e.target.value)}
                        placeholder="Author name..."
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 text-sm"
                      />
                    </div>

                    {/* Date From */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Date From
                      </label>
                      <input
                        type="date"
                        value={filters.date_from}
                        onChange={(e) => handleFilterUpdate('date_from', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                      />
                    </div>

                    {/* Date To */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Date To
                      </label>
                      <input
                        type="date"
                        value={filters.date_to}
                        onChange={(e) => handleFilterUpdate('date_to', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                      />
                    </div>
                  </div>

                  {/* Clear Filters Button */}
                  <div className="flex justify-end">
                    <button
                      onClick={handleClearFilters}
                      className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg transition font-medium text-sm"
                    >
                      Clear Filters
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          <PostGrid
            posts={posts}
            loading={loading}
            onPostClick={handlePostClick}
            hasMore={pagination.page < pagination.pages}
            onLoadMore={handleLoadMore}
          />
        </div>
      </div>

      {selectedPost && (
        <PostDetailModal post={selectedPost} onClose={handleCloseModal} />
      )}
    </div>
  )
}

export default Overview


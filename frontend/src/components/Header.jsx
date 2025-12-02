import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

const Header = ({ onMenuClick }) => {
  const location = useLocation()
  const navigate = useNavigate()
  const [searchKeyword, setSearchKeyword] = useState('')

  const handleSearch = (e) => {
    e.preventDefault()
    // Navigate to overview with search keyword
    if (location.pathname !== '/dashboard') {
      navigate('/dashboard', { state: { search: searchKeyword } })
    } else {
      // If already on dashboard, update the location state to trigger filter update
      navigate('/dashboard', { state: { search: searchKeyword }, replace: true })
    }
  }

  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
      <div className="px-4 py-4 md:px-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={onMenuClick}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition"
              aria-label="Toggle menu"
            >
              <svg className="w-6 h-6 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            
            <h1 className="text-xl md:text-2xl font-bold text-gray-800 dark:text-gray-100">
              Facebook Media Aggregator
            </h1>
          </div>

          <div className="flex items-center space-x-4 flex-1 max-w-md mx-4">
            <form onSubmit={handleSearch} className="flex-1">
              <div className="relative">
                <input
                  type="text"
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  placeholder="Search posts..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400"
                />
                <svg
                  className="absolute left-3 top-2.5 w-5 h-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </form>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header

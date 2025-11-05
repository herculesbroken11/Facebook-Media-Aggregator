import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'
import ProfileSettings from '../components/settings/ProfileSettings'
import SecuritySettings from '../components/settings/SecuritySettings'
import OtherSettings from '../components/settings/OtherSettings'

const Settings = () => {
  const [activeTab, setActiveTab] = useState('profile')
  const { user } = useAuth()
  const [profileUser, setProfileUser] = useState(user)

  useEffect(() => {
    // Fetch latest profile data
    const fetchProfile = async () => {
      try {
        const response = await api.get('/profile')
        setProfileUser(response.data)
      } catch (error) {
        console.error('Error fetching profile:', error)
      }
    }
    fetchProfile()
  }, [])

  const tabs = [
    { id: 'profile', label: 'Profile' },
    { id: 'security', label: 'Security' },
    { id: 'others', label: 'Others' },
  ]

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 md:p-6 lg:p-8">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">Settings</h1>

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
          <nav className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm transition
                  ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
                  }
                `}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="max-w-4xl">
          {activeTab === 'profile' && <ProfileSettings user={profileUser || user} />}
          {activeTab === 'security' && <SecuritySettings user={profileUser || user} />}
          {activeTab === 'others' && <OtherSettings user={profileUser || user} />}
        </div>
      </div>
    </div>
  )
}

export default Settings


import { useState, useEffect } from 'react'
import { useTheme } from '../../context/ThemeContext'

const OtherSettings = ({ user }) => {
  const { darkMode, toggleDarkMode } = useTheme()
  const [settings, setSettings] = useState({
    notifications: true,
    emailAlerts: false,
  })

  const handleToggle = (key) => {
    if (key === 'darkMode') {
      toggleDarkMode()
    } else {
      setSettings({ ...settings, [key]: !settings[key] })
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-6">Other Settings</h2>
      
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-gray-800 dark:text-gray-200">Email Notifications</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">Receive email alerts for new posts</p>
          </div>
          <button
            onClick={() => handleToggle('emailAlerts')}
            className={`
              relative inline-flex h-6 w-11 items-center rounded-full transition
              ${settings.emailAlerts ? 'bg-primary-600' : 'bg-gray-300'}
            `}
          >
            <span
              className={`
                inline-block h-4 w-4 transform rounded-full bg-white transition
                ${settings.emailAlerts ? 'translate-x-6' : 'translate-x-1'}
              `}
            />
          </button>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-gray-800 dark:text-gray-200">Push Notifications</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">Enable browser notifications</p>
          </div>
          <button
            onClick={() => handleToggle('notifications')}
            className={`
              relative inline-flex h-6 w-11 items-center rounded-full transition
              ${settings.notifications ? 'bg-primary-600' : 'bg-gray-300'}
            `}
          >
            <span
              className={`
                inline-block h-4 w-4 transform rounded-full bg-white transition
                ${settings.notifications ? 'translate-x-6' : 'translate-x-1'}
              `}
            />
          </button>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-gray-800 dark:text-gray-200">Dark Mode</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">Switch to dark theme</p>
          </div>
          <button
            onClick={() => handleToggle('darkMode')}
            className={`
              relative inline-flex h-6 w-11 items-center rounded-full transition
              ${darkMode ? 'bg-primary-600' : 'bg-gray-300'}
            `}
          >
            <span
              className={`
                inline-block h-4 w-4 transform rounded-full bg-white transition
                ${darkMode ? 'translate-x-6' : 'translate-x-1'}
              `}
            />
          </button>
        </div>
      </div>
    </div>
  )
}

export default OtherSettings


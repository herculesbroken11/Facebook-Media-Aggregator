const StatsCards = ({ stats }) => {
  const statItems = [
    {
      label: 'Total Posts',
      value: stats.total_posts?.toLocaleString() || '0',
      icon: '📊',
      color: 'bg-blue-500',
    },
    {
      label: 'Total Reactions',
      value: stats.total_reactions?.toLocaleString() || '0',
      icon: '👍',
      color: 'bg-green-500',
    },
    {
      label: 'Total Comments',
      value: stats.total_comments?.toLocaleString() || '0',
      icon: '💬',
      color: 'bg-yellow-500',
    },
    {
      label: 'Total Shares',
      value: stats.total_shares?.toLocaleString() || '0',
      icon: '🔁',
      color: 'bg-purple-500',
    },
    {
      label: 'Unique Authors',
      value: stats.total_authors?.toLocaleString() || '0',
      icon: '👥',
      color: 'bg-indigo-500',
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      {statItems.map((item, index) => (
        <div
          key={index}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border border-gray-200 dark:border-gray-700 hover:shadow-lg transition"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{item.label}</p>
              <p className="text-2xl font-bold text-gray-800 dark:text-gray-100">{item.value}</p>
            </div>
            <div className={`${item.color} p-3 rounded-full text-2xl`}>
              {item.icon}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default StatsCards


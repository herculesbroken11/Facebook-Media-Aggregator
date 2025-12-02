import { useState } from 'react'

const PostCard = ({ post, onClick }) => {
  const [imageError, setImageError] = useState(false)

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const formatDateTime = (dateString) => {
    if (!dateString) return 'Unknown date'
    const date = new Date(dateString)
    const dateStr = date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
    const timeStr = date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    })
    return `${dateStr} at ${timeStr}`
  }

  return (
    <div
      onClick={onClick}
      className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden hover:shadow-xl transition cursor-pointer border border-gray-200 dark:border-gray-700 flex flex-col"
    >
      {/* Media - Image or Video */}
      {post.content_type === 'video' && post.video_urls && post.video_urls.length > 0 ? (
        <div className="relative h-48 bg-gray-200 dark:bg-gray-700 overflow-hidden">
          <video
            src={post.video_urls[0]}
            className="w-full h-full object-cover"
            controls
            muted
            playsInline
            onError={() => setImageError(true)}
            loading="lazy"
          />
          <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-xs">
            ▶ Video
          </div>
        </div>
      ) : post.media_url && !imageError ? (
        <div className="relative h-48 bg-gray-200 dark:bg-gray-700 overflow-hidden">
          <img
            src={post.media_url}
            alt={post.content?.substring(0, 50) || 'Post image'}
            className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
            onError={() => setImageError(true)}
            loading="lazy"
          />
        </div>
      ) : (
        <div className="h-48 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center">
          <span className="text-4xl text-gray-400 dark:text-gray-500">
            {post.content_type === 'video' ? '🎥' : '📷'}
          </span>
        </div>
      )}

      {/* Content */}
      <div className="p-4 flex-1 flex flex-col">
        {/* Author */}
        {post.author && (
          <a
            href={post.author_url || '#'}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-semibold mb-2 text-sm"
          >
            {post.author}
          </a>
        )}

        {/* Post Text */}
        <p className="text-gray-700 dark:text-gray-300 mb-3 line-clamp-3 flex-1">
          {post.content || 'No content available'}
        </p>

        {/* Engagement Metrics */}
        <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-2">
          <div className="flex items-center space-x-4">
            {post.reactions !== null && (
              <span className="flex items-center">
                <span className="mr-1">👍</span>
                {post.reactions || 0}
              </span>
            )}
            {post.comments !== null && (
              <span className="flex items-center">
                <span className="mr-1">💬</span>
                {post.comments || 0}
              </span>
            )}
            {post.shares !== null && (
              <span className="flex items-center">
                <span className="mr-1">🔁</span>
                {post.shares || 0}
              </span>
            )}
          </div>
        </div>

        {/* Date and Time */}
        <p className="text-xs text-gray-400 dark:text-gray-500">
          {formatDateTime(post.created_at)}
        </p>
      </div>
    </div>
  )
}

export default PostCard


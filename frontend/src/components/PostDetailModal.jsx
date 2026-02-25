import { useState } from 'react'
import { getImageSrc } from '../utils/imageUrl'

const PostDetailModal = ({ post, onClose }) => {
  const [imageError, setImageError] = useState(false)

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (!post) return null

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Post Details</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition"
            >
              <svg className="w-6 h-6 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Media - Images or Videos */}
          {post.content_type === 'video' && post.video_urls && post.video_urls.length > 0 ? (
            <div className="mb-6 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700">
              <video
                src={post.video_urls[0]}
                className="w-full h-auto max-h-96 object-contain"
                controls
                autoPlay={false}
                onError={() => setImageError(true)}
              />
              {post.video_urls.length > 1 && (
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400 px-4">
                  {post.video_urls.length} video{post.video_urls.length > 1 ? 's' : ''} available
                </p>
              )}
            </div>
          ) : post.image_urls && post.image_urls.length > 0 ? (
            <div className="mb-6">
              {post.image_urls.map((url, index) => (
                <div key={index} className="mb-4 rounded-lg overflow-hidden">
                  <img
                    src={getImageSrc(url)}
                    alt={`Post image ${index + 1}`}
                    className="w-full h-auto max-h-96 object-contain bg-gray-100 dark:bg-gray-700"
                    onError={() => setImageError(true)}
                    referrerPolicy="no-referrer"
                  />
                </div>
              ))}
            </div>
          ) : post.media_url && !imageError ? (
            <div className="mb-6 rounded-lg overflow-hidden">
              <img
                src={getImageSrc(post.media_url)}
                alt={post.content?.substring(0, 50) || 'Post image'}
                className="w-full h-auto max-h-96 object-contain bg-gray-100 dark:bg-gray-700"
                onError={() => setImageError(true)}
                referrerPolicy="no-referrer"
              />
            </div>
          ) : null}

          {/* Author */}
          {post.author && (
            <div className="mb-4">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Author</p>
              <a
                href={post.author_url || '#'}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-semibold text-lg"
              >
                {post.author}
              </a>
            </div>
          )}

          {/* Post Content */}
          <div className="mb-6">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Content</p>
            <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
              {post.content || 'No content available'}
            </p>
          </div>

          {/* Engagement Metrics */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{post.reactions || 0}</p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Reactions</p>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">{post.comments || 0}</p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Comments</p>
            </div>
            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{post.shares || 0}</p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Shares</p>
            </div>
          </div>

          {/* Date */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Posted on</p>
            <p className="text-gray-700 dark:text-gray-300">{formatDate(post.created_at)}</p>
          </div>

          {/* Post Link */}
          {post.post_id && (
            <div className="mt-4">
              <a
                href={post.post_id}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium"
              >
                <span className="mr-2">🔗</span>
                View on Facebook
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default PostDetailModal


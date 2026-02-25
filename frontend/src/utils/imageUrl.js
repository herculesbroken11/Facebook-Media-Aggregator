/**
 * Facebook CDN often blocks images when loaded from other origins (referrer/CORS).
 * Use the backend image proxy for Facebook URLs so images load reliably.
 */
const FACEBOOK_HOSTS = ['facebook.com', 'fbcdn.net', 'fbcdn.', 'scontent.']

function isFacebookCdnUrl(url) {
  if (!url || typeof url !== 'string') return false
  const lower = url.toLowerCase()
  return FACEBOOK_HOSTS.some(h => lower.includes(h))
}

/**
 * Returns the URL to use for an image. For Facebook CDN URLs, returns the proxy URL.
 * @param {string} url - Original image URL
 * @returns {string} - URL to use in img src (proxy URL for Facebook, otherwise original)
 */
export function getImageSrc(url) {
  if (!url) return url
  if (isFacebookCdnUrl(url)) {
    return `/api/image-proxy?url=${encodeURIComponent(url)}`
  }
  return url
}

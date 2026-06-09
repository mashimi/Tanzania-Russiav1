/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow API calls to the FastAPI backend
  async rewrites() {
    return [];
  },
};

module.exports = nextConfig;

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // Environment variables
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'PGwallah',
  },

  // Image optimization
  images: {
    domains: [
      'localhost',
      'minio',
      's3.amazonaws.com',
      // Add your CDN domains here
    ],
    formats: ['image/webp', 'image/avif'],
  },

  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },

  // Redirects
  async redirects() {
    return [
      {
        source: '/dashboard',
        destination: '/tenant/dashboard',
        permanent: false,
        has: [
          {
            type: 'cookie',
            key: 'user_role',
            value: 'tenant',
          },
        ],
      },
      {
        source: '/dashboard',
        destination: '/admin/dashboard',
        permanent: false,
        has: [
          {
            type: 'cookie',
            key: 'user_role',
            value: 'admin',
          },
        ],
      },
    ];
  },

  // Experimental features
  experimental: {
    // Enable if you want to use app directory
    // appDir: true,

    // Server components
    serverComponentsExternalPackages: ['axios'],
  },

  // Bundle analyzer
  ...(process.env.ANALYZE === 'true' && {
    webpack: (config, { isServer }) => {
      if (!isServer) {
        const { BundleAnalyzerPlugin } = require('@next/bundle-analyzer')({
          enabled: true,
        });
        config.plugins.push(new BundleAnalyzerPlugin());
      }
      return config;
    },
  }),

  // Custom webpack config
  webpack: (config, { dev, isServer }) => {
    // Production optimizations can be added here if needed
    return config;
  },

  // Output configuration
  output: process.env.NODE_ENV === 'production' ? 'standalone' : undefined,

  // Trailing slash
  trailingSlash: false,

  // Power by header
  poweredByHeader: false,

  // Compress
  compress: true,
};

module.exports = nextConfig;
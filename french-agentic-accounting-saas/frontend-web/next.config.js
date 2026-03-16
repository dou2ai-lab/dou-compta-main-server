// -----------------------------------------------------------------------------
// File: next.config.js
// Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
// Created On: 21-11-2025
// Description: Next.js configuration for the web application
// -----------------------------------------------------------------------------

/** @type {import('next').NextConfig} */
const path = require('path')

const nextConfig = {
  reactStrictMode: true,
  turbopack: {
    root: __dirname,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
  },
  images: {
    domains: [],
  },
  compress: true,
  poweredByHeader: false,
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production' ? { exclude: ['error', 'warn'] } : false,
  },
}

module.exports = nextConfig










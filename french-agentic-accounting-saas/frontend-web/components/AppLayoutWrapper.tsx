'use client'

import { usePathname } from 'next/navigation'
import Layout from '@/components/Layout'

const NO_LAYOUT_PATHS = ['/', '/login', '/signup', '/forgot-password', '/reset-password', '/legal', '/contact', '/pricing', '/security']

export default function AppLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const skipLayout = pathname && NO_LAYOUT_PATHS.some((p) => pathname === p || pathname.startsWith(p + '/'))

  if (skipLayout) {
    return <>{children}</>
  }

  return <Layout>{children}</Layout>
}

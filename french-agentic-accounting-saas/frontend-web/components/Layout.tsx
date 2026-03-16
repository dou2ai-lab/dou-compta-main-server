'use client'

import { ReactNode } from 'react'
import Sidebar from './Sidebar'
import Header from './Header'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="flex min-h-screen bg-bgPage">
      <Sidebar />
      <div className="ml-[260px] flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 p-8 min-w-0 overflow-x-auto">{children}</main>
      </div>
    </div>
  )
}

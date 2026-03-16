'use client'

import { useState, useEffect, useRef } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faSearch, faChevronRight, faChevronDown, faRightFromBracket } from '@fortawesome/free-solid-svg-icons'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useLanguage } from '@/contexts/LanguageContext'
import { useAuth } from '@/contexts/AuthContext'
import LanguageSwitcher from '@/components/LanguageSwitcher'
import NotificationBell from '@/components/NotificationBell'

interface BreadcrumbItem {
  label: string
  href?: string
}

function getBreadcrumbs(pathname: string, t: (key: string) => string): BreadcrumbItem[] {
  if (pathname === '/dashboard' || pathname === '/') {
    return [{ label: t('common.home') }, { label: t('common.dashboard') }]
  }

  const segments = pathname.split('/').filter(Boolean)
  const breadcrumbs: BreadcrumbItem[] = [{ label: t('common.home'), href: '/dashboard' }]

  let currentPath = ''
  segments.forEach((segment, index) => {
    currentPath += `/${segment}`
    const isLast = index === segments.length - 1
    const routeKey = `routes.${segment}`
    const translated = t(routeKey)
    breadcrumbs.push({
      label: translated !== routeKey ? translated : segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' '),
      href: isLast ? undefined : currentPath,
    })
  })

  return breadcrumbs
}

export default function Header() {
  const pathname = usePathname()
  const router = useRouter()
  const { t } = useLanguage()
  const { logout, user } = useAuth()
  const breadcrumbs = getBreadcrumbs(pathname || '/', t)
  const [searchMounted, setSearchMounted] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const userMenuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setSearchMounted(true)
  }, [])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const displayName =
    (user?.first_name || user?.last_name)
      ? `${user?.first_name ?? ''} ${user?.last_name ?? ''}`.trim()
      : user?.email ?? 'User'

  const handleLogout = async () => {
    setUserMenuOpen(false)
    await logout()
    router.push('/login')
  }

  return (
    <header className="h-16 bg-surface border-b border-borderColor sticky top-0 z-30">
      <div className="h-full px-8 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-sm">
          {breadcrumbs.map((crumb, index) => (
            <div key={index} className="flex items-center space-x-2">
              {crumb.href ? (
                <Link href={crumb.href} className="text-textSecondary hover:text-textPrimary">
                  {crumb.label}
                </Link>
              ) : (
                <span className="text-textPrimary font-medium">{crumb.label}</span>
              )}
              {index < breadcrumbs.length - 1 && (
                <FontAwesomeIcon icon={faChevronRight} className="text-textMuted text-xs" />
              )}
            </div>
          ))}
        </div>

        <div className="flex-1 max-w-[500px] mx-8">
          {searchMounted && (
            <div className="relative">
              <FontAwesomeIcon
                icon={faSearch}
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-textMuted text-sm w-4"
              />
              <input
                type="text"
                placeholder={t('header.searchPlaceholder')}
                className="w-full h-10 pl-10 pr-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          )}
        </div>

        <div className="flex items-center space-x-4">
          <NotificationBell />

          <LanguageSwitcher variant="header" />

          <div className="relative pl-4 border-l border-borderColor" ref={userMenuRef}>
            <button
              type="button"
              onClick={() => setUserMenuOpen((o) => !o)}
              className="flex items-center space-x-3 rounded-lg hover:bg-gray-50 px-2 py-1.5 -ml-2 transition-colors"
              aria-expanded={userMenuOpen}
              aria-haspopup="true"
            >
              <img
                src="https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-2.jpg"
                alt="User"
                className="w-8 h-8 rounded-full"
              />
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-textPrimary max-w-[140px] truncate">
                  {displayName}
                </span>
                <FontAwesomeIcon icon={faChevronDown} className={`text-xs text-textMuted transition-transform ${userMenuOpen ? 'rotate-180' : ''}`} />
              </div>
            </button>
            {userMenuOpen && (
              <div className="absolute right-0 top-full mt-1 py-1 bg-surface border border-borderColor rounded-lg shadow-lg min-w-[180px] z-[9999]">
                <div className="px-4 pb-2 border-b border-borderColor">
                  <div className="text-sm font-medium text-textPrimary truncate">{displayName}</div>
                  {user?.email && (
                    <div className="text-xs text-textSecondary truncate">{user.email}</div>
                  )}
                </div>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full flex items-center space-x-2 px-4 py-2.5 text-left text-sm text-textPrimary hover:bg-gray-50 rounded-lg transition-colors"
                >
                  <FontAwesomeIcon icon={faRightFromBracket} className="text-textMuted w-4" />
                  <span>{t('header.logout')}</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}

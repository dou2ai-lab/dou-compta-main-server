'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faHome,
  faReceipt,
  faFileText,
  faCheckSquare,
  faArrowUp,
  faExclamationTriangle,
  faClipboardCheck,
  faComments,
  faUsers,
  faShieldAlt,
  faFolderTree,
  faPlug,
  faCog,
  faEllipsisV,
  faCalculator,
  faBriefcase,
  faUniversity,
  faFileInvoiceDollar,
  faFileInvoice,
  faMoneyBillWave,
  faInbox,
  faRobot,
} from '@fortawesome/free-solid-svg-icons'
import { useLanguage } from '@/contexts/LanguageContext'

interface NavItem {
  href: string
  icon: any
  labelKey: string
  badge?: number
  badgeColor?: string
}

interface NavSection {
  titleKey?: string
  items: NavItem[]
}

const navigation: NavSection[] = [
  {
    items: [
      { href: '/dashboard', icon: faHome, labelKey: 'sidebar.dashboard' },
      { href: '/expenses', icon: faReceipt, labelKey: 'sidebar.expenses' },
      { href: '/reports', icon: faFileText, labelKey: 'sidebar.reports' },
      { href: '/approvals', icon: faCheckSquare, labelKey: 'sidebar.approvals' },
    ],
  },
  {
    titleKey: 'sidebar.accounting',
    items: [
      { href: '/accounting', icon: faCalculator, labelKey: 'sidebar.accounting' },
      { href: '/dossiers', icon: faBriefcase, labelKey: 'sidebar.dossiers' },
      { href: '/banking', icon: faUniversity, labelKey: 'sidebar.banking' },
      { href: '/tax', icon: faFileInvoiceDollar, labelKey: 'sidebar.tax' },
      { href: '/analysis', icon: faArrowUp, labelKey: 'sidebar.analysis' },
      { href: '/invoices', icon: faFileInvoice, labelKey: 'sidebar.invoices' },
      { href: '/payroll', icon: faMoneyBillWave, labelKey: 'sidebar.payroll' },
      { href: '/documents', icon: faInbox, labelKey: 'sidebar.documents' },
      { href: '/agents', icon: faRobot, labelKey: 'sidebar.agents' },
    ],
  },
  {
    titleKey: 'sidebar.financeAudit',
    items: [
      { href: '/finance', icon: faArrowUp, labelKey: 'sidebar.financeDashboard' },
      { href: '/anomalies', icon: faExclamationTriangle, labelKey: 'sidebar.anomalies' },
      { href: '/audit/reports', icon: faClipboardCheck, labelKey: 'sidebar.auditReports' },
      { href: '/audit/qa', icon: faComments, labelKey: 'sidebar.auditCoPilot' },
    ],
  },
  {
    titleKey: 'sidebar.administration',
    items: [
      { href: '/admin/users', icon: faUsers, labelKey: 'sidebar.usersRoles' },
      { href: '/admin/policies', icon: faShieldAlt, labelKey: 'sidebar.policies' },
      { href: '/admin/categories', icon: faFolderTree, labelKey: 'sidebar.categoriesGL' },
      { href: '/admin/integrations', icon: faPlug, labelKey: 'sidebar.integrations' },
      { href: '/settings', icon: faCog, labelKey: 'sidebar.settings' },
    ],
  },
]

export default function Sidebar() {
  const pathname = usePathname()
  const { t } = useLanguage()

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === '/dashboard' || pathname === '/'
    }
    return pathname?.startsWith(href)
  }

  return (
    <div className="fixed top-0 left-0 h-full w-[260px] bg-surface border-r border-borderColor flex flex-col z-40">
      <div className="h-[60px] flex items-center px-6 border-b border-borderColor">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <FontAwesomeIcon icon={faReceipt} className="text-white text-sm" />
          </div>
          <span className="text-lg font-semibold text-textPrimary">Dou</span>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto py-4">
        {navigation.map((section, sectionIndex) => (
          <div key={sectionIndex} className={sectionIndex > 0 ? 'mt-6' : ''}>
            {section.titleKey && (
              <div className="px-3 mb-3">
                <span className="text-xs font-semibold text-textMuted uppercase tracking-wide">{t(section.titleKey)}</span>
              </div>
            )}
            <div className="px-3 mb-6">
              {section.items.map((item) => {
                const active = isActive(item.href)
                return (
                  <div key={item.href} className="mb-2">
                    <Link
                      href={item.href}
                      className={`flex items-center h-[44px] px-3 rounded-lg transition-colors ${
                        active
                          ? 'bg-indigo-50 text-primary border-l-[3px] border-primary'
                          : 'text-textSecondary hover:bg-gray-50'
                      } ${item.badge ? 'justify-between' : ''}`}
                    >
                      <div className="flex items-center">
                        <FontAwesomeIcon icon={item.icon} className="w-5 mr-3" />
                        <span className="text-sm font-medium">{t(item.labelKey)}</span>
                      </div>
                      {item.badge && (
                        <span
                          className={`badge-count bg-${item.badgeColor || 'errorRed'} text-white rounded-full px-2`}
                        >
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  </div>
                )
              })}
            </div>
            {sectionIndex < navigation.length - 1 && <div className="h-px bg-borderColor mx-3 my-4" />}
          </div>
        ))}
      </nav>

      <div className="border-t border-borderColor p-4">
        <div className="flex items-center space-x-3">
          <img
            src="https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-2.jpg"
            alt="User Avatar"
            className="w-10 h-10 rounded-full"
          />
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-textPrimary truncate">Jean Dupont</div>
            <div className="text-xs text-textSecondary truncate">{t('sidebar.financeManager')}</div>
          </div>
          <button className="text-textMuted hover:text-textSecondary">
            <FontAwesomeIcon icon={faEllipsisV} />
          </button>
        </div>
      </div>
    </div>
  )
}

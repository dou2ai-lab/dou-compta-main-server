'use client'

import { useState } from 'react'
import Badge from '@/components/ui/Badge'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faBell,
  faCheckCircle,
  faExclamationTriangle,
  faInfoCircle,
  faTimes,
  faCheck,
  faTrash,
  faFilter,
  faSearch,
} from '@fortawesome/free-solid-svg-icons'

export default function NotificationsPage() {
  const [activeFilter, setActiveFilter] = useState('all')

  const notifications = [
    {
      id: 1,
      type: 'approval',
      title: 'New expense approval required',
      message: 'Marie Laurent submitted an expense report for €1,247.50',
      time: '2 minutes ago',
      read: false,
      icon: faCheckCircle,
      variant: 'info' as const,
    },
    {
      id: 2,
      type: 'warning',
      title: 'Policy violation detected',
      message: 'Expense exceeds daily meal limit by €45',
      time: '1 hour ago',
      read: false,
      icon: faExclamationTriangle,
      variant: 'warning' as const,
    },
    {
      id: 3,
      type: 'success',
      title: 'Expense approved',
      message: 'Your expense report for €456.80 has been approved',
      time: '3 hours ago',
      read: true,
      icon: faCheckCircle,
      variant: 'success' as const,
    },
    {
      id: 4,
      type: 'info',
      title: 'System update',
      message: 'New features available in the Finance Dashboard',
      time: '1 day ago',
      read: true,
      icon: faInfoCircle,
      variant: 'info' as const,
    },
  ]

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">Notifications Center</h1>
            <p className="text-textSecondary">View and manage all your notifications</p>
          </div>
          <div className="flex items-center space-x-3">
            <button className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
              <FontAwesomeIcon icon={faFilter} />
              <span>Filter</span>
            </button>
            <button className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">
              Mark All Read
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={() => setActiveFilter('all')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              activeFilter === 'all'
                ? 'bg-primary text-white'
                : 'text-textSecondary hover:bg-gray-50'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setActiveFilter('unread')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              activeFilter === 'unread'
                ? 'bg-primary text-white'
                : 'text-textSecondary hover:bg-gray-50'
            }`}
          >
            Unread
          </button>
          <button
            onClick={() => setActiveFilter('approvals')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              activeFilter === 'approvals'
                ? 'bg-primary text-white'
                : 'text-textSecondary hover:bg-gray-50'
            }`}
          >
            Approvals
          </button>
          <button
            onClick={() => setActiveFilter('alerts')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              activeFilter === 'alerts'
                ? 'bg-primary text-white'
                : 'text-textSecondary hover:bg-gray-50'
            }`}
          >
            Alerts
          </button>
        </div>
      </section>

      <section className="bg-surface rounded-xl border border-borderColor shadow-sm">
        <div className="p-6 border-b border-borderColor">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-textPrimary mb-1">Notifications</h2>
              <p className="text-sm text-textSecondary">Manage your notification preferences</p>
            </div>
            <div className="relative">
              <FontAwesomeIcon
                icon={faSearch}
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-textMuted"
              />
              <input
                type="text"
                placeholder="Search notifications..."
                className="h-10 pl-10 pr-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </div>
        </div>

        <div className="divide-y divide-borderColor">
          {notifications.map((notification) => (
            <div
              key={notification.id}
              className={`p-6 hover:bg-gray-50 transition-colors ${
                !notification.read ? 'bg-indigo-50' : ''
              }`}
            >
              <div className="flex items-start space-x-4">
                <div
                  className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    notification.variant === 'success'
                      ? 'bg-green-50'
                      : notification.variant === 'warning'
                        ? 'bg-amber-50'
                        : 'bg-blue-50'
                  }`}
                >
                  <FontAwesomeIcon
                    icon={notification.icon}
                    className={`${
                      notification.variant === 'success'
                        ? 'text-successGreen'
                        : notification.variant === 'warning'
                          ? 'text-warningAmber'
                          : 'text-infoBlue'
                    }`}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between mb-1">
                    <div>
                      <h3 className="text-sm font-semibold text-textPrimary mb-1">{notification.title}</h3>
                      <p className="text-sm text-textSecondary">{notification.message}</p>
                    </div>
                    {!notification.read && (
                      <span className="w-2 h-2 bg-primary rounded-full flex-shrink-0 mt-2"></span>
                    )}
                  </div>
                  <div className="flex items-center justify-between mt-3">
                    <span className="text-xs text-textMuted">{notification.time}</span>
                    <div className="flex items-center space-x-2">
                      {!notification.read && (
                        <button className="text-xs text-primary hover:text-primaryHover font-medium">
                          Mark as read
                        </button>
                      )}
                      <button className="w-8 h-8 flex items-center justify-center text-textSecondary hover:text-errorRed hover:bg-red-50 rounded-lg">
                        <FontAwesomeIcon icon={faTrash} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
  )
}

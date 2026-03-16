'use client'

import { useState, useEffect, useRef } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faBell, faCheck, faCheckDouble } from '@fortawesome/free-solid-svg-icons'
import { notificationAPI } from '@/lib/api'

const PRIORITY_COLORS: Record<string, string> = {
  urgent: 'border-l-red-500',
  high: 'border-l-orange-500',
  normal: 'border-l-blue-500',
  low: 'border-l-gray-300',
}

export default function NotificationBell() {
  const [open, setOpen] = useState(false)
  const [notifications, setNotifications] = useState<any[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadUnreadCount()
    const interval = setInterval(loadUnreadCount, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (open) loadNotifications()
  }, [open])

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  async function loadUnreadCount() {
    try {
      const res = await notificationAPI.getUnreadCount()
      setUnreadCount(res.unread_count || 0)
    } catch { /* ignore */ }
  }

  async function loadNotifications() {
    try {
      const res = await notificationAPI.list({ page_size: 10 })
      setNotifications(res.data || [])
      setUnreadCount(res.unread_count || 0)
    } catch { /* ignore */ }
  }

  async function handleMarkRead(id: string) {
    try {
      await notificationAPI.markRead(id)
      loadNotifications()
    } catch { /* ignore */ }
  }

  async function handleMarkAllRead() {
    try {
      await notificationAPI.markAllRead()
      loadNotifications()
    } catch { /* ignore */ }
  }

  return (
    <div className="relative" ref={ref}>
      <button onClick={() => setOpen(!open)} className="relative p-2 text-textSecondary hover:text-textPrimary">
        <FontAwesomeIcon icon={faBell} className="text-lg" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-96 bg-white rounded-xl border border-borderColor shadow-lg z-50 max-h-[500px] overflow-hidden flex flex-col">
          <div className="flex items-center justify-between px-4 py-3 border-b border-borderColor">
            <h3 className="font-semibold text-sm">Notifications</h3>
            {unreadCount > 0 && (
              <button onClick={handleMarkAllRead} className="text-xs text-primary hover:underline flex items-center gap-1">
                <FontAwesomeIcon icon={faCheckDouble} /> Tout marquer lu
              </button>
            )}
          </div>
          <div className="overflow-y-auto flex-1">
            {notifications.length === 0 ? (
              <div className="text-center py-8 text-sm text-textSecondary">Aucune notification</div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`px-4 py-3 border-b border-borderColor border-l-4 ${PRIORITY_COLORS[n.priority] || PRIORITY_COLORS.normal} ${n.status === 'unread' ? 'bg-blue-50/50' : ''} hover:bg-gray-50`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm ${n.status === 'unread' ? 'font-semibold' : ''} text-textPrimary`}>{n.title}</p>
                      {n.body && <p className="text-xs text-textSecondary mt-0.5 truncate">{n.body}</p>}
                      <p className="text-xs text-textMuted mt-1">{new Date(n.created_at).toLocaleString('fr-FR')}</p>
                    </div>
                    {n.status === 'unread' && (
                      <button onClick={() => handleMarkRead(n.id)} className="ml-2 text-textMuted hover:text-primary shrink-0" title="Marquer comme lu">
                        <FontAwesomeIcon icon={faCheck} className="text-xs" />
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

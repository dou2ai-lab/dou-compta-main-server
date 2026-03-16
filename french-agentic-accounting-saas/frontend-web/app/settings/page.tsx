'use client'

import { useState, useEffect, useCallback } from 'react'
import Badge from '@/components/ui/Badge'
import { useLanguage } from '@/contexts/LanguageContext'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faCog,
  faBuilding,
  faUsers,
  faShieldAlt,
  faBell,
  faFileAlt,
  faSave,
  faHistory,
  faTimes,
  faSpinner,
} from '@fortawesome/free-solid-svg-icons'
import { adminAPI } from '@/lib/api'
import { getAuthErrorMessage } from '@/lib/api'

type SettingsState = {
  general: {
    company_name: string
    company_address: string
    tax_id_siret: string
    vat_number: string
    default_currency: string
  }
  users: {
    default_user_role: string
    require_email_verification: boolean
  }
  security: {
    two_factor_enabled: boolean
    session_timeout_minutes: number
  }
  notifications: {
    email_approvals: boolean
    push_mobile: boolean
  }
  billing: {
    billing_email: string
    plan: string
    plan_details: string
  }
}

const defaultSettings: SettingsState = {
  general: {
    company_name: 'Dou France SAS',
    company_address: '123 Rue de la République, 75001 Paris, France',
    tax_id_siret: '123 456 789 00012',
    vat_number: 'FR12 345678901',
    default_currency: 'EUR',
  },
  users: {
    default_user_role: 'Employee',
    require_email_verification: true,
  },
  security: {
    two_factor_enabled: true,
    session_timeout_minutes: 30,
  },
  notifications: {
    email_approvals: true,
    push_mobile: true,
  },
  billing: {
    billing_email: 'billing@company.com',
    plan: 'Professional',
    plan_details: '€99/month • 50 users',
  },
}

type ChangelogEntry = {
  id: string
  changed_at: string
  section: string
  action: string
  changed_by_email?: string
  old_value?: Record<string, unknown>
  new_value?: Record<string, unknown>
}

export default function SettingsPage() {
  const { t, localeVersion } = useLanguage()
  void localeVersion
  const [activeTab, setActiveTab] = useState('general')
  const [settings, setSettings] = useState<SettingsState>(defaultSettings)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [changelogOpen, setChangelogOpen] = useState(false)
  const [changelog, setChangelog] = useState<ChangelogEntry[]>([])
  const [changelogLoading, setChangelogLoading] = useState(false)

  const loadSettings = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await adminAPI.getSettings()
      const s = data?.settings ?? data
      if (s && typeof s === 'object') {
        setSettings({
          general: { ...defaultSettings.general, ...s.general },
          users: { ...defaultSettings.users, ...s.users },
          security: { ...defaultSettings.security, ...s.security },
          notifications: { ...defaultSettings.notifications, ...s.notifications },
          billing: { ...defaultSettings.billing, ...s.billing },
        })
      }
    } catch (err) {
      setError(getAuthErrorMessage(err, 'Failed to load settings'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSettings()
  }, [loadSettings])

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setSuccess(null)
    try {
      await adminAPI.updateSettings({
        general: settings.general,
        users: settings.users,
        security: settings.security,
        notifications: settings.notifications,
        billing: settings.billing,
      })
      setSuccess('Settings saved successfully.')
      loadSettings()
    } catch (err) {
      setError(getAuthErrorMessage(err, 'Failed to save settings'))
    } finally {
      setSaving(false)
    }
  }

  const handleViewChangelog = async () => {
    setChangelogOpen(true)
    setChangelogLoading(true)
    try {
      const entries = await adminAPI.getSettingsChangelog({ page: 1, page_size: 50 })
      setChangelog(Array.isArray(entries) ? entries : [])
    } catch (err) {
      setChangelog([])
    } finally {
      setChangelogLoading(false)
    }
  }

  const updateGeneral = (key: keyof SettingsState['general'], value: string) => {
    setSettings((prev) => ({ ...prev, general: { ...prev.general, [key]: value } }))
  }
  const updateUsers = (key: keyof SettingsState['users'], value: string | boolean) => {
    setSettings((prev) => ({ ...prev, users: { ...prev.users, [key]: value } }))
  }
  const updateSecurity = (key: keyof SettingsState['security'], value: boolean | number) => {
    setSettings((prev) => ({ ...prev, security: { ...prev.security, [key]: value } }))
  }
  const updateNotifications = (key: keyof SettingsState['notifications'], value: boolean) => {
    setSettings((prev) => ({ ...prev, notifications: { ...prev.notifications, [key]: value } }))
  }
  const updateBilling = (key: keyof SettingsState['billing'], value: string) => {
    setSettings((prev) => ({ ...prev, billing: { ...prev.billing, [key]: value } }))
  }

  const tabs = [
    { id: 'general', nameKey: 'settings.general' as const, icon: faBuilding },
    { id: 'users', nameKey: 'settings.usersPermissions' as const, icon: faUsers },
    { id: 'security', nameKey: 'settings.security' as const, icon: faShieldAlt },
    { id: 'notifications', nameKey: 'settings.notifications' as const, icon: faBell },
    { id: 'billing', nameKey: 'settings.billing' as const, icon: faFileAlt },
  ]

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">{t('settings.title')}</h1>
            <p className="text-textSecondary">
              {t('settings.subtitle')}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={handleViewChangelog}
              className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2"
            >
              <FontAwesomeIcon icon={faHistory} />
              <span>{t('settings.viewChangeLog')}</span>
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving || loading}
              className="h-10 px-6 bg-primary hover:bg-primaryHover disabled:opacity-50 text-white rounded-lg text-sm font-medium flex items-center space-x-2"
            >
              {saving ? <FontAwesomeIcon icon={faSpinner} className="animate-spin" /> : <FontAwesomeIcon icon={faSave} />}
              <span>{saving ? t('settings.saving') || 'Saving…' : t('settings.saveChanges')}</span>
            </button>
          </div>
        </div>
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-errorRed">{error}</div>
        )}
        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-sm text-successGreen">
            {success}
          </div>
        )}
      </section>

      <div className="grid grid-cols-4 gap-6">
        <div className="col-span-1">
          <section className="bg-surface rounded-xl border border-borderColor shadow-sm">
            <div className="p-4 space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === tab.id ? 'bg-indigo-50 text-primary border-l-4 border-primary' : 'text-textSecondary hover:bg-gray-50'
                  }`}
                >
                  <FontAwesomeIcon icon={tab.icon} />
                  <span>{t(tab.nameKey)}</span>
                </button>
              ))}
            </div>
          </section>
        </div>

        <div className="col-span-3">
          <section className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-textPrimary mb-1">
                {t(tabs.find((tab) => tab.id === activeTab)?.nameKey ?? 'settings.settings')} {t('settings.settings')}
              </h2>
              <p className="text-sm text-textSecondary">
                {t('settings.configurePreferences') || (() => { const tab = tabs.find((t) => t.id === activeTab); return tab ? `Configure ${t(tab.nameKey).toLowerCase()} preferences` : 'Configure preferences'; })()}
              </p>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <FontAwesomeIcon icon={faSpinner} className="text-3xl text-primary animate-spin" />
              </div>
            ) : (
              <>
                {activeTab === 'general' && (
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-textPrimary mb-2">Company Name</label>
                      <input
                        type="text"
                        value={settings.general.company_name}
                        onChange={(e) => updateGeneral('company_name', e.target.value)}
                        className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-textPrimary mb-2">Company Address</label>
                      <textarea
                        rows={3}
                        value={settings.general.company_address}
                        onChange={(e) => updateGeneral('company_address', e.target.value)}
                        className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-textPrimary mb-2">Tax ID (SIRET)</label>
                        <input
                          type="text"
                          value={settings.general.tax_id_siret}
                          onChange={(e) => updateGeneral('tax_id_siret', e.target.value)}
                          className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-textPrimary mb-2">VAT Number</label>
                        <input
                          type="text"
                          value={settings.general.vat_number}
                          onChange={(e) => updateGeneral('vat_number', e.target.value)}
                          className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-textPrimary mb-2">Default Currency</label>
                      <select
                        value={settings.general.default_currency}
                        onChange={(e) => updateGeneral('default_currency', e.target.value)}
                        className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      >
                        <option value="EUR">EUR (€)</option>
                        <option value="USD">USD ($)</option>
                        <option value="GBP">GBP (£)</option>
                      </select>
                    </div>
                  </div>
                )}

                {activeTab === 'users' && (
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-textPrimary mb-2">Default User Role</label>
                      <select
                        value={settings.users.default_user_role}
                        onChange={(e) => updateUsers('default_user_role', e.target.value)}
                        className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      >
                        <option value="Employee">Employee</option>
                        <option value="Approver">Approver</option>
                        <option value="Finance Manager">Finance Manager</option>
                        <option value="Admin">Admin</option>
                      </select>
                    </div>
                    <div className="flex items-center space-x-3 h-10">
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={settings.users.require_email_verification}
                          onChange={(e) => updateUsers('require_email_verification', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                      </label>
                      <span className="text-sm text-textPrimary">Require email verification for new users</span>
                    </div>
                  </div>
                )}

                {activeTab === 'security' && (
                  <div className="space-y-6">
                    <div className="flex items-center space-x-3 h-10">
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={settings.security.two_factor_enabled}
                          onChange={(e) => updateSecurity('two_factor_enabled', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                      </label>
                      <span className="text-sm text-textPrimary">Enable Two-Factor Authentication</span>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-textPrimary mb-2">Session Timeout (minutes)</label>
                      <input
                        type="number"
                        min={5}
                        max={480}
                        value={settings.security.session_timeout_minutes}
                        onChange={(e) => updateSecurity('session_timeout_minutes', parseInt(e.target.value, 10) || 30)}
                        className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      />
                    </div>
                  </div>
                )}

                {activeTab === 'notifications' && (
                  <div className="space-y-6">
                    <div className="flex items-center space-x-3 h-10">
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={settings.notifications.email_approvals}
                          onChange={(e) => updateNotifications('email_approvals', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                      </label>
                      <span className="text-sm text-textPrimary">Email notifications for approvals</span>
                    </div>
                    <div className="flex items-center space-x-3 h-10">
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={settings.notifications.push_mobile}
                          onChange={(e) => updateNotifications('push_mobile', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                      </label>
                      <span className="text-sm text-textPrimary">Push notifications for mobile app</span>
                    </div>
                  </div>
                )}

                {activeTab === 'billing' && (
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-textPrimary mb-2">Billing Email</label>
                      <input
                        type="email"
                        value={settings.billing.billing_email}
                        onChange={(e) => updateBilling('billing_email', e.target.value)}
                        className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-textPrimary mb-2">Plan</label>
                      <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="text-sm font-semibold text-textPrimary">{settings.billing.plan}</div>
                            <div className="text-xs text-textSecondary">{settings.billing.plan_details}</div>
                          </div>
                          <button
                            type="button"
                            onClick={() => setSuccess('To change plan, contact sales at billing@company.com.')}
                            className="text-sm text-primary hover:text-primaryHover font-medium"
                          >
                            Change Plan
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </section>
        </div>
      </div>

      {/* Changelog modal */}
      {changelogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={() => setChangelogOpen(false)}>
          <div
            className="bg-surface rounded-xl border border-borderColor shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 border-b border-borderColor flex items-center justify-between">
              <h2 className="text-xl font-semibold text-textPrimary">Settings Change Log</h2>
              <button
                type="button"
                onClick={() => setChangelogOpen(false)}
                className="w-10 h-10 flex items-center justify-center text-textMuted hover:text-textPrimary hover:bg-gray-100 rounded-lg"
              >
                <FontAwesomeIcon icon={faTimes} />
              </button>
            </div>
            <div className="p-6 overflow-y-auto flex-1">
              {changelogLoading ? (
                <div className="flex justify-center py-8">
                  <FontAwesomeIcon icon={faSpinner} className="text-2xl text-primary animate-spin" />
                </div>
              ) : changelog.length === 0 ? (
                <p className="text-sm text-textSecondary">No changes recorded yet.</p>
              ) : (
                <ul className="space-y-4">
                  {changelog.map((entry) => (
                    <li key={entry.id} className="border border-borderColor rounded-lg p-4">
                      <div className="flex items-center justify-between text-sm mb-2">
                        <span className="font-medium text-textPrimary capitalize">{entry.section}</span>
                        <span className="text-textMuted">
                          {entry.changed_by_email ?? 'Unknown'} • {new Date(entry.changed_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-xs text-textSecondary">{entry.action}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

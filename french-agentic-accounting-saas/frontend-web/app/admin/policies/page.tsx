'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import Link from 'next/link'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faShieldAlt,
  faDownload,
  faFileImport,
  faFileLines,
  faPlus,
  faFlag,
  faUtensils,
  faPercent,
  faEuroSign,
  faHotel,
  faCar,
  faEllipsisV,
  faSearch,
  faCopy,
  faTrash,
  faTimes,
  faPlay,
  faCheckCircle,
  faInfoCircle,
  faExclamationTriangle,
} from '@fortawesome/free-solid-svg-icons'
import { useLanguage } from '@/contexts/LanguageContext'
import { adminAPI, getAuthErrorMessage } from '@/lib/api'

/** Backend policy_type values (evaluator + admin API) */
const POLICY_TYPE_VALUES = [
  'amount_limit',
  'category_limit',
  'meal_cap',
  'hotel_cap',
  'mileage_rate',
  'required_fields',
  'category_restriction',
] as const
export type BackendPolicyType = (typeof POLICY_TYPE_VALUES)[number]

const POLICY_TABS = ['All Policies', ...POLICY_TYPE_VALUES]

export interface PolicyRecord {
  id: string
  tenant_id: string
  name: string
  description: string | null
  policy_type: string
  policy_rules: Record<string, unknown>
  applies_to_roles: string[]
  is_active: boolean
  effective_from: string | null
  effective_until: string | null
  created_by: string | null
  created_at: string
  updated_at: string
}

function policyTypeToTab(policyType: string): number {
  const idx = POLICY_TYPE_VALUES.indexOf(policyType as BackendPolicyType)
  return idx >= 0 ? idx + 1 : 0
}

function typeBadgeClass(policyType: string): string {
  const map: Record<string, string> = {
    meal_cap: 'text-successGreen bg-green-50',
    amount_limit: 'text-purple-600 bg-purple-50',
    category_limit: 'text-purple-500 bg-purple-50',
    hotel_cap: 'text-indigo-600 bg-indigo-50',
    mileage_rate: 'text-pink-600 bg-pink-50',
    required_fields: 'text-pink-600 bg-pink-50',
    category_restriction: 'text-amber-600 bg-amber-50',
  }
  return map[policyType] ?? 'text-textMuted bg-gray-100'
}

/** French compliance templates: name, policy_type, policy_rules for one-click create */
const FRENCH_TEMPLATES: {
  key: string
  name: string
  desc: string
  policy_type: BackendPolicyType
  policy_rules: Record<string, unknown>
  icon: typeof faUtensils
  bg: string
  hoverBg: string
  iconColor: string
  hoverIcon: string
}[] = [
  {
    key: 'urssaf_per_diem',
    name: 'URSSAF Per Diem',
    desc: 'Standard meal rates',
    icon: faUtensils,
    bg: 'bg-blue-50',
    hoverBg: 'group-hover:bg-primary',
    iconColor: 'text-infoBlue',
    hoverIcon: 'group-hover:text-white',
    policy_type: 'meal_cap',
    policy_rules: { max_amount: 25, meal_type: 'lunch', requires_comment: true },
  },
  {
    key: 'french_vat',
    name: 'French VAT Rules',
    desc: 'Category-based VAT',
    icon: faPercent,
    bg: 'bg-green-50',
    hoverBg: 'group-hover:bg-successGreen',
    iconColor: 'text-successGreen',
    hoverIcon: 'group-hover:text-white',
    policy_type: 'category_restriction',
    policy_rules: { restricted_categories: [] },
  },
  {
    key: 'meal_limits',
    name: 'Meal Limits',
    desc: 'Daily/per-meal caps',
    icon: faEuroSign,
    bg: 'bg-amber-50',
    hoverBg: 'group-hover:bg-warningAmber',
    iconColor: 'text-warningAmber',
    hoverIcon: 'group-hover:text-white',
    policy_type: 'meal_cap',
    policy_rules: { max_amount: 25, meal_type: 'lunch', requires_comment: true },
  },
  {
    key: 'hotel_caps',
    name: 'Hotel Caps',
    desc: 'City-based limits',
    icon: faHotel,
    bg: 'bg-purple-50',
    hoverBg: 'group-hover:bg-purple-600',
    iconColor: 'text-purple-600',
    hoverIcon: 'group-hover:text-white',
    policy_type: 'hotel_cap',
    policy_rules: { max_amount: 200, allow_with_approval: true, requires_comment: true },
  },
  {
    key: 'mileage_rates',
    name: 'Mileage Rates',
    desc: 'Government rates',
    icon: faCar,
    bg: 'bg-pink-50',
    hoverBg: 'group-hover:bg-pink-600',
    iconColor: 'text-pink-600',
    hoverIcon: 'group-hover:text-white',
    policy_type: 'mileage_rate',
    policy_rules: { rate_per_km: 0.629, requires_comment: true },
  },
]

/** Severity from API (error/warning) to display label */
function violationSeverityLabel(severity: string): 'High' | 'Medium' | 'Low' {
  const s = (severity || '').toLowerCase()
  if (s === 'error') return 'High'
  if (s === 'warning') return 'Medium'
  return 'Low'
}

const EXPENSE_CATEGORIES = [
  'meals',
  'travel',
  'accommodation',
  'transport',
  'office',
  'training',
  'client_gifts',
]

/** Send date-only (YYYY-MM-DD) as full ISO datetime for backend validation */
function toISODateTime(dateStr: string): string {
  if (!dateStr || dateStr.length < 10) return dateStr
  if (dateStr.length > 10) return dateStr // already has time
  return `${dateStr}T00:00:00.000Z`
}

function formatRelative(dateStr: string): string {
  try {
    const d = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const days = Math.floor(diffMs / (24 * 60 * 60 * 1000))
    if (days === 0) return 'Today'
    if (days === 1) return '1 day ago'
    if (days < 7) return `${days} days ago`
    if (days < 30) return `${Math.floor(days / 7)} week(s) ago`
    return `${Math.floor(days / 30)} month(s) ago`
  } catch {
    return dateStr
  }
}

export default function PolicyBuilderPage() {
  const { t } = useLanguage()
  const [policies, setPolicies] = useState<PolicyRecord[]>([])
  const [policyStats, setPolicyStats] = useState<{
    total_expenses: number
    compliant_count: number
    violations_count: number
    compliant_percent: number
    violations_percent: number
  } | null>(null)
  const [recentViolations, setRecentViolations] = useState<{
    id: string
    expense_id: string
    date: string | null
    employee: string
    policy: string
    violation: string
    amount: number
    severity: string
  }[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [policyTypeTab, setPolicyTypeTab] = useState(0)
  const [selectedPolicyId, setSelectedPolicyId] = useState<string | null>(null)
  const [policySearch, setPolicySearch] = useState('')
  const [saving, setSaving] = useState(false)
  const [createFromTemplate, setCreateFromTemplate] = useState<typeof FRENCH_TEMPLATES[0] | null>(null)
  const [isEditorVisible, setIsEditorVisible] = useState(false)
  const [newEditorInstance, setNewEditorInstance] = useState(0)
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null)

  const fetchPolicies = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [data, stats, violations] = await Promise.all([
        adminAPI.listPolicies(),
        adminAPI.getPolicyStats().catch(() => null),
        adminAPI.getPolicyViolations(20).catch(() => []),
      ])
      setPolicies(Array.isArray(data) ? data : [])
      setPolicyStats(stats)
      setRecentViolations(Array.isArray(violations) ? violations : [])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load policies')
      setPolicies([])
    } finally {
      setLoading(false)
    }
  }, [selectedPolicyId])

  useEffect(() => {
    fetchPolicies()
  }, [fetchPolicies])

  const filteredPolicies = policies.filter((p) => {
    const matchTab = policyTypeTab === 0 || p.policy_type === POLICY_TYPE_VALUES[policyTypeTab - 1]
    const matchSearch = !policySearch.trim() || p.name.toLowerCase().includes(policySearch.toLowerCase())
    return matchTab && matchSearch
  })

  const selectedPolicy = selectedPolicyId && selectedPolicyId !== 'new'
    ? policies.find((p) => p.id === selectedPolicyId)
    : null
  const isNewPolicy = selectedPolicyId === 'new' || createFromTemplate !== null
  const importInputRef = useRef<HTMLInputElement>(null)
  const violationsSectionRef = useRef<HTMLElement>(null)

  const handleCreateNew = () => {
    setCreateFromTemplate(null)
    setSelectedPolicyId('new')
    setIsEditorVisible(true)
    setNewEditorInstance((prev) => prev + 1)
  }

  const handleExport = () => {
    const exportData = policies.map((p) => ({
      name: p.name,
      description: p.description ?? undefined,
      policy_type: p.policy_type,
      policy_rules: p.policy_rules,
      applies_to_roles: p.applies_to_roles ?? [],
      is_active: p.is_active,
      effective_from: p.effective_from ?? undefined,
      effective_until: p.effective_until ?? undefined,
    }))
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `policies-export-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleImportClick = () => {
    importInputRef.current?.click()
  }

  const handleImportFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setError(null)
    try {
      const text = await file.text()
      const data = JSON.parse(text)
      const list = Array.isArray(data) ? data : [data]
      if (list.length === 0) {
        setError('File contains no policies.')
        e.target.value = ''
        return
      }
      setSaving(true)
      let created = 0
      for (const item of list) {
        const name = item?.name ?? item?.policy_name
        const policy_type = item?.policy_type ?? 'amount_limit'
        const policy_rules = item?.policy_rules ?? {}
        if (!name || typeof name !== 'string') continue
        await adminAPI.createPolicy({
          name,
          description: item?.description ?? undefined,
          policy_type,
          policy_rules,
          applies_to_roles: Array.isArray(item?.applies_to_roles) ? item.applies_to_roles : [],
          effective_from: item?.effective_from ?? undefined,
          effective_until: item?.effective_until ?? undefined,
        })
        created++
      }
      await fetchPolicies()
      if (created === list.length) setError(null)
      else if (created > 0) setError(`Imported ${created} of ${list.length}. Some entries were skipped (missing name).`)
      else setError('No valid policies in file (each entry needs a name).')
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, 'Invalid file. Use a JSON export from this page.'))
    } finally {
      setSaving(false)
      e.target.value = ''
    }
  }

  const handleApplyTemplate = (tpl: typeof FRENCH_TEMPLATES[0]) => {
    setCreateFromTemplate(tpl)
    setSelectedPolicyId('new')
    setIsEditorVisible(true)
    setNewEditorInstance((prev) => prev + 1)
  }

  const handleCancelEditor = () => {
    if (selectedPolicyId && selectedPolicyId !== 'new') {
      // When editing an existing policy, go back to read-only details view
      setIsEditorVisible(false)
    } else {
      // When creating a new policy, return to the empty state
      setSelectedPolicyId(null)
      setCreateFromTemplate(null)
      setIsEditorVisible(false)
    }
  }

  const handleSave = async (payload: {
    name: string
    description?: string
    policy_type: string
    policy_rules: Record<string, unknown>
    applies_to_roles?: string[]
    is_active?: boolean
    effective_from?: string
    effective_until?: string
  }) => {
    setSaving(true)
    try {
      if (isNewPolicy) {
        await adminAPI.createPolicy({
          name: payload.name,
          description: payload.description ?? undefined,
          policy_type: payload.policy_type,
          policy_rules: payload.policy_rules,
          applies_to_roles: payload.applies_to_roles ?? [],
          effective_from: payload.effective_from ? toISODateTime(payload.effective_from) : undefined,
          effective_until: payload.effective_until ? toISODateTime(payload.effective_until) : undefined,
        })
        await fetchPolicies()
        // After creating a policy, hide the form and reset editor state.
        setCreateFromTemplate(null)
        setSelectedPolicyId(null)
        setIsEditorVisible(false)
      } else if (selectedPolicyId && selectedPolicyId !== 'new') {
        await adminAPI.updatePolicy(selectedPolicyId, {
          name: payload.name,
          description: payload.description,
          policy_type: payload.policy_type,
          policy_rules: payload.policy_rules,
          applies_to_roles: payload.applies_to_roles,
          is_active: payload.is_active,
          effective_from: payload.effective_from ? toISODateTime(payload.effective_from) : undefined,
          effective_until: payload.effective_until ? toISODateTime(payload.effective_until) : undefined,
        })
        await fetchPolicies()
      }
    } catch (e: unknown) {
      setError(getAuthErrorMessage(e, 'Failed to save policy'))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (policyId: string) => {
    if (!confirm(t('policies.confirmDelete') || 'Delete this policy?')) return
    setSaving(true)
    try {
      await adminAPI.deletePolicy(policyId)
      await fetchPolicies()
      setSelectedPolicyId(policies[0]?.id ?? null)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to delete policy')
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">
              {t('policies.title') || 'Policy Builder'}
            </h1>
            <p className="text-textSecondary">
              {t('policies.subtitle') || 'Configure expense policies and compliance rules'}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={handleExport}
              disabled={policies.length === 0}
              className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FontAwesomeIcon icon={faDownload} />
              <span>{t('policies.export') || 'Export'}</span>
            </button>
            <input
              ref={importInputRef}
              type="file"
              accept=".json,application/json"
              className="hidden"
              onChange={handleImportFile}
            />
            <button
              type="button"
              onClick={handleImportClick}
              disabled={saving}
              className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FontAwesomeIcon icon={faFileImport} />
              <span>{t('policies.import') || 'Import'}</span>
            </button>
            <button
              type="button"
              onClick={handleCreateNew}
              className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2"
            >
              <FontAwesomeIcon icon={faPlus} />
              <span>{t('policies.createPolicy') || 'Create Policy'}</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-center justify-between">
            <span>{error}</span>
            <button type="button" onClick={() => setError(null)} className="text-red-600 hover:text-red-800">
              <FontAwesomeIcon icon={faTimes} />
            </button>
          </div>
        )}

        <div className="flex items-center space-x-4 flex-wrap gap-2">
          {POLICY_TABS.map((label, i) => (
            <button
              key={label}
              type="button"
              onClick={() => setPolicyTypeTab(i)}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                policyTypeTab === i ? 'bg-primary text-white' : 'text-textSecondary hover:bg-gray-50'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </section>

      <section className="mb-8">
        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-6 border border-indigo-100">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center">
                <FontAwesomeIcon icon={faFlag} className="text-white text-xl" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-textPrimary mb-1">
                  {t('policies.frenchTemplates') || 'French Compliance Templates'}
                </h2>
                <p className="text-sm text-textSecondary">
                  {t('policies.frenchTemplatesDesc') || 'Pre-configured policies for French regulations'}
                </p>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
            {FRENCH_TEMPLATES.map((tpl) => (
              <button
                key={tpl.key}
                type="button"
                onClick={() => handleApplyTemplate(tpl)}
                className="bg-white rounded-lg p-4 border border-indigo-100 hover:border-primary transition-all group text-left"
              >
                <div className={`w-10 h-10 ${tpl.bg} ${tpl.hoverBg} rounded-lg flex items-center justify-center mb-3 transition-colors`}>
                  <FontAwesomeIcon icon={tpl.icon} className={`${tpl.iconColor} ${tpl.hoverIcon} transition-colors`} />
                </div>
                <h3 className="text-sm font-semibold text-textPrimary mb-1">{tpl.name}</h3>
                <p className="text-xs text-textSecondary">{tpl.desc}</p>
              </button>
            ))}
          </div>
        </div>
      </section>

      <div className="grid grid-cols-3 gap-6 mb-8">
        <section className="col-span-1">
          <div className="bg-surface rounded-xl border border-borderColor shadow-sm">
            <div className="p-6 border-b border-borderColor">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-textPrimary">{t('policies.activePolicies') || 'Active Policies'}</h2>
                <span className="text-xs font-medium text-successGreen bg-green-50 px-2 py-1 rounded-full">
                  {policies.filter((p) => p.is_active).length} Active
                </span>
              </div>
              <div className="relative">
                <FontAwesomeIcon icon={faSearch} className="absolute left-3 top-1/2 -translate-y-1/2 text-textMuted text-sm" />
                <input
                  type="text"
                  placeholder={t('policies.searchPolicies') || 'Search policies...'}
                  value={policySearch}
                  onChange={(e) => setPolicySearch(e.target.value)}
                  className="w-full h-10 pl-9 pr-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>
            </div>
            <div className="overflow-y-auto max-h-[800px]">
              {loading ? (
                <div className="p-6 text-center text-textMuted text-sm">{t('common.loading') || 'Loading...'}</div>
              ) : (
                <>
                  {filteredPolicies.map((policy) => (
                    <div
                      key={policy.id}
                      role="button"
                      tabIndex={0}
                      onClick={() => { setSelectedPolicyId(policy.id); setCreateFromTemplate(null); setIsEditorVisible(false); setMenuOpenId(null) }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          setSelectedPolicyId(policy.id)
                          setCreateFromTemplate(null)
                          setIsEditorVisible(false)
                          setMenuOpenId(null)
                        }
                      }}
                      className={`p-4 border-b border-borderColor hover:bg-gray-50 cursor-pointer transition-colors ${
                        selectedPolicyId === policy.id ? 'bg-indigo-50 border-l-4 border-l-primary' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h3 className="text-sm font-semibold text-textPrimary mb-1">{policy.name}</h3>
                          <div className="flex items-center space-x-2 flex-wrap gap-1">
                            <span className={`text-xs font-medium px-2 py-1 rounded-full ${typeBadgeClass(policy.policy_type)}`}>
                              {policy.policy_type}
                            </span>
                          </div>
                        </div>
                        <div className="relative">
                          <button
                            type="button"
                            className="text-textMuted hover:text-textPrimary p-1"
                            onClick={(e) => {
                              e.stopPropagation()
                              setMenuOpenId((current) => (current === policy.id ? null : policy.id))
                            }}
                          >
                            <FontAwesomeIcon icon={faEllipsisV} />
                          </button>
                          {menuOpenId === policy.id && (
                            <div className="absolute right-0 mt-2 w-32 bg-white border border-borderColor rounded-lg shadow-lg z-10 text-xs">
                              <button
                                type="button"
                                className="w-full text-left px-3 py-2 hover:bg-gray-50"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setSelectedPolicyId(policy.id)
                                  setCreateFromTemplate(null)
                                  setIsEditorVisible(true)
                                  setMenuOpenId(null)
                                }}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="w-full text-left px-3 py-2 text-errorRed hover:bg-red-50"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setMenuOpenId(null)
                                  handleDelete(policy.id)
                                }}
                              >
                                Delete
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center justify-between text-xs text-textMuted">
                        <span>Modified {formatRelative(policy.updated_at)}</span>
                        <span className={policy.is_active ? 'text-successGreen font-medium' : 'text-warningAmber font-medium'}>
                          {policy.is_active ? 'Active' : 'Draft'}
                        </span>
                      </div>
                    </div>
                  ))}
                  {filteredPolicies.length === 0 && !loading && (
                    <div className="p-6 text-center text-textMuted text-sm">
                      {policySearch || policyTypeTab > 0 ? 'No policies match filters' : 'No policies yet. Create one or use a template.'}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </section>

        <section className="col-span-2">
          <div className="bg-surface rounded-xl border border-borderColor shadow-sm">
            <div className="p-6 border-b border-borderColor">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-textPrimary mb-1">{t('policies.policyEditor') || 'Policy Editor'}</h2>
                  <p className="text-sm text-textSecondary">
                    {isEditorVisible
                      ? (t('policies.policyEditorDesc') || 'Configure policy details and rules')
                      : selectedPolicy
                        ? (t('policies.policyDetailsDesc') || 'View policy details. Use Edit to make changes.')
                        : (t('policies.policyEditorDesc') || 'Configure policy details and rules')}
                  </p>
                </div>
                {selectedPolicy && !isEditorVisible && (
                  <div className="flex items-center space-x-3">
                    <button
                      type="button"
                      onClick={() => {
                        setIsEditorVisible(true)
                        setCreateFromTemplate(null)
                      }}
                      className="h-8 px-4 border border-borderColor rounded-md text-xs font-medium text-textPrimary hover:bg-gray-50"
                    >
                      {t('common.edit') || 'Edit'}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(selectedPolicy.id)}
                      className="h-8 px-4 border border-errorRed text-errorRed rounded-md text-xs font-medium hover:bg-red-50"
                    >
                      {t('common.delete') || 'Delete'}
                    </button>
                  </div>
                )}
              </div>
            </div>
            <div className="p-6 overflow-y-auto max-h-[800px]">
              {isEditorVisible && (selectedPolicy || isNewPolicy) ? (
                <PolicyEditorForm
                  key={
                    selectedPolicy
                      ? `editor-${selectedPolicyId}`
                      : `editor-new-${newEditorInstance}-${createFromTemplate?.key ?? 'blank'}`
                  }
                  policy={selectedPolicy ?? undefined}
                  createFromTemplate={createFromTemplate}
                  saving={saving}
                  t={t}
                  onSave={handleSave}
                  onCancel={handleCancelEditor}
                  onDelete={selectedPolicy ? () => handleDelete(selectedPolicy.id) : undefined}
                />
              ) : selectedPolicy ? (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-semibold text-textPrimary">{selectedPolicy.name}</h3>
                    {selectedPolicy.description && (
                      <p className="text-sm text-textSecondary mt-1">{selectedPolicy.description}</p>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-textMuted">Type</div>
                      <div className="font-medium">{selectedPolicy.policy_type}</div>
                    </div>
                    <div>
                      <div className="text-textMuted">Status</div>
                      <div className={`font-medium ${selectedPolicy.is_active ? 'text-successGreen' : 'text-warningAmber'}`}>
                        {selectedPolicy.is_active ? 'Active' : 'Draft'}
                      </div>
                    </div>
                    <div>
                      <div className="text-textMuted">Effective From</div>
                      <div className="font-medium">
                        {selectedPolicy.effective_from ? selectedPolicy.effective_from.slice(0, 10) : '—'}
                      </div>
                    </div>
                    <div>
                      <div className="text-textMuted">Effective Until</div>
                      <div className="font-medium">
                        {selectedPolicy.effective_until ? selectedPolicy.effective_until.slice(0, 10) : '—'}
                      </div>
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-textMuted mb-1">Rules (JSON)</div>
                    <pre className="text-xs bg-gray-50 border border-borderColor rounded-lg p-3 overflow-x-auto">
                      {JSON.stringify(selectedPolicy.policy_rules ?? {}, null, 2)}
                    </pre>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-16 text-textMuted">
                  <FontAwesomeIcon icon={faShieldAlt} className="text-4xl mb-4 opacity-50" />
                  <p className="text-sm mb-4">
                    {t('policies.selectPolicyToEdit') || 'Select a policy from the list to edit or create one'}
                  </p>
                  <button
                    type="button"
                    onClick={handleCreateNew}
                    className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2"
                  >
                    <FontAwesomeIcon icon={faPlus} />
                    <span>{t('policies.createPolicy') || 'Create Policy'}</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>

      <section className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faShieldAlt} className="text-primary text-xl" />
            </div>
            <span className="text-xs font-medium text-successGreen bg-green-50 px-2 py-1 rounded-full">{t('policies.active') || 'Active'}</span>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">{policies.filter((p) => p.is_active).length}</div>
          <div className="text-sm text-textSecondary">{t('policies.activePoliciesCount') || 'Active Policies'}</div>
        </div>
        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-amber-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faFileLines} className="text-warningAmber text-xl" />
            </div>
            <span className="text-xs font-medium text-warningAmber bg-amber-50 px-2 py-1 rounded-full">{t('policies.draft') || 'Draft'}</span>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">{policies.filter((p) => !p.is_active).length}</div>
          <div className="text-sm text-textSecondary">{t('policies.draftPolicies') || 'Draft Policies'}</div>
        </div>
        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faCheckCircle} className="text-successGreen text-xl" />
            </div>
            {policyStats && policyStats.total_expenses > 0 && (
              <span className="text-xs font-medium text-successGreen bg-green-50 px-2 py-1 rounded-full">{policyStats.compliant_percent}%</span>
            )}
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">
            {policyStats ? policyStats.compliant_count.toLocaleString() : '—'}
          </div>
          <div className="text-sm text-textSecondary">{t('policies.compliantExpenses') || 'Compliant Expenses'}</div>
          <div className="mt-4 text-xs text-textMuted">{t('policies.thisMonth') || 'This month'}</div>
        </div>
        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-red-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faExclamationTriangle} className="text-errorRed text-xl" />
            </div>
            {policyStats && policyStats.total_expenses > 0 && (
              <span className="text-xs font-medium text-errorRed bg-red-50 px-2 py-1 rounded-full">{policyStats.violations_percent}%</span>
            )}
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">
            {policyStats ? policyStats.violations_count.toLocaleString() : '—'}
          </div>
          <div className="text-sm text-textSecondary">{t('policies.policyViolations') || 'Policy Violations'}</div>
          <div className="mt-4 text-xs text-textMuted">{t('policies.requiresReview') || 'Requires review'}</div>
        </div>
      </section>

      <section className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-textPrimary mb-1">{t('policies.impactAnalysis') || 'Policy Impact Analysis'}</h2>
            <p className="text-sm text-textSecondary">{t('policies.impactAnalysisDesc') || 'How policies affect expense submissions'}</p>
          </div>
          <div className="flex items-center space-x-2">
            <button type="button" className="px-3 py-1.5 text-xs font-medium text-primary bg-indigo-50 rounded-lg">Last 30 Days</button>
            <button type="button" className="px-3 py-1.5 text-xs font-medium text-textSecondary hover:bg-gray-50 rounded-lg">Last Quarter</button>
            <button type="button" className="px-3 py-1.5 text-xs font-medium text-textSecondary hover:bg-gray-50 rounded-lg">Last Year</button>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-6">
          {(() => {
            const total = policyStats?.total_expenses ?? 0
            const compliant = policyStats?.compliant_count ?? 0
            const violations = policyStats?.violations_count ?? 0
            const compliantPct = total > 0 ? Math.round((compliant / total) * 100) : 0
            const violationsPct = total > 0 ? Math.round((violations / total) * 100) : 0
            return (
              <>
                <div className="p-5 border border-borderColor rounded-xl">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-textPrimary">{t('policies.autoApproved') || 'Auto-Approved'}</h3>
                  </div>
                  <div className="text-3xl font-bold text-successGreen mb-2">{policyStats ? compliant.toLocaleString() : '—'}</div>
                  <div className="text-sm text-textSecondary mb-4">{t('policies.expensesPassedChecks') || 'Expenses passed all checks'}</div>
                  <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-successGreen rounded-full transition-all" style={{ width: `${compliantPct}%` }} />
                  </div>
                  <div className="flex justify-between text-xs text-textMuted mt-2">
                    <span>{total > 0 ? `${compliantPct}% of total` : '—'}</span>
                    <span>{total > 0 ? `${total.toLocaleString()} total` : '—'}</span>
                  </div>
                </div>
                <div className="p-5 border border-borderColor rounded-xl">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-textPrimary">{t('policies.flaggedForReview') || 'Flagged for Review'}</h3>
                  </div>
                  <div className="text-3xl font-bold text-warningAmber mb-2">0</div>
                  <div className="text-sm text-textSecondary mb-4">{t('policies.requiredManualApproval') || 'Required manual approval'}</div>
                  <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-warningAmber rounded-full" style={{ width: '0%' }} />
                  </div>
                  <div className="flex justify-between text-xs text-textMuted mt-2">
                    <span>{total > 0 ? '0% of total' : '—'}</span>
                    <span>{total > 0 ? `${total.toLocaleString()} total` : '—'}</span>
                  </div>
                </div>
                <div className="p-5 border border-borderColor rounded-xl">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-textPrimary">{t('policies.blockedRejected') || 'Blocked/Rejected'}</h3>
                  </div>
                  <div className="text-3xl font-bold text-errorRed mb-2">{policyStats ? violations.toLocaleString() : '—'}</div>
                  <div className="text-sm text-textSecondary mb-4">{t('policies.violationsDetected') || 'Policy violations detected'}</div>
                  <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-errorRed rounded-full transition-all" style={{ width: `${violationsPct}%` }} />
                  </div>
                  <div className="flex justify-between text-xs text-textMuted mt-2">
                    <span>{total > 0 ? `${violationsPct}% of total` : '—'}</span>
                    <span>{total > 0 ? `${total.toLocaleString()} total` : '—'}</span>
                  </div>
                </div>
              </>
            )
          })()}
        </div>
      </section>

      <section ref={violationsSectionRef} id="recent-violations" className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-textPrimary mb-1">{t('policies.recentViolations') || 'Recent Policy Violations'}</h2>
            <p className="text-sm text-textSecondary">{t('policies.recentViolationsDesc') || 'Expenses that triggered policy alerts'}</p>
          </div>
          <button
            type="button"
            onClick={() => violationsSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
            className="text-sm text-primary hover:text-primaryHover font-medium"
          >
            {t('policies.viewAllViolations') || 'View All Violations'}
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-borderColor">
                <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('common.date') || 'Date'}</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('policies.employee') || 'Employee'}</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('policies.policy') || 'Policy'}</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('policies.violation') || 'Violation'}</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('common.amount') || 'Amount'}</th>
                <th className="text-center py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('policies.severity') || 'Severity'}</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('common.actions') || 'Actions'}</th>
              </tr>
            </thead>
            <tbody>
              {recentViolations.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-textMuted text-sm">
                    {t('policies.noViolations') || 'No recent policy violations. Expenses that trigger policy alerts will appear here.'}
                  </td>
                </tr>
              ) : (
                recentViolations.map((row) => {
                  const severityLabel = violationSeverityLabel(row.severity)
                  const dateStr = row.date ? new Date(row.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : '—'
                  return (
                    <tr key={row.id} className="border-b border-borderColor hover:bg-gray-50 h-14">
                      <td className="py-3 px-4 text-sm text-textPrimary">{dateStr}</td>
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xs font-medium">
                            {(row.employee || '?').charAt(0).toUpperCase()}
                          </div>
                          <span className="text-sm text-textPrimary">{row.employee || '—'}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-sm text-textSecondary">{row.policy}</td>
                      <td className="py-3 px-4 text-sm text-textSecondary">{row.violation}</td>
                      <td className="py-3 px-4 text-right text-sm font-medium text-errorRed">
                        €{typeof row.amount === 'number' ? row.amount.toFixed(2) : row.amount}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`inline-flex items-center text-xs font-medium px-2 py-1 rounded-full ${
                          severityLabel === 'High' ? 'text-errorRed bg-red-50' :
                          severityLabel === 'Medium' ? 'text-warningAmber bg-amber-50' :
                          'text-successGreen bg-green-50'
                        }`}>
                          {severityLabel}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Link
                          href={`/expenses/${row.expense_id}`}
                          className="text-primary hover:text-primaryHover text-sm font-medium"
                        >
                          {t('policies.review') || 'Review'}
                        </Link>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}

/** Inline form for create/edit with type-specific rule fields */
function PolicyEditorForm({
  policy,
  createFromTemplate,
  saving,
  t,
  onSave,
  onCancel,
  onDelete,
}: {
  policy?: PolicyRecord
  createFromTemplate: typeof FRENCH_TEMPLATES[0] | null
  saving: boolean
  t: (key: string) => string
  onSave: (payload: {
    name: string
    description?: string
    policy_type: string
    policy_rules: Record<string, unknown>
    applies_to_roles?: string[]
    is_active?: boolean
    effective_from?: string
    effective_until?: string
  }) => Promise<void>
  onCancel: () => void
  onDelete?: () => void
}) {
  const isNew = !policy
  const template = createFromTemplate ?? null
  const [name, setName] = useState(policy?.name ?? template?.name ?? '')
  const [description, setDescription] = useState(policy?.description ?? (template ? '' : ''))
  const [policyType, setPolicyType] = useState<string>(policy?.policy_type ?? template?.policy_type ?? 'amount_limit')
  const defaultRules: Record<string, unknown> = {
    amount_limit: { max_amount: 1000, block_on_exceed: false, requires_comment_on_exceed: true },
    meal_cap: { max_amount: 25, meal_type: 'lunch', requires_comment: true },
    hotel_cap: { max_amount: 200, allow_with_approval: true, requires_comment: true },
    mileage_rate: { rate_per_km: 0.629, requires_comment: true },
    required_fields: { required_fields: ['description', 'merchant_name', 'category'] },
    category_restriction: { restricted_categories: [] },
    category_limit: { category_limits: {} },
  }
  const [policyRules, setPolicyRules] = useState<Record<string, unknown>>(
    (policy?.policy_rules ?? template?.policy_rules ?? defaultRules['amount_limit']) as Record<string, unknown>
  )
  const [isActive, setIsActive] = useState(policy?.is_active ?? true)
  const [effectiveFrom, setEffectiveFrom] = useState(
    policy?.effective_from ? policy.effective_from.slice(0, 10) : new Date().toISOString().slice(0, 10)
  )
  const [effectiveUntil, setEffectiveUntil] = useState(
    policy?.effective_until ? policy.effective_until.slice(0, 10) : ''
  )
  const [appliesToRoles, setAppliesToRoles] = useState<string[]>(Array.isArray(policy?.applies_to_roles) ? policy.applies_to_roles : [])

  const updateRule = (key: string, value: unknown) => {
    setPolicyRules((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({
      name,
      description: description || undefined,
      policy_type: policyType,
      policy_rules: policyRules,
      applies_to_roles: appliesToRoles,
      is_active: isActive,
      effective_from: effectiveFrom || undefined,
      effective_until: effectiveUntil || undefined,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="flex items-center justify-between mb-4">
        <div />
        <div className="flex items-center space-x-2">
          <button type="button" onClick={onCancel} className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">
            {t('common.cancel') || 'Cancel'}
          </button>
          {!isNew && (
            <button type="button" onClick={onDelete} className="h-10 px-4 border border-errorRed text-errorRed rounded-lg text-sm font-medium hover:bg-red-50">
              {t('common.delete') || 'Delete'}
            </button>
          )}
          <button type="submit" disabled={saving} className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium disabled:opacity-50">
            {saving ? (t('common.loading') || 'Saving...') : (isNew ? (t('policies.createPolicy') || 'Create Policy') : (t('policies.saveActivate') || 'Save & Activate'))}
          </button>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-textPrimary mb-4">{t('policies.basicInfo') || 'Basic Information'}</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-textPrimary mb-2">{t('policies.policyName') || 'Policy Name'} *</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-textPrimary mb-2">{t('policies.policyType') || 'Policy Type'} *</label>
            <select
              value={policyType}
              onChange={(e) => setPolicyType(e.target.value)}
              className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white"
            >
              {POLICY_TYPE_VALUES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="mt-4">
          <label className="block text-sm font-medium text-textPrimary mb-2">{t('policies.description') || 'Description'}</label>
          <textarea
            rows={3}
            placeholder={t('policies.describePolicy') || 'Describe this policy...'}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>
      </div>

      <div className="h-px bg-borderColor" />

      <div>
        <h3 className="text-lg font-semibold text-textPrimary mb-4">{t('policies.ruleBuilder') || 'Rule Configuration'}</h3>
        <TypeSpecificRuleForm
          policyType={policyType}
          policyRules={policyRules}
          updateRule={updateRule}
          t={t}
        />
      </div>

      <div className="h-px bg-borderColor" />

      <div>
        <h3 className="text-lg font-semibold text-textPrimary mb-4">{t('policies.effectiveDates') || 'Effective Dates'}</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-textPrimary mb-2">{t('policies.startDate') || 'Start Date'}</label>
            <input
              type="date"
              value={effectiveFrom}
              onChange={(e) => setEffectiveFrom(e.target.value)}
              className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-textPrimary mb-2">{t('policies.endDate') || 'End Date'}</label>
            <input
              type="date"
              value={effectiveUntil}
              onChange={(e) => setEffectiveUntil(e.target.value)}
              placeholder={t('policies.noEndDate') || 'No end date'}
              className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <p className="text-xs text-textMuted mt-1">{t('policies.noEndDateHint') || 'Leave empty for no expiration'}</p>
          </div>
        </div>
      </div>

      {!isNew && (
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="is_active"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="rounded border-borderColor"
          />
          <label htmlFor="is_active" className="text-sm font-medium text-textPrimary">{t('policies.active') || 'Active'}</label>
        </div>
      )}
    </form>
  )
}

/** Renders inputs for policy_rules based on policy_type (backend evaluator shapes). */
function TypeSpecificRuleForm({
  policyType,
  policyRules,
  updateRule,
  t,
}: {
  policyType: string
  policyRules: Record<string, unknown>
  updateRule: (key: string, value: unknown) => void
  t: (key: string) => string
}) {
  if (policyType === 'amount_limit') {
    const max = (policyRules.max_amount as number) ?? 1000
    const block = (policyRules.block_on_exceed as boolean) ?? false
    const reqComment = (policyRules.requires_comment_on_exceed as boolean) ?? true
    return (
      <div className="space-y-4 p-4 border border-borderColor rounded-xl bg-gray-50">
        <div>
          <label className="block text-sm font-medium text-textPrimary mb-2">Max amount (€)</label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={max}
            onChange={(e) => updateRule('max_amount', parseFloat(e.target.value) || 0)}
            className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm"
          />
        </div>
        <label className="flex items-center space-x-2">
          <input type="checkbox" checked={block} onChange={(e) => updateRule('block_on_exceed', e.target.checked)} className="rounded" />
          <span className="text-sm">Block expense when exceeded</span>
        </label>
        <label className="flex items-center space-x-2">
          <input type="checkbox" checked={reqComment} onChange={(e) => updateRule('requires_comment_on_exceed', e.target.checked)} className="rounded" />
          <span className="text-sm">Require comment when exceeded</span>
        </label>
      </div>
    )
  }
  if (policyType === 'meal_cap') {
    const maxAmount = (policyRules.max_amount as number) ?? 25
    const mealType = (policyRules.meal_type as string) ?? 'lunch'
    const requiresComment = (policyRules.requires_comment as boolean) ?? true
    return (
      <div className="space-y-4 p-4 border border-borderColor rounded-xl bg-gray-50">
        <div>
          <label className="block text-sm font-medium text-textPrimary mb-2">Meal type</label>
          <select
            value={mealType}
            onChange={(e) => updateRule('meal_type', e.target.value)}
            className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm"
          >
            <option value="breakfast">Breakfast (€19 cap)</option>
            <option value="lunch">Lunch (€25 cap)</option>
            <option value="dinner">Dinner (€25 cap)</option>
            <option value="default">Default</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-textPrimary mb-2">Max amount per meal (€)</label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={maxAmount}
            onChange={(e) => updateRule('max_amount', parseFloat(e.target.value) || 0)}
            className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm"
          />
        </div>
        <label className="flex items-center space-x-2">
          <input type="checkbox" checked={requiresComment} onChange={(e) => updateRule('requires_comment', e.target.checked)} className="rounded" />
          <span className="text-sm">Require comment when over cap</span>
        </label>
      </div>
    )
  }
  if (policyType === 'hotel_cap') {
    const maxAmount = (policyRules.max_amount as number) ?? 200
    const allowWithApproval = (policyRules.allow_with_approval as boolean) ?? true
    const requiresComment = (policyRules.requires_comment as boolean) ?? true
    return (
      <div className="space-y-4 p-4 border border-borderColor rounded-xl bg-gray-50">
        <div>
          <label className="block text-sm font-medium text-textPrimary mb-2">Max amount per night (€)</label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={maxAmount}
            onChange={(e) => updateRule('max_amount', parseFloat(e.target.value) || 0)}
            className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm"
          />
        </div>
        <label className="flex items-center space-x-2">
          <input type="checkbox" checked={allowWithApproval} onChange={(e) => updateRule('allow_with_approval', e.target.checked)} className="rounded" />
          <span className="text-sm">Allow with approval when over cap</span>
        </label>
        <label className="flex items-center space-x-2">
          <input type="checkbox" checked={requiresComment} onChange={(e) => updateRule('requires_comment', e.target.checked)} className="rounded" />
          <span className="text-sm">Require comment</span>
        </label>
      </div>
    )
  }
  if (policyType === 'mileage_rate') {
    const ratePerKm = (policyRules.rate_per_km as number) ?? 0.629
    const requiresComment = (policyRules.requires_comment as boolean) ?? true
    return (
      <div className="space-y-4 p-4 border border-borderColor rounded-xl bg-gray-50">
        <div>
          <label className="block text-sm font-medium text-textPrimary mb-2">Rate per km (€)</label>
          <input
            type="number"
            step="0.001"
            min="0"
            value={ratePerKm}
            onChange={(e) => updateRule('rate_per_km', parseFloat(e.target.value) || 0)}
            className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm"
          />
        </div>
        <label className="flex items-center space-x-2">
          <input type="checkbox" checked={requiresComment} onChange={(e) => updateRule('requires_comment', e.target.checked)} className="rounded" />
          <span className="text-sm">Require comment when amount does not match distance</span>
        </label>
      </div>
    )
  }
  if (policyType === 'required_fields') {
    const requiredFields = (policyRules.required_fields as string[]) ?? ['description', 'merchant_name', 'category']
    const options = ['description', 'merchant_name', 'category']
    return (
      <div className="space-y-4 p-4 border border-borderColor rounded-xl bg-gray-50">
        <label className="block text-sm font-medium text-textPrimary mb-2">Required fields</label>
        {options.map((opt) => (
          <label key={opt} className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={requiredFields.includes(opt)}
              onChange={(e) => {
                const next = e.target.checked
                  ? [...requiredFields, opt]
                  : requiredFields.filter((f) => f !== opt)
                updateRule('required_fields', next)
              }}
              className="rounded"
            />
            <span className="text-sm">{opt}</span>
          </label>
        ))}
      </div>
    )
  }
  if (policyType === 'category_restriction') {
    const restricted = (policyRules.restricted_categories as string[]) ?? []
    return (
      <div className="space-y-4 p-4 border border-borderColor rounded-xl bg-gray-50">
        <label className="block text-sm font-medium text-textPrimary mb-2">Restricted categories (expenses in these are blocked)</label>
        <div className="flex flex-wrap gap-2">
          {EXPENSE_CATEGORIES.map((cat) => (
            <label key={cat} className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={restricted.includes(cat)}
                onChange={(e) => {
                  const next = e.target.checked
                    ? [...restricted, cat]
                    : restricted.filter((c) => c !== cat)
                  updateRule('restricted_categories', next)
                }}
                className="rounded"
              />
              <span className="text-sm">{cat}</span>
            </label>
          ))}
        </div>
      </div>
    )
  }
  if (policyType === 'category_limit') {
    const categoryLimits = (policyRules.category_limits as Record<string, { max_amount?: number; block_on_exceed?: boolean; requires_comment?: boolean }>) ?? {}
    const updateCategoryLimit = (cat: string, field: string, value: number | boolean) => {
      const next = { ...categoryLimits, [cat]: { ...(categoryLimits[cat] ?? {}), [field]: value } }
      updateRule('category_limits', next)
    }
    return (
      <div className="space-y-4 p-4 border border-borderColor rounded-xl bg-gray-50">
        <p className="text-sm text-textSecondary mb-2">Max amount per category (€). Leave empty to skip.</p>
        {EXPENSE_CATEGORIES.map((cat) => {
          const lim = categoryLimits[cat]
          const maxAmount = lim?.max_amount ?? 0
          const blockOnExceed = lim?.block_on_exceed ?? true
          const requiresComment = lim?.requires_comment ?? false
          return (
            <div key={cat} className="flex items-center gap-4 flex-wrap">
              <span className="text-sm font-medium text-textPrimary w-40">{cat}</span>
              <input
                type="number"
                step="0.01"
                min="0"
                placeholder="Max €"
                value={maxAmount || ''}
                onChange={(e) => updateCategoryLimit(cat, 'max_amount', parseFloat(e.target.value) || 0)}
                className="w-24 h-9 px-2 border border-borderColor rounded text-sm"
              />
              <label className="flex items-center gap-1 text-xs">
                <input type="checkbox" checked={blockOnExceed} onChange={(e) => updateCategoryLimit(cat, 'block_on_exceed', e.target.checked)} className="rounded" />
                Block
              </label>
              <label className="flex items-center gap-1 text-xs">
                <input type="checkbox" checked={requiresComment} onChange={(e) => updateCategoryLimit(cat, 'requires_comment', e.target.checked)} className="rounded" />
                Comment
              </label>
            </div>
          )
        })}
      </div>
    )
  }
  return (
    <div className="p-4 border border-borderColor rounded-xl bg-gray-50 text-sm text-textSecondary">
      Rule configuration for type &quot;{policyType}&quot;. Edit raw rules if needed.
    </div>
  )
}

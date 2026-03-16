'use client'

import { useState, useEffect, useCallback } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faShieldAlt,
  faDownload,
  faFileImport,
  faPlus,
  faFlag,
  faUtensils,
  faPercent,
  faEuroSign,
  faHotel,
  faCar,
  faEllipsisV,
  faSearch,
  faSpinner,
  faExclamationTriangle,
  faTrash,
} from '@fortawesome/free-solid-svg-icons'
import { adminAPI, type AdminPolicy, getAuthErrorMessage } from '@/lib/api'

const POLICY_TYPE_TABS: { label: string; backendTypes: string[] }[] = [
  { label: 'All Policies', backendTypes: [] },
  { label: 'Spending Limits', backendTypes: ['amount_limit', 'category_limit'] },
  { label: 'Per Diem', backendTypes: ['meal_cap', 'hotel_cap', 'mileage_rate'] },
  { label: 'VAT Rules', backendTypes: ['vat_rule'] },
  { label: 'Approval Rules', backendTypes: ['approval_required'] },
  { label: 'Document Rules', backendTypes: ['required_fields', 'category_restriction'] },
]

const POLICY_TYPE_OPTIONS = [
  { value: 'amount_limit', label: 'Spending Limit' },
  { value: 'meal_cap', label: 'Per Diem (Meal)' },
  { value: 'hotel_cap', label: 'Per Diem (Hotel)' },
  { value: 'mileage_rate', label: 'Mileage Rate' },
  { value: 'approval_required', label: 'Approval Required' },
  { value: 'required_fields', label: 'Document / Receipt Required' },
  { value: 'category_restriction', label: 'Category Restriction' },
  { value: 'category_limit', label: 'Category Limit' },
]

const TEMPLATES = [
  { name: 'URSSAF Per Diem', desc: 'Standard meal rates', icon: faUtensils, bg: 'bg-blue-50', iconColor: 'text-infoBlue', hoverBg: 'group-hover:bg-primary', hoverIcon: 'group-hover:text-white' },
  { name: 'French VAT Rules', desc: 'Category-based VAT', icon: faPercent, bg: 'bg-green-50', iconColor: 'text-successGreen', hoverBg: 'group-hover:bg-successGreen', hoverIcon: 'group-hover:text-white' },
  { name: 'Meal Limits', desc: 'Daily/per-meal caps', icon: faEuroSign, bg: 'bg-amber-50', iconColor: 'text-warningAmber', hoverBg: 'group-hover:bg-warningAmber', hoverIcon: 'group-hover:text-white' },
  { name: 'Hotel Caps', desc: 'City-based limits', icon: faHotel, bg: 'bg-purple-50', iconColor: 'text-purple-600', hoverBg: 'group-hover:bg-purple-600', hoverIcon: 'group-hover:text-white' },
  { name: 'Mileage Rates', desc: 'Government rates', icon: faCar, bg: 'bg-pink-50', iconColor: 'text-pink-600', hoverBg: 'group-hover:bg-pink-600', hoverIcon: 'group-hover:text-white' },
]

function policyScopeDisplay(policy: AdminPolicy): string {
  const r = policy.policy_rules || {}
  if (typeof r.max_amount === 'number') return `>€${r.max_amount}`
  if (typeof r.amount_limit === 'number') return `>€${r.amount_limit}`
  if (r.category_ids && Array.isArray(r.category_ids)) return `${(r.category_ids as unknown[]).length} categories`
  if (r.scope) return String(r.scope)
  return 'All'
}

function formatModified(updatedAt: string): string {
  if (!updatedAt) return ''
  const d = new Date(updatedAt)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffDays = Math.floor(diffMs / (24 * 60 * 60 * 1000))
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return '1 day ago'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
  return `${Math.floor(diffDays / 30)} months ago`
}

export default function PoliciesPage() {
  const [policyTypeTab, setPolicyTypeTab] = useState(0)
  const [policies, setPolicies] = useState<AdminPolicy[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [selectedPolicyId, setSelectedPolicyId] = useState<string | null>(null)
  const [policySearch, setPolicySearch] = useState('')
  const [saveLoading, setSaveLoading] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [menuPolicyId, setMenuPolicyId] = useState<string | null>(null)

  const selectedPolicy = policies.find((p) => p.id === selectedPolicyId) || null
  const tabFilter = POLICY_TYPE_TABS[policyTypeTab]
  const filteredPolicies = tabFilter.backendTypes.length
    ? policies.filter((p) => tabFilter.backendTypes.includes(p.policy_type))
    : policies
  const searchFiltered = policySearch.trim()
    ? filteredPolicies.filter(
        (p) =>
          p.name.toLowerCase().includes(policySearch.trim().toLowerCase()) ||
          (p.description || '').toLowerCase().includes(policySearch.trim().toLowerCase())
      )
    : filteredPolicies

  const loadPolicies = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const list = await adminAPI.listPolicies()
      setPolicies(list)
      if (!isCreating) {
        if (list.length && !selectedPolicyId) setSelectedPolicyId(list[0].id)
        if (selectedPolicyId && !list.some((p) => p.id === selectedPolicyId)) setSelectedPolicyId(list[0]?.id ?? null)
      }
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, 'Failed to load policies'))
      setPolicies([])
    } finally {
      setLoading(false)
    }
  }, [selectedPolicyId, isCreating])

  useEffect(() => {
    loadPolicies()
  }, [loadPolicies])

  const handleSubmitPolicy = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = e.currentTarget
    const name = (form.querySelector('[name="policyName"]') as HTMLInputElement)?.value?.trim()
    const policyType = (form.querySelector('[name="policyType"]') as HTMLSelectElement)?.value
    const description = (form.querySelector('[name="policyDescription"]') as HTMLTextAreaElement)?.value?.trim() || undefined
    const amountLimit = (form.querySelector('[name="amountLimit"]') as HTMLInputElement)?.value
    const isActive = (form.querySelector('[name="isActive"]') as HTMLSelectElement)?.value === 'active'
    if (!name || !policyType) return
    setSaveLoading(true)
    setError(null)
    setSuccess(null)
    try {
      const policy_rules: Record<string, unknown> =
        selectedPolicy && !isCreating ? { ...(selectedPolicy.policy_rules || {}) } : {}
      if (amountLimit && !Number.isNaN(Number(amountLimit))) policy_rules.max_amount = Number(amountLimit)
      else if (selectedPolicy && !isCreating) delete policy_rules.max_amount

      if (isCreating || !selectedPolicy) {
        await adminAPI.createPolicy({ name, description, policy_type: policyType, policy_rules })
        await loadPolicies()
        // Reset form to blank for next policy
        form.reset()
        setIsCreating(true)
        setSuccess('Policy created and activated successfully.')
      } else {
        await adminAPI.updatePolicy(selectedPolicy.id, {
          name,
          description: description ?? null,
          policy_type: policyType,
          policy_rules,
          is_active: isActive,
        })
        await loadPolicies()
        setSuccess('Policy updated successfully.')
      }
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, isCreating ? 'Failed to create policy' : 'Failed to update policy'))
    } finally {
      setSaveLoading(false)
    }
  }

  const handleDeletePolicy = async (policyId: string) => {
    setError(null)
    setSuccess(null)
    try {
      await adminAPI.deletePolicy(policyId)
      setMenuPolicyId(null)
      if (selectedPolicyId === policyId) setSelectedPolicyId(policies.find((p) => p.id !== policyId)?.id ?? null)
      await loadPolicies()
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, 'Failed to delete policy'))
    }
  }

  const handleToggleActive = async (policy: AdminPolicy) => {
    setError(null)
    setSuccess(null)
    try {
      await adminAPI.updatePolicy(policy.id, { is_active: !policy.is_active })
      setMenuPolicyId(null)
      await loadPolicies()
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, 'Failed to update policy status'))
    }
  }

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">Policy Builder</h1>
            <p className="text-textSecondary">Configure expense policies and compliance rules</p>
          </div>
          <div className="flex items-center space-x-3">
            <button type="button" className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
              <FontAwesomeIcon icon={faDownload} />
              <span>Export</span>
            </button>
            <button type="button" className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
              <FontAwesomeIcon icon={faFileImport} />
              <span>Import</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setIsCreating(true)
                setSelectedPolicyId(null)
              }}
              className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2"
            >
              <FontAwesomeIcon icon={faPlus} />
              <span>Create Policy</span>
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-4 flex-wrap gap-2">
          {POLICY_TYPE_TABS.map((tab, i) => (
            <button
              key={tab.label}
              onClick={() => setPolicyTypeTab(i)}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                policyTypeTab === i ? 'bg-primary text-white' : 'text-textSecondary hover:bg-gray-50'
              }`}
            >
              {tab.label}
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
                <h2 className="text-xl font-semibold text-textPrimary mb-1">French Compliance Templates</h2>
                <p className="text-sm text-textSecondary">Pre-configured policies for French regulations</p>
              </div>
            </div>
            <button type="button" className="text-sm text-primary hover:text-primaryHover font-medium">View All Templates</button>
          </div>
          <div className="grid grid-cols-5 gap-4">
            {TEMPLATES.map((t, idx) => (
              <button
                key={idx}
                type="button"
                className="bg-white rounded-lg p-4 border border-indigo-100 hover:border-primary transition-all group text-left"
              >
                <div className={`w-10 h-10 ${t.bg} ${t.hoverBg} rounded-lg flex items-center justify-center mb-3 transition-colors`}>
                  <FontAwesomeIcon icon={t.icon} className={`${t.iconColor} ${t.hoverIcon} transition-colors`} />
                </div>
                <h3 className="text-sm font-semibold text-textPrimary mb-1">{t.name}</h3>
                <p className="text-xs text-textSecondary">{t.desc}</p>
              </button>
            ))}
          </div>
        </div>
      </section>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-800 text-sm">
          <FontAwesomeIcon icon={faExclamationTriangle} />
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-successGreen text-sm">
          <FontAwesomeIcon icon={faCheckCircle} />
          {success}
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        <section className="col-span-1">
          <div className="bg-surface rounded-xl border border-borderColor shadow-sm">
            <div className="p-6 border-b border-borderColor">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-textPrimary">Active Policies</h2>
                <span className="text-xs font-medium text-successGreen bg-green-50 px-2 py-1 rounded-full">
                  {searchFiltered.length} {policyTypeTab === 0 ? 'Total' : 'Filtered'}
                </span>
              </div>
              <div className="relative">
                <FontAwesomeIcon icon={faSearch} className="absolute left-3 top-1/2 -translate-y-1/2 text-textMuted text-sm" />
                <input
                  type="text"
                  placeholder="Search policies..."
                  value={policySearch}
                  onChange={(e) => setPolicySearch(e.target.value)}
                  className="w-full h-10 pl-9 pr-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>
            </div>
            <div className="overflow-y-auto max-h-[600px]">
              {loading ? (
                <div className="flex items-center justify-center py-12 text-textSecondary">
                  <FontAwesomeIcon icon={faSpinner} spin className="mr-2" />
                  Loading...
                </div>
              ) : (
                searchFiltered.map((policy) => (
                  <div
                    key={policy.id}
                    onClick={() => {
                      setSelectedPolicyId(policy.id)
                      setIsCreating(false)
                    }}
                    className={`p-4 border-b border-borderColor hover:bg-gray-50 cursor-pointer transition-colors ${
                      selectedPolicyId === policy.id ? 'bg-indigo-50 border-l-4 border-l-primary' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="text-sm font-semibold text-textPrimary mb-1">{policy.name}</h3>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-medium text-successGreen bg-green-50 px-2 py-1 rounded-full">
                            {policy.policy_type}
                          </span>
                          <span className="text-xs text-textMuted">• {policyScopeDisplay(policy)}</span>
                        </div>
                      </div>
                      <div className="relative flex items-center gap-1">
                        {menuPolicyId === policy.id && (
                          <div
                            className="absolute right-0 mt-6 w-40 bg-white border border-borderColor rounded-lg shadow-md z-10"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <button
                              type="button"
                              className="w-full text-left px-3 py-2 text-xs hover:bg-gray-50"
                              onClick={() => handleToggleActive(policy)}
                            >
                              Set {policy.is_active ? 'Inactive' : 'Active'}
                            </button>
                            <button
                              type="button"
                              className="w-full text-left px-3 py-2 text-xs text-errorRed hover:bg-red-50"
                              onClick={() => handleDeletePolicy(policy.id)}
                            >
                              Delete
                            </button>
                          </div>
                        )}
                        <button
                          type="button"
                          className="text-textMuted hover:text-textPrimary"
                          onClick={(e) => {
                            e.stopPropagation()
                            setMenuPolicyId((prev) => (prev === policy.id ? null : policy.id))
                          }}
                        >
                          <FontAwesomeIcon icon={faEllipsisV} />
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-xs text-textMuted">
                      <span>Modified {formatModified(policy.updated_at)}</span>
                      <span className={policy.is_active ? 'text-successGreen font-medium' : 'text-warningAmber font-medium'}>
                        {policy.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>

        <section className="col-span-2">
          <div className="bg-surface rounded-xl border border-borderColor shadow-sm">
            <div className="p-6 border-b border-borderColor">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-textPrimary mb-1">
                    {isCreating || !selectedPolicy ? 'Create Policy' : 'Policy Editor'}
                  </h2>
                  <p className="text-sm text-textSecondary">
                    {isCreating || !selectedPolicy
                      ? 'Define a new expense policy.'
                      : 'Configure policy details and rules.'}
                  </p>
                </div>
              </div>
            </div>
            <div className="p-6 overflow-y-auto max-h-[600px]">
              {(isCreating || selectedPolicy) ? (
                <form onSubmit={handleSubmitPolicy} className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-textPrimary mb-4">Basic Information</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-textPrimary mb-2">Policy Name *</label>
                        <input
                          name="policyName"
                          type="text"
                          defaultValue={selectedPolicy?.name ?? ''}
                          required
                          className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-textPrimary mb-2">Policy Type *</label>
                        <select
                          name="policyType"
                          defaultValue={selectedPolicy?.policy_type ?? POLICY_TYPE_OPTIONS[0]?.value}
                          className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        >
                          {POLICY_TYPE_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-textPrimary mb-2">Status</label>
                        <select
                          name="isActive"
                          defaultValue={selectedPolicy?.is_active === false ? 'inactive' : 'active'}
                          className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        >
                          <option value="active">Active</option>
                          <option value="inactive">Inactive</option>
                        </select>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-textPrimary mb-4">Scope & Conditions</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-textPrimary mb-2">Amount / Limit (€)</label>
                        <input
                          name="amountLimit"
                          type="number"
                          placeholder="e.g. 100"
                          defaultValue={
                            (selectedPolicy?.policy_rules?.max_amount ?? selectedPolicy?.policy_rules?.amount_limit) as number | undefined
                          }
                          className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                      </div>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-textPrimary mb-4">Description</h3>
                    <textarea
                      name="policyDescription"
                      rows={3}
                      defaultValue={selectedPolicy?.description ?? ''}
                      placeholder="Describe when this policy applies and any exceptions..."
                      className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                  </div>
                  <div className="flex items-center justify-end gap-2">
                    <button
                      type="submit"
                      disabled={saveLoading}
                      className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium disabled:opacity-50 flex items-center gap-2"
                    >
                      {saveLoading && <FontAwesomeIcon icon={faSpinner} spin />}
                      Save & Activate
                    </button>
                  </div>
                </form>
              ) : (
                <div className="flex flex-col items-center justify-center py-16 text-textMuted">
                  <FontAwesomeIcon icon={faShieldAlt} className="text-4xl mb-4 opacity-50" />
                  <p className="text-sm">Select a policy from the list to edit, or create a new one</p>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </>
  )
}

'use client'

import { useEffect, useState, useMemo } from 'react'
import Badge from '@/components/ui/Badge'
import { useLanguage } from '@/contexts/LanguageContext'
import { expensesAPI } from '@/lib/api'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faCheckSquare,
  faCheck,
  faXmark,
  faClock,
  faCircleNotch,
  faFilter,
  faSort,
  faSortAmountDown,
  faSortAmountUp,
  faExclamationTriangle,
  faCheckDouble,
  faInbox,
  faChevronDown,
} from '@fortawesome/free-solid-svg-icons'

type Expense = {
  id: string
  amount: number
  currency: string
  description?: string | null
  merchant_name?: string | null
  category?: string | null
  expense_date: string
  status: string
  approval_status?: string | null
  submitted_by?: string
  submitted_by_name?: string | null
  submitted_by_email?: string | null
  vat_rate?: number | null
  vat_amount?: number | null
  created_at?: string | null
}

type TabKey = 'all' | 'pending' | 'myqueue' | 'escalated' | 'completed'
type SortField = 'date' | 'amount' | 'name' | 'category'
type SortDir = 'asc' | 'desc'

function formatDate(value: string | Date | null | undefined): string {
  if (!value) return ''
  const d = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatCurrency(amount: number, currency = 'EUR'): string {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(amount)
}

export default function ApprovalsPage() {
  const { t } = useLanguage()
  const [allExpenses, setAllExpenses] = useState<Expense[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionId, setActionId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabKey>('all')
  const [sortField, setSortField] = useState<SortField>('date')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [showSortMenu, setShowSortMenu] = useState(false)
  const [showFilterMenu, setShowFilterMenu] = useState(false)
  const [filterCategory, setFilterCategory] = useState<string>('')
  const [filterAmountMin, setFilterAmountMin] = useState<string>('')
  const [filterAmountMax, setFilterAmountMax] = useState<string>('')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [bulkActing, setBulkActing] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  // Load ALL expenses (pending + approved + rejected)
  const loadAll = async () => {
    setLoading(true)
    setError(null)
    try {
      // Load pending approvals
      const pendingRes = await expensesAPI.pendingApprovals({ page: 1, page_size: 100 })
      const pendingData = Array.isArray(pendingRes?.data) ? pendingRes.data : Array.isArray(pendingRes) ? pendingRes : []

      // Also load all expenses to get approved/rejected ones
      const allRes = await expensesAPI.list({ page: 1, page_size: 100 })
      const allData = Array.isArray(allRes?.data) ? allRes.data : Array.isArray(allRes) ? allRes : []

      // Merge: pending approvals + approved/rejected from all expenses
      const pendingIds = new Set(pendingData.map((e: any) => e.id))
      const completed = allData.filter((e: any) =>
        !pendingIds.has(e.id) && (e.status === 'approved' || e.status === 'rejected')
      )

      setAllExpenses([...pendingData, ...completed] as Expense[])
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Erreur de chargement')
      setAllExpenses([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void loadAll() }, [])

  // Auto-dismiss toast
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000)
      return () => clearTimeout(timer)
    }
  }, [toast])

  // Categorize expenses
  const pending = useMemo(() => allExpenses.filter(e => e.status === 'submitted' || e.status === 'pending' || e.approval_status === 'pending'), [allExpenses])
  const myQueue = useMemo(() => pending.filter((_, i) => i % 2 === 0), [pending]) // Simulate "my queue" as even-indexed pending
  const escalated = useMemo(() => pending.filter(e => Number(e.amount) > 200), [pending]) // Simulate escalated as high-amount
  const completed = useMemo(() => allExpenses.filter(e => e.status === 'approved' || e.status === 'rejected'), [allExpenses])

  // Get items for active tab
  const tabItems = useMemo(() => {
    switch (activeTab) {
      case 'pending': return pending
      case 'myqueue': return myQueue
      case 'escalated': return escalated
      case 'completed': return completed
      default: return allExpenses
    }
  }, [activeTab, allExpenses, pending, myQueue, escalated, completed])

  // Apply filters
  const filtered = useMemo(() => {
    let result = [...tabItems]

    if (filterCategory) {
      result = result.filter(e => (e.category || '').toLowerCase().includes(filterCategory.toLowerCase()))
    }
    if (filterAmountMin) {
      result = result.filter(e => e.amount >= Number(filterAmountMin))
    }
    if (filterAmountMax) {
      result = result.filter(e => e.amount <= Number(filterAmountMax))
    }

    return result
  }, [tabItems, filterCategory, filterAmountMin, filterAmountMax])

  // Apply sorting
  const sorted = useMemo(() => {
    const result = [...filtered]
    const dir = sortDir === 'asc' ? 1 : -1

    result.sort((a, b) => {
      switch (sortField) {
        case 'amount': return (a.amount - b.amount) * dir
        case 'name': return ((a.merchant_name || a.description || '').localeCompare(b.merchant_name || b.description || '')) * dir
        case 'category': return ((a.category || '').localeCompare(b.category || '')) * dir
        case 'date':
        default: return (new Date(a.expense_date).getTime() - new Date(b.expense_date).getTime()) * dir
      }
    })
    return result
  }, [filtered, sortField, sortDir])

  // Actions
  const handleApprove = async (id: string) => {
    setActionId(id)
    try {
      await expensesAPI.approve(id)
      setToast({ message: 'Depense approuvee avec succes', type: 'success' })
      await loadAll()
    } catch (err: any) {
      setToast({ message: err?.response?.data?.detail || 'Erreur lors de l\'approbation', type: 'error' })
    } finally {
      setActionId(null)
    }
  }

  const handleReject = async (id: string) => {
    setActionId(id)
    try {
      await expensesAPI.reject(id, 'Rejetee depuis la page d\'approbation')
      setToast({ message: 'Depense rejetee', type: 'success' })
      await loadAll()
    } catch (err: any) {
      setToast({ message: err?.response?.data?.detail || 'Erreur lors du rejet', type: 'error' })
    } finally {
      setActionId(null)
    }
  }

  const handleBulkApprove = async () => {
    if (selectedIds.size === 0) return
    setBulkActing(true)
    let successCount = 0
    for (const id of selectedIds) {
      try {
        await expensesAPI.approve(id)
        successCount++
      } catch { /* continue */ }
    }
    setToast({ message: `${successCount}/${selectedIds.size} depenses approuvees`, type: 'success' })
    setSelectedIds(new Set())
    setBulkActing(false)
    await loadAll()
  }

  const toggleSelect = (id: string) => {
    const next = new Set(selectedIds)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSelectedIds(next)
  }

  const toggleSelectAll = () => {
    const pendingInView = sorted.filter(e => e.status === 'submitted' || e.status === 'pending')
    if (selectedIds.size === pendingInView.length && pendingInView.length > 0) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(pendingInView.map(e => e.id)))
    }
  }

  const getStatusBadge = (exp: Expense) => {
    if (exp.status === 'approved') return <Badge variant="success" icon={faCheck}>Approuve</Badge>
    if (exp.status === 'rejected') return <Badge variant="error" icon={faXmark}>Rejete</Badge>
    if (exp.status === 'draft') return <Badge variant="default">Brouillon</Badge>
    return <Badge variant="warning" icon={faClock}>En attente</Badge>
  }

  const isPending = (exp: Expense) => exp.status === 'submitted' || exp.status === 'pending'

  const categories = useMemo(() => {
    const cats = new Set(allExpenses.map(e => e.category).filter(Boolean))
    return Array.from(cats) as string[]
  }, [allExpenses])

  const tabs: { key: TabKey; label: string; count: number; color: string }[] = [
    { key: 'all', label: 'Tout', count: allExpenses.length, color: 'bg-indigo-50 text-primary' },
    { key: 'pending', label: 'En attente', count: pending.length, color: 'bg-yellow-50 text-yellow-700' },
    { key: 'myqueue', label: 'Ma file', count: myQueue.length, color: 'bg-blue-50 text-blue-700' },
    { key: 'escalated', label: 'Escalade', count: escalated.length, color: 'bg-red-50 text-red-700' },
    { key: 'completed', label: 'Terminees', count: completed.length, color: 'bg-green-50 text-green-700' },
  ]

  return (
    <div className="relative">
      {/* Header */}
      <section className="mb-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-textPrimary">Approbations</h1>
            {pending.length > 0 && (
              <span className="bg-red-500 text-white rounded-full px-3 py-0.5 text-sm font-semibold">{pending.length}</span>
            )}
          </div>
          <div className="flex items-center space-x-3">
            {/* Filter */}
            <div className="relative">
              <button
                onClick={() => { setShowFilterMenu(!showFilterMenu); setShowSortMenu(false) }}
                className={`h-10 px-4 border rounded-lg text-sm font-medium flex items-center space-x-2 ${filterCategory || filterAmountMin || filterAmountMax ? 'border-primary text-primary bg-indigo-50' : 'border-borderColor text-textSecondary hover:bg-gray-50'}`}
              >
                <FontAwesomeIcon icon={faFilter} />
                <span>Filtrer</span>
                {(filterCategory || filterAmountMin || filterAmountMax) && <span className="w-2 h-2 bg-primary rounded-full" />}
              </button>
              {showFilterMenu && (
                <div className="absolute right-0 top-full mt-1 w-72 bg-white border border-borderColor rounded-xl shadow-lg z-50 p-4">
                  <div className="text-sm font-semibold text-textPrimary mb-3">Filtres</div>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs text-textSecondary mb-1">Categorie</label>
                      <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}
                        className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm">
                        <option value="">Toutes</option>
                        {categories.map(c => <option key={c} value={c}>{c}</option>)}
                      </select>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs text-textSecondary mb-1">Montant min</label>
                        <input type="number" value={filterAmountMin} onChange={(e) => setFilterAmountMin(e.target.value)}
                          placeholder="0" className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" />
                      </div>
                      <div>
                        <label className="block text-xs text-textSecondary mb-1">Montant max</label>
                        <input type="number" value={filterAmountMax} onChange={(e) => setFilterAmountMax(e.target.value)}
                          placeholder="10000" className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" />
                      </div>
                    </div>
                    <div className="flex justify-between pt-2">
                      <button onClick={() => { setFilterCategory(''); setFilterAmountMin(''); setFilterAmountMax('') }}
                        className="text-xs text-textSecondary hover:text-textPrimary">Reinitialiser</button>
                      <button onClick={() => setShowFilterMenu(false)}
                        className="text-xs text-primary font-medium">Appliquer</button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Sort */}
            <div className="relative">
              <button
                onClick={() => { setShowSortMenu(!showSortMenu); setShowFilterMenu(false) }}
                className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2"
              >
                <FontAwesomeIcon icon={sortDir === 'desc' ? faSortAmountDown : faSortAmountUp} />
                <span>Trier</span>
                <FontAwesomeIcon icon={faChevronDown} className="text-xs" />
              </button>
              {showSortMenu && (
                <div className="absolute right-0 top-full mt-1 w-56 bg-white border border-borderColor rounded-xl shadow-lg z-50 py-1">
                  {([
                    { field: 'date' as SortField, label: 'Date' },
                    { field: 'amount' as SortField, label: 'Montant' },
                    { field: 'name' as SortField, label: 'Nom' },
                    { field: 'category' as SortField, label: 'Categorie' },
                  ]).map(opt => (
                    <button key={opt.field}
                      onClick={() => {
                        if (sortField === opt.field) setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
                        else { setSortField(opt.field); setSortDir('desc') }
                        setShowSortMenu(false)
                      }}
                      className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center justify-between ${sortField === opt.field ? 'text-primary font-medium' : 'text-textSecondary'}`}
                    >
                      <span>{opt.label}</span>
                      {sortField === opt.field && (
                        <FontAwesomeIcon icon={sortDir === 'desc' ? faSortAmountDown : faSortAmountUp} className="text-xs" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Bulk Approve */}
            <button
              onClick={handleBulkApprove}
              disabled={selectedIds.size === 0 || bulkActing}
              className="h-10 px-4 bg-primary hover:bg-primaryHover disabled:opacity-50 text-white rounded-lg text-sm font-medium flex items-center space-x-2"
            >
              {bulkActing ? <FontAwesomeIcon icon={faCircleNotch} className="animate-spin" /> : <FontAwesomeIcon icon={faCheckDouble} />}
              <span>{selectedIds.size > 0 ? `Approuver (${selectedIds.size})` : 'Approuver'}</span>
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center space-x-1 border-b border-borderColor">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => { setActiveTab(tab.key); setSelectedIds(new Set()) }}
              className={`px-4 py-3 text-sm font-medium rounded-t-lg transition-colors ${
                activeTab === tab.key
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-textSecondary hover:text-textPrimary hover:bg-gray-50'
              }`}
            >
              {tab.label}
              <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${activeTab === tab.key ? tab.color : 'bg-gray-100 text-textMuted'}`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>
      </section>

      {/* Error */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
          <FontAwesomeIcon icon={faExclamationTriangle} />
          {error}
        </div>
      )}

      {/* Escalated warning */}
      {activeTab === 'escalated' && escalated.length > 0 && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <FontAwesomeIcon icon={faExclamationTriangle} className="text-red-500 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-900">{escalated.length} depense(s) necessitant une attention urgente</p>
            <p className="text-xs text-red-700 mt-1">Ces depenses depassent le seuil d'approbation automatique (200 EUR) et necessitent une validation manuelle.</p>
          </div>
        </div>
      )}

      {/* Table */}
      <section className="bg-white rounded-xl border border-borderColor overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-borderColor bg-gray-50">
                {activeTab !== 'completed' && (
                  <th className="py-3 px-4 w-10">
                    <input type="checkbox" checked={selectedIds.size > 0 && selectedIds.size === sorted.filter(isPending).length}
                      onChange={toggleSelectAll} className="w-4 h-4 text-primary rounded border-borderColor" />
                  </th>
                )}
                <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase">Depense</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase">Soumis par</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase">Date</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase">Categorie</th>
                <th className="text-center py-3 px-4 text-xs font-semibold text-textMuted uppercase">Statut</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-textMuted uppercase">Montant</th>
                {activeTab !== 'completed' && (
                  <th className="text-right py-3 px-4 text-xs font-semibold text-textMuted uppercase">Actions</th>
                )}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                [...Array(5)].map((_, i) => (
                  <tr key={i} className="border-b border-borderColor animate-pulse">
                    {activeTab !== 'completed' && <td className="py-4 px-4"><span className="inline-block w-4 h-4 bg-gray-200 rounded" /></td>}
                    <td className="py-4 px-4"><span className="inline-block h-4 w-32 bg-gray-200 rounded" /></td>
                    <td className="py-4 px-4"><span className="inline-block h-4 w-24 bg-gray-200 rounded" /></td>
                    <td className="py-4 px-4"><span className="inline-block h-4 w-20 bg-gray-200 rounded" /></td>
                    <td className="py-4 px-4"><span className="inline-block h-4 w-16 bg-gray-200 rounded" /></td>
                    <td className="py-4 px-4"><span className="inline-block h-5 w-20 bg-gray-200 rounded mx-auto" /></td>
                    <td className="py-4 px-4"><span className="inline-block h-4 w-16 bg-gray-200 rounded ml-auto" /></td>
                    {activeTab !== 'completed' && <td className="py-4 px-4" />}
                  </tr>
                ))
              ) : sorted.length === 0 ? (
                <tr>
                  <td colSpan={activeTab !== 'completed' ? 8 : 6} className="py-16 text-center">
                    <FontAwesomeIcon icon={faInbox} className="text-4xl text-gray-300 mb-3" />
                    <p className="text-textSecondary text-sm">
                      {activeTab === 'completed' ? 'Aucune depense traitee' :
                       activeTab === 'escalated' ? 'Aucune depense escaladee' :
                       activeTab === 'myqueue' ? 'Votre file d\'attente est vide' :
                       'Aucune depense en attente d\'approbation'}
                    </p>
                  </td>
                </tr>
              ) : (
                sorted.map((exp) => {
                  const title = exp.description || exp.merchant_name || 'Depense'
                  const submittedBy = exp.submitted_by_name || exp.submitted_by_email || 'Utilisateur'
                  const isActing = actionId === exp.id
                  const isSelected = selectedIds.has(exp.id)
                  const canAct = isPending(exp)

                  return (
                    <tr key={exp.id} className={`border-b border-borderColor hover:bg-gray-50 ${isSelected ? 'bg-indigo-50/50' : ''}`}>
                      {activeTab !== 'completed' && (
                        <td className="py-4 px-4">
                          {canAct && (
                            <input type="checkbox" checked={isSelected} onChange={() => toggleSelect(exp.id)}
                              className="w-4 h-4 text-primary rounded border-borderColor" />
                          )}
                        </td>
                      )}
                      <td className="py-4 px-4">
                        <div className="text-sm font-medium text-textPrimary">{title}</div>
                        <div className="text-xs text-textSecondary">{exp.merchant_name || '—'}</div>
                      </td>
                      <td className="py-4 px-4 text-sm text-textPrimary">{submittedBy}</td>
                      <td className="py-4 px-4 text-sm text-textSecondary">{formatDate(exp.expense_date)}</td>
                      <td className="py-4 px-4">
                        {exp.category && (
                          <span className="text-xs px-2 py-1 bg-gray-100 rounded-full text-textSecondary">{exp.category}</span>
                        )}
                      </td>
                      <td className="py-4 px-4 text-center">{getStatusBadge(exp)}</td>
                      <td className="py-4 px-4 text-right text-sm font-semibold text-textPrimary">
                        {formatCurrency(exp.amount, exp.currency)}
                      </td>
                      {activeTab !== 'completed' && (
                        <td className="py-4 px-4 text-right">
                          {canAct && (
                            <div className="flex justify-end space-x-2">
                              <button onClick={() => handleApprove(exp.id)} disabled={isActing}
                                className="h-8 px-3 bg-green-500 hover:bg-green-600 disabled:opacity-50 text-white rounded-lg text-xs font-medium flex items-center space-x-1">
                                {isActing ? <FontAwesomeIcon icon={faCircleNotch} className="animate-spin" /> : <FontAwesomeIcon icon={faCheck} />}
                                <span>Approuver</span>
                              </button>
                              <button onClick={() => handleReject(exp.id)} disabled={isActing}
                                className="h-8 px-3 bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white rounded-lg text-xs font-medium flex items-center space-x-1">
                                {isActing ? <FontAwesomeIcon icon={faCircleNotch} className="animate-spin" /> : <FontAwesomeIcon icon={faXmark} />}
                                <span>Rejeter</span>
                              </button>
                            </div>
                          )}
                        </td>
                      )}
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        {!loading && sorted.length > 0 && (
          <div className="px-4 py-3 border-t border-borderColor bg-gray-50 flex items-center justify-between text-sm text-textSecondary">
            <span>{sorted.length} depense(s) affichee(s)</span>
            <span>
              Tri: {sortField === 'date' ? 'Date' : sortField === 'amount' ? 'Montant' : sortField === 'name' ? 'Nom' : 'Categorie'}
              {' '}({sortDir === 'desc' ? 'decroissant' : 'croissant'})
            </span>
          </div>
        )}
      </section>

      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-6 right-6 z-50 px-5 py-3 rounded-xl shadow-lg text-sm font-medium text-white ${toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'}`}>
          {toast.message}
        </div>
      )}

      {/* Click outside to close menus */}
      {(showSortMenu || showFilterMenu) && (
        <div className="fixed inset-0 z-40" onClick={() => { setShowSortMenu(false); setShowFilterMenu(false) }} />
      )}
    </div>
  )
}

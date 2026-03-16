'use client'

import { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import Badge from '@/components/ui/Badge'
import { useLanguage } from '@/contexts/LanguageContext'
import { TableRowSkeleton } from '@/components/ui/Skeleton'
import { useExpenses } from '@/lib/hooks'
import { reportAPI, getAuthErrorMessage } from '@/lib/api'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faReceipt,
  faEuroSign,
  faClock,
  faPlus,
  faDownload,
  faSearch,
  faSliders,
  faSort,
  faPlane,
  faUtensils,
  faHotel,
  faCar,
  faLaptop,
  faCheck,
  faEllipsisV,
  faFileText,
  faTrash,
  faTimes,
  faPaperPlane,
  faFile,
} from '@fortawesome/free-solid-svg-icons'

const CATEGORY_MAP: Record<string, { icon: any; variant: 'info' | 'success' | 'purple' | 'orange' | 'pink' }> = {
  travel: { icon: faPlane, variant: 'info' },
  meals: { icon: faUtensils, variant: 'success' },
  accommodation: { icon: faHotel, variant: 'purple' },
  transport: { icon: faCar, variant: 'orange' },
  office: { icon: faLaptop, variant: 'pink' },
  training: { icon: faFileText, variant: 'info' },
}

function getDisplayStatus(exp: { status?: string; approval_status?: string }, t: (k: string) => string) {
  if (exp.status === 'draft') return { label: t('statusLabel.draft'), variant: 'default' as const, icon: faFile }
  if (exp.approval_status === 'approved') return { label: t('statusLabel.approved'), variant: 'success' as const, icon: faCheck }
  if (exp.approval_status === 'rejected') return { label: t('statusLabel.rejected'), variant: 'error' as const, icon: faTimes }
  return { label: t('statusLabel.pending'), variant: 'warning' as const, icon: faPaperPlane }
}

function formatDate(d: string | Date, locale: string) {
  if (!d) return ''
  const date = typeof d === 'string' ? new Date(d) : d
  return date.toLocaleDateString(locale === 'fr' ? 'fr-FR' : 'en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

const pageSize = 20

type ExpenseRow = {
  id: string
  category?: string
  status?: string
  approval_status?: string
  expense_date?: string
  merchant_name?: string
  description?: string
  amount?: number
  vat_amount?: number
}

export default function ExpensesPage() {
  const router = useRouter()
  const { locale, t, localeVersion } = useLanguage()
  void localeVersion // force re-render when language changes
  const [selectedCount, setSelectedCount] = useState(0)
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [bulkActionLoading, setBulkActionLoading] = useState(false)
  const [showBulkActions, setShowBulkActions] = useState(false)
  const [page, setPage] = useState(1)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterDateStart, setFilterDateStart] = useState('')
  const [filterDateEnd, setFilterDateEnd] = useState('')
  const [filterCategory, setFilterCategory] = useState('All Categories')
  const [filterStatus, setFilterStatus] = useState('All Status')
  const [filterAmountMin, setFilterAmountMin] = useState(0)
  const [filterAmountMax, setFilterAmountMax] = useState(5000)
  const { expenses, total, isLoading: loading } = useExpenses({ page, page_size: pageSize })

  const displayExpenses = useMemo(() => (expenses as ExpenseRow[]).map((exp) => {
    const cat = CATEGORY_MAP[exp.category || ''] || { icon: faReceipt, variant: 'info' as const }
    const statusInfo = getDisplayStatus(exp, t)
    const categoryLabel = exp.category || t('common.other')
    return {
      id: exp.id,
      date: formatDate(exp.expense_date ?? '', locale),
      merchant: exp.merchant_name || '—',
      category: categoryLabel,
      categoryIcon: cat.icon,
      categoryVariant: cat.variant,
      description: exp.description || '—',
      amount: `€${Number(exp.amount || 0).toFixed(2)}`,
      vat: exp.vat_amount != null ? `€${Number(exp.vat_amount).toFixed(2)}` : '—',
      status: statusInfo.label,
      statusVariant: statusInfo.variant,
      statusIcon: statusInfo.icon,
      receiptImage: null,
    }
  }), [expenses, t, locale])

  const filteredExpenses = useMemo(() => {
    return displayExpenses.filter((exp) => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase()
        if (!exp.description.toLowerCase().includes(q) && !exp.merchant.toLowerCase().includes(q)) return false
      }
      if (filterCategory && filterCategory !== 'All Categories' && exp.category.toLowerCase() !== filterCategory.toLowerCase()) return false
      if (filterStatus && filterStatus !== 'All Status' && exp.status !== filterStatus) return false
      if (filterDateStart) {
        const expDate = new Date(exp.date)
        const startDate = new Date(filterDateStart)
        if (!isNaN(expDate.getTime()) && !isNaN(startDate.getTime()) && expDate < startDate) return false
      }
      if (filterDateEnd) {
        const expDate = new Date(exp.date)
        const endDate = new Date(filterDateEnd)
        if (!isNaN(expDate.getTime()) && !isNaN(endDate.getTime()) && expDate > endDate) return false
      }
      const amountNum = parseFloat(exp.amount.replace('€', '').replace(',', ''))
      if (!isNaN(amountNum)) {
        if (amountNum < filterAmountMin) return false
        if (amountNum > filterAmountMax) return false
      }
      return true
    })
  }, [displayExpenses, searchQuery, filterCategory, filterStatus, filterDateStart, filterDateEnd, filterAmountMin, filterAmountMax])

  const clearAllFilters = () => {
    setSearchQuery('')
    setFilterDateStart('')
    setFilterDateEnd('')
    setFilterCategory('All Categories')
    setFilterStatus('All Status')
    setFilterAmountMin(0)
    setFilterAmountMax(5000)
  }

  const hasActiveFilters = searchQuery || filterDateStart || filterDateEnd || filterCategory !== 'All Categories' || filterStatus !== 'All Status' || filterAmountMin > 0 || filterAmountMax < 5000

  const handleAddToReport = async () => {
    if (!selectedIds.length) return

    try {
      setBulkActionLoading(true)

      const now = new Date()
      const periodStart = new Date(now.getFullYear(), now.getMonth(), 1)
      const periodEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0)
      const period_start_date = periodStart.toISOString().slice(0, 10)
      const period_end_date = periodEnd.toISOString().slice(0, 10)
      const monthLabel = now.toLocaleString('default', { month: 'long', year: 'numeric' })

      const payload = {
        report_type: 'period',
        title: `Expenses ${monthLabel}`,
        description: 'Created from Expenses list selection.',
        period_start_date,
        period_end_date,
        period_type: 'monthly',
        expense_ids: selectedIds,
      }

      const created = await reportAPI.create(payload)
      const reportId = created?.data?.id ?? created?.id

      setSelectedCount(0)
      setSelectedIds([])
      setShowBulkActions(false)

      if (reportId) {
        router.push(`/reports/${reportId}`)
      } else {
        router.push('/reports')
      }
    } catch (err: any) {
      const message = getAuthErrorMessage(err, 'Failed to create expense report.')
      alert(message)
    } finally {
      setBulkActionLoading(false)
    }
  }

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">{t('expenses.myExpenses')}</h1>
            <p className="text-textSecondary">{t('expenses.manageAndTrack')}</p>
          </div>
          <div className="flex items-center space-x-3">
            <button className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
              <FontAwesomeIcon icon={faDownload} />
              <span>{t('common.export')}</span>
            </button>
            <button
              onClick={() => router.push('/expenses/new')}
              className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2"
            >
              <FontAwesomeIcon icon={faPlus} />
              <span>{t('common.newExpense')}</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6 mb-6">
          <div className="bg-surface rounded-xl p-5 border border-borderColor">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-textSecondary mb-1">{t('expenses.totalExpenses')}</div>
                <div className="text-2xl font-bold text-textPrimary">{loading ? '—' : total}</div>
              </div>
              <div className="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faReceipt} className="text-primary text-xl" />
              </div>
            </div>
          </div>

          <div className="bg-surface rounded-xl p-5 border border-borderColor">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-textSecondary mb-1">{t('expenses.totalAmount')}</div>
                <div className="text-2xl font-bold text-textPrimary">
                  €{loading ? '—' : (expenses as ExpenseRow[]).reduce((s: number, e) => s + Number(e.amount || 0), 0).toLocaleString(locale === 'fr' ? 'fr-FR' : 'en-GB', { minimumFractionDigits: 2 })}
                </div>
              </div>
              <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faEuroSign} className="text-successGreen text-xl" />
              </div>
            </div>
          </div>

          <div className="bg-surface rounded-xl p-5 border border-borderColor">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-textSecondary mb-1">Pending Approval</div>
                <div className="text-2xl font-bold text-textPrimary">
                  {loading ? '—' : (expenses as ExpenseRow[]).filter((e: ExpenseRow) => e.status === 'submitted' && e.approval_status !== 'approved' && e.approval_status !== 'rejected').length}
                </div>
              </div>
              <div className="w-12 h-12 bg-amber-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faClock} className="text-warningAmber text-xl" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-surface rounded-xl p-6 border border-borderColor mb-6">
        <div className="grid grid-cols-12 gap-4 mb-4">
          <div className="col-span-4">
            <label className="block text-xs font-medium text-textSecondary mb-2">Search</label>
            <div className="relative">
              <FontAwesomeIcon
                icon={faSearch}
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-textMuted"
              />
              <input
                type="text"
                placeholder={t('expenses.searchPlaceholder')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full h-10 pl-10 pr-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </div>

          <div className="col-span-3">
            <label className="block text-xs font-medium text-textSecondary mb-2">Date Range</label>
            <div className="flex items-center space-x-2">
              <input
                type="date"
                value={filterDateStart}
                onChange={(e) => setFilterDateStart(e.target.value)}
                className="flex-1 h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
              <span className="text-textMuted">-</span>
              <input
                type="date"
                value={filterDateEnd}
                onChange={(e) => setFilterDateEnd(e.target.value)}
                className="flex-1 h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </div>

          <div className="col-span-2">
            <label className="block text-xs font-medium text-textSecondary mb-2">Category</label>
            <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)} className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent appearance-none bg-white pr-8">
              <option>All Categories</option>
              <option>Travel</option>
              <option>Meals</option>
              <option>Accommodation</option>
              <option>Transport</option>
              <option>Office Supplies</option>
            </select>
          </div>

          <div className="col-span-2">
            <label className="block text-xs font-medium text-textSecondary mb-2">Status</label>
            <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent appearance-none bg-white pr-8">
              <option>All Status</option>
              <option>Draft</option>
              <option>Submitted</option>
              <option>Approved</option>
              <option>Rejected</option>
              <option>Reimbursed</option>
            </select>
          </div>

          <div className="col-span-1 flex items-end">
            <button className="w-full h-10 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center justify-center">
              <FontAwesomeIcon icon={faSliders} />
            </button>
          </div>
        </div>

        <div className="pt-4 border-t border-borderColor">
          <label className="block text-xs font-medium text-textSecondary mb-3">Amount Range</label>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-textSecondary">€</span>
              <input
                type="number"
                value={filterAmountMin}
                onChange={(e) => setFilterAmountMin(Number(e.target.value))}
                min={0}
                className="w-20 h-8 px-2 border border-borderColor rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div className="flex-1">
              <input
                type="range"
                min={0}
                max={5000}
                value={filterAmountMin}
                onChange={(e) => setFilterAmountMin(Number(e.target.value))}
                className="w-full"
              />
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-textSecondary">€</span>
              <input
                type="number"
                value={filterAmountMax}
                onChange={(e) => setFilterAmountMax(Number(e.target.value))}
                min={0}
                className="w-20 h-8 px-2 border border-borderColor rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
        </div>

        {hasActiveFilters && (
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-borderColor">
          <div className="flex items-center space-x-2 flex-wrap gap-1">
            <span className="text-sm text-textSecondary">Active Filters:</span>
            {searchQuery && (
              <span className="inline-flex items-center text-xs font-medium text-primary bg-indigo-50 px-2 py-1 rounded-full">
                Search: {searchQuery}
                <button className="ml-1.5" onClick={() => setSearchQuery('')}>
                  <FontAwesomeIcon icon={faTimes} className="text-xs" />
                </button>
              </span>
            )}
            {filterDateStart && (
              <span className="inline-flex items-center text-xs font-medium text-primary bg-indigo-50 px-2 py-1 rounded-full">
                From: {filterDateStart}
                <button className="ml-1.5" onClick={() => setFilterDateStart('')}>
                  <FontAwesomeIcon icon={faTimes} className="text-xs" />
                </button>
              </span>
            )}
            {filterDateEnd && (
              <span className="inline-flex items-center text-xs font-medium text-primary bg-indigo-50 px-2 py-1 rounded-full">
                To: {filterDateEnd}
                <button className="ml-1.5" onClick={() => setFilterDateEnd('')}>
                  <FontAwesomeIcon icon={faTimes} className="text-xs" />
                </button>
              </span>
            )}
            {filterCategory !== 'All Categories' && (
              <span className="inline-flex items-center text-xs font-medium text-primary bg-indigo-50 px-2 py-1 rounded-full">
                {filterCategory}
                <button className="ml-1.5" onClick={() => setFilterCategory('All Categories')}>
                  <FontAwesomeIcon icon={faTimes} className="text-xs" />
                </button>
              </span>
            )}
            {filterStatus !== 'All Status' && (
              <span className="inline-flex items-center text-xs font-medium text-primary bg-indigo-50 px-2 py-1 rounded-full">
                {filterStatus}
                <button className="ml-1.5" onClick={() => setFilterStatus('All Status')}>
                  <FontAwesomeIcon icon={faTimes} className="text-xs" />
                </button>
              </span>
            )}
            {(filterAmountMin > 0 || filterAmountMax < 5000) && (
              <span className="inline-flex items-center text-xs font-medium text-primary bg-indigo-50 px-2 py-1 rounded-full">
                €{filterAmountMin} - €{filterAmountMax}
                <button className="ml-1.5" onClick={() => { setFilterAmountMin(0); setFilterAmountMax(5000) }}>
                  <FontAwesomeIcon icon={faTimes} className="text-xs" />
                </button>
              </span>
            )}
          </div>
          <button onClick={clearAllFilters} className="text-sm text-primary hover:text-primaryHover font-medium">Clear All Filters</button>
        </div>
        )}
      </section>

      {showBulkActions && (
        <div className="bg-indigo-50 border border-primary rounded-xl p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-textPrimary">
                <span>{selectedCount}</span> items selected
              </span>
              <button
                onClick={() => {
                  setSelectedCount(0)
                  setShowBulkActions(false)
                }}
                className="text-sm text-primary hover:text-primaryHover font-medium"
              >
                Clear selection
              </button>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleAddToReport}
                disabled={bulkActionLoading || selectedCount === 0}
                className="h-10 px-4 bg-white border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FontAwesomeIcon icon={faFileText} />
                <span>Add to Report</span>
              </button>
              <button className="h-10 px-4 bg-white border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
                <FontAwesomeIcon icon={faDownload} />
                <span>Export Selected</span>
              </button>
              <button className="h-10 px-4 bg-errorRed hover:bg-red-600 text-white rounded-lg text-sm font-medium flex items-center space-x-2">
                <FontAwesomeIcon icon={faTrash} />
                <span>Delete Selected</span>
              </button>
            </div>
          </div>
        </div>
      )}

      <section className="bg-surface rounded-xl border border-borderColor overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-borderColor bg-gray-50">
                <th className="w-8 py-4 px-4">
                  <input
                    type="checkbox"
                    className="w-4 h-4 text-primary border-borderColor rounded focus:ring-primary"
                  />
                </th>
                <th className="w-12 py-4 px-4"></th>
                <th className="text-left py-4 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide cursor-pointer hover:text-textPrimary">
                  {t('common.date')} <FontAwesomeIcon icon={faSort} className="ml-1" />
                </th>
                <th className="text-left py-4 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide cursor-pointer hover:text-textPrimary">
                  {t('common.merchant')} <FontAwesomeIcon icon={faSort} className="ml-1" />
                </th>
                <th className="text-left py-4 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide cursor-pointer hover:text-textPrimary">
                  {t('common.category')} <FontAwesomeIcon icon={faSort} className="ml-1" />
                </th>
                <th className="text-left py-4 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">
                  {t('expenses.description')}
                </th>
                <th className="text-right py-4 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide cursor-pointer hover:text-textPrimary">
                  {t('common.amount')} <FontAwesomeIcon icon={faSort} className="ml-1" />
                </th>
                <th className="text-right py-4 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">
                  {t('expenses.vat')}
                </th>
                <th className="text-center py-4 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide cursor-pointer hover:text-textPrimary">
                  {t('common.status')} <FontAwesomeIcon icon={faSort} className="ml-1" />
                </th>
                <th className="text-right py-4 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">
                  {t('common.actions')}
                </th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                [...Array(5)].map((_, i) => <TableRowSkeleton key={i} cols={10} />)
              ) : filteredExpenses.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-textSecondary">
                    {hasActiveFilters ? 'No expenses match your filters.' : t('expenses.newExpenseToGetStarted')}
                  </td>
                </tr>
              ) : (
              filteredExpenses.map((expense) => (
                <tr key={expense.id} className="border-b border-borderColor hover:bg-gray-50 h-16 group">
                  <td className="py-3 px-4">
                    <input
                      type="checkbox"
                      className="w-4 h-4 text-primary border-borderColor rounded focus:ring-primary"
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedCount((prev) => prev + 1)
                          setSelectedIds((prev) => [...prev, expense.id])
                          setShowBulkActions(true)
                        } else {
                          setSelectedCount((prev) => Math.max(0, prev - 1))
                          setSelectedIds((prev) => prev.filter((id) => id !== expense.id))
                          if (selectedCount <= 1) setShowBulkActions(false)
                        }
                      }}
                    />
                  </td>
                  <td className="py-3 px-4">
                    {expense.receiptImage ? (
                      <img
                        src={expense.receiptImage}
                        alt="Receipt"
                        className="w-12 h-12 object-cover rounded-md border border-borderColor"
                      />
                    ) : (
                      <div className="w-12 h-12 bg-gray-100 rounded-md border border-borderColor flex items-center justify-center">
                        <FontAwesomeIcon icon={faReceipt} className="text-textMuted text-lg" />
                      </div>
                    )}
                  </td>
                  <td className="py-3 px-4 text-sm text-textPrimary whitespace-nowrap">{expense.date}</td>
                  <td className="py-3 px-4 text-sm text-textPrimary font-medium">{expense.merchant}</td>
                  <td className="py-3 px-4">
                    <Badge variant={expense.categoryVariant} icon={expense.categoryIcon}>
                      {expense.category}
                    </Badge>
                  </td>
                  <td className="py-3 px-4 text-sm text-textSecondary max-w-xs truncate" title={expense.description}>
                    {expense.description}
                  </td>
                  <td className="py-3 px-4 text-right text-sm font-medium text-textPrimary">{expense.amount}</td>
                  <td className="py-3 px-4 text-right text-sm text-textSecondary">{expense.vat}</td>
                  <td className="py-3 px-4 text-center">
                    <Badge variant={expense.statusVariant} icon={expense.statusIcon}>
                      {expense.status}
                    </Badge>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => router.push(`/expenses/${expense.id}`)}
                      className="w-8 h-8 flex items-center justify-center text-textMuted hover:text-infoBlue hover:bg-blue-50 rounded-lg"
                      title="View"
                    >
                      <FontAwesomeIcon icon={faEllipsisV} />
                    </button>
                  </td>
                </tr>
              )))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between p-4 border-t border-borderColor">
          <div className="text-sm text-textSecondary">
            {loading ? '—' : `Showing ${filteredExpenses.length} of ${total} expenses`}
          </div>
          <div className="flex items-center space-x-2">
            <button className="w-8 h-8 flex items-center justify-center border border-borderColor rounded-lg text-textMuted hover:bg-gray-50 disabled:opacity-50" disabled>
              <FontAwesomeIcon icon={faSort} className="text-xs rotate-90" />
            </button>
            <button className="w-8 h-8 flex items-center justify-center bg-primary text-white rounded-lg">1</button>
            <button className="w-8 h-8 flex items-center justify-center border border-borderColor rounded-lg text-textSecondary hover:bg-gray-50">2</button>
            <button className="w-8 h-8 flex items-center justify-center border border-borderColor rounded-lg text-textSecondary hover:bg-gray-50">3</button>
            <span className="text-textMuted">...</span>
            <button className="w-8 h-8 flex items-center justify-center border border-borderColor rounded-lg text-textSecondary hover:bg-gray-50">26</button>
            <button className="w-8 h-8 flex items-center justify-center border border-borderColor rounded-lg text-textMuted hover:bg-gray-50">
              <FontAwesomeIcon icon={faSort} className="text-xs -rotate-90" />
            </button>
          </div>
        </div>
      </section>
    </>
  )
}

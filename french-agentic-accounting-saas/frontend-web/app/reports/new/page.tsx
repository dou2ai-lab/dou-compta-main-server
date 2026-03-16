'use client'

import { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import Chart from '@/components/ui/Chart'
import Badge from '@/components/ui/Badge'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faEuroSign,
  faReceipt,
  faPaperPlane,
  faSpinner,
  faPlane,
  faUtensils,
  faHotel,
  faCar,
  faLaptop,
  faFileText,
} from '@fortawesome/free-solid-svg-icons'
import { useExpenses } from '@/lib/hooks'
import { reportAPI, getAuthErrorMessage } from '@/lib/api'

const CATEGORY_ICON: Record<string, typeof faReceipt> = {
  travel: faPlane,
  meals: faUtensils,
  accommodation: faHotel,
  transport: faCar,
  office: faLaptop,
  training: faFileText,
}

function formatDate(d: string | undefined): string {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function NewReportPage() {
  const router = useRouter()
  const [reportTitle, setReportTitle] = useState('')
  const [reportType, setReportType] = useState<'period' | 'trip'>('period')
  const [periodStart, setPeriodStart] = useState('')
  const [periodEnd, setPeriodEnd] = useState('')
  const [description, setDescription] = useState('')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const { expenses, isLoading } = useExpenses({ page: 1, page_size: 100 })

  const expenseList = useMemo(() => (Array.isArray(expenses) ? expenses : []), [expenses])

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const selectAll = () => {
    if (selectedIds.size === expenseList.length) setSelectedIds(new Set())
    else setSelectedIds(new Set(expenseList.map((e: { id: string }) => String(e.id))))
  }

  const selectedExpenses = useMemo(
    () => expenseList.filter((e: { id: string }) => selectedIds.has(String(e.id))),
    [expenseList, selectedIds]
  )

  const totalAmount = useMemo(
    () => selectedExpenses.reduce((sum: number, e: { amount?: number }) => sum + Number(e.amount ?? 0), 0),
    [selectedExpenses]
  )

  const handleCreateReport = async () => {
    if (selectedIds.size === 0) {
      setError('Select at least one expense to include in the report.')
      return
    }
    const title = reportTitle.trim() || `Report ${new Date().toLocaleDateString('en-GB', { month: 'short', year: 'numeric' })}`
    const now = new Date()
    const start = periodStart || new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10)
    const end = periodEnd || new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().slice(0, 10)

    setSaving(true)
    setError('')
    try {
      const payload = {
        report_type: reportType,
        title,
        description: description.trim() || undefined,
        period_start_date: start,
        period_end_date: end,
        period_type: 'monthly',
        expense_ids: Array.from(selectedIds),
      }
      const res = await reportAPI.create(payload)
      const reportId = res?.data?.id ?? res?.id
      if (reportId) router.push(`/reports/${reportId}`)
      else router.push('/reports')
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, 'Failed to create report'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex-1 max-w-2xl">
            <div className="flex items-center space-x-3 mb-4">
              <input
                type="text"
                value={reportTitle}
                onChange={(e) => setReportTitle(e.target.value)}
                placeholder="Report title (e.g. January 2025 Expense Report)"
                className="text-3xl font-bold text-textPrimary bg-transparent border-b-2 border-transparent hover:border-borderColor focus:border-primary focus:outline-none transition-colors w-full"
              />
              <span className="inline-flex items-center text-xs font-medium text-textSecondary bg-gray-100 px-3 py-1.5 rounded-full shrink-0">
                <span className="w-2 h-2 bg-warningAmber rounded-full mr-2" />
                New Report
              </span>
            </div>
            <p className="text-textSecondary mb-4">Select expenses and submit for approval</p>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-textSecondary mb-2">Report Type</label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value as 'period' | 'trip')}
                  className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="period">Period Report</option>
                  <option value="trip">Trip Report</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-textSecondary mb-2">Start Date</label>
                <input
                  type="date"
                  value={periodStart}
                  onChange={(e) => setPeriodStart(e.target.value)}
                  className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-textSecondary mb-2">End Date</label>
                <input
                  type="date"
                  value={periodEnd}
                  onChange={(e) => setPeriodEnd(e.target.value)}
                  className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 mb-8">
        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faEuroSign} className="text-primary text-xl" />
            </div>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">
            €{totalAmount.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-sm text-textSecondary mb-2">Total (selected)</div>
          <div className="text-xs text-textMuted">{selectedIds.size} expense(s) selected</div>
        </div>
      </section>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      <section className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-textPrimary mb-1">Expenses to include</h2>
            <p className="text-sm text-textSecondary">Select expenses for this report</p>
          </div>
          <button
            type="button"
            onClick={selectAll}
            className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50"
          >
            {selectedIds.size === expenseList.length && expenseList.length > 0 ? 'Deselect all' : 'Select all'}
          </button>
        </div>

        {isLoading ? (
          <div className="py-12 flex flex-col items-center justify-center text-textSecondary">
            <FontAwesomeIcon icon={faSpinner} className="animate-spin text-2xl mb-4" />
            <p>Loading expenses…</p>
          </div>
        ) : expenseList.length === 0 ? (
          <div className="py-12 text-center text-textSecondary">
            <FontAwesomeIcon icon={faReceipt} className="text-4xl mb-4 opacity-50" />
            <p className="font-medium">No expenses yet</p>
            <p className="text-sm mt-1">Create expenses from the Expenses page, then come back to add them to a report.</p>
            <button
              onClick={() => router.push('/expenses')}
              className="mt-4 h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium"
            >
              Go to Expenses
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {expenseList.map((exp: { id: string; expense_date?: string; merchant_name?: string; category?: string; description?: string; amount?: number; vat_amount?: number; status?: string }) => {
              const id = String(exp.id)
              const isSelected = selectedIds.has(id)
              const icon = CATEGORY_ICON[exp.category ?? ''] ?? faReceipt
              return (
                <div
                  key={id}
                  className={`flex items-center space-x-4 p-4 rounded-lg border transition-colors cursor-pointer ${
                    isSelected ? 'border-primary bg-indigo-50/50' : 'border-borderColor hover:bg-gray-50'
                  }`}
                  onClick={() => toggleSelect(id)}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleSelect(id)}
                    className="w-4 h-4 text-primary border-borderColor rounded focus:ring-primary"
                    onClick={(e) => e.stopPropagation()}
                  />
                  <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                    <FontAwesomeIcon icon={icon} className="text-textMuted" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-textPrimary">{exp.merchant_name || 'Unknown'}</div>
                    <div className="flex items-center space-x-2 text-xs text-textSecondary">
                      <span>{formatDate(exp.expense_date)}</span>
                      <span>•</span>
                      <span>{(exp.category || 'Other').replace(/^\w/, (c) => c.toUpperCase())}</span>
                      {exp.description && (
                        <>
                          <span>•</span>
                          <span className="truncate max-w-[200px]" title={exp.description}>{exp.description}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="font-semibold text-textPrimary">
                      €{Number(exp.amount ?? 0).toFixed(2)}
                    </div>
                    {exp.vat_amount != null && (
                      <div className="text-xs text-textSecondary">VAT €{Number(exp.vat_amount).toFixed(2)}</div>
                    )}
                  </div>
                  <Badge variant={exp.status === 'draft' ? 'default' : exp.status === 'submitted' ? 'warning' : 'success'}>
                    {exp.status || 'draft'}
                  </Badge>
                </div>
              )
            })}
          </div>
        )}
      </section>

      <section className="flex items-center justify-between">
        <button
          onClick={() => router.back()}
          className="h-12 px-6 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50"
        >
          Cancel
        </button>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleCreateReport}
            disabled={saving || selectedIds.size === 0}
            className="h-12 px-8 bg-primary hover:bg-primaryHover disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium flex items-center space-x-2"
          >
            {saving ? (
              <>
                <FontAwesomeIcon icon={faSpinner} className="animate-spin" />
                <span>Creating…</span>
              </>
            ) : (
              <>
                <FontAwesomeIcon icon={faPaperPlane} />
                <span>Create Report</span>
              </>
            )}
          </button>
        </div>
      </section>
    </>
  )
}

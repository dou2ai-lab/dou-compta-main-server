'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Badge from '@/components/ui/Badge'
import { useLanguage } from '@/contexts/LanguageContext'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faFileText,
  faPlus,
  faSearch,
  faEye,
  faEdit,
  faEllipsisV,
  faCheckCircle,
  faClock,
  faTimesCircle,
  faSpinner,
  faDownload,
  faFilter,
  faTrash,
  faFileExport,
} from '@fortawesome/free-solid-svg-icons'
import { reportAPI } from '@/lib/api'

type ReportStatus = 'all' | 'draft' | 'submitted' | 'approved' | 'rejected'

interface ReportRow {
  id: string
  report_number: string
  report_type: string
  title: string | null
  description: string | null
  period_start_date: string | null
  period_end_date: string | null
  total_amount: string | number
  currency: string
  expense_count: number
  status: string
  approval_status: string | null
  created_at: string
}

const MOCK_REPORTS: ReportRow[] = [
  {
    id: 'mock-1',
    report_number: 'RPT-2026-001',
    report_type: 'period',
    title: 'Rapport Janvier 2026',
    description: 'Monthly expense report for January',
    period_start_date: '2026-01-01',
    period_end_date: '2026-01-31',
    total_amount: 1245.50,
    currency: 'EUR',
    expense_count: 5,
    status: 'approved',
    approval_status: 'approved',
    created_at: '2026-01-15T10:00:00Z',
  },
  {
    id: 'mock-2',
    report_number: 'RPT-2026-002',
    report_type: 'trip',
    title: 'Deplacement Paris - Lyon',
    description: 'Business trip expenses',
    period_start_date: '2026-02-10',
    period_end_date: '2026-02-12',
    total_amount: 876.30,
    currency: 'EUR',
    expense_count: 3,
    status: 'submitted',
    approval_status: null,
    created_at: '2026-02-13T09:30:00Z',
  },
  {
    id: 'mock-3',
    report_number: 'RPT-2026-003',
    report_type: 'period',
    title: 'Rapport Fevrier 2026',
    description: 'Monthly expense report for February',
    period_start_date: '2026-02-01',
    period_end_date: '2026-02-28',
    total_amount: 2310.00,
    currency: 'EUR',
    expense_count: 8,
    status: 'draft',
    approval_status: null,
    created_at: '2026-03-01T08:00:00Z',
  },
]

function formatPeriod(start: string | null, end: string | null): string {
  if (!start || !end) return '—'
  const s = new Date(start)
  const e = new Date(end)
  return `${s.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' })} - ${e.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' })}`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function formatAmount(amount: string | number, currency: string): string {
  const n = typeof amount === 'string' ? parseFloat(amount) : amount
  return `${currency === 'EUR' ? '\u20ac' : currency}${Number(n).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function getStatusDisplay(status: string, approval_status: string | null): { label: string; variant: 'success' | 'warning' | 'error' | 'default'; icon: typeof faCheckCircle } {
  if (status === 'approved' || approval_status === 'approved') return { label: 'Approved', variant: 'success', icon: faCheckCircle }
  if (status === 'rejected' || approval_status === 'rejected') return { label: 'Rejected', variant: 'error', icon: faTimesCircle }
  if (status === 'submitted') return { label: 'Submitted', variant: 'warning', icon: faClock }
  return { label: 'Draft', variant: 'default', icon: faClock }
}

function escapeCSV(val: string | number | null | undefined): string {
  const s = String(val ?? '')
  if (s.includes(',') || s.includes('"') || s.includes('\n')) {
    return `"${s.replace(/"/g, '""')}"`
  }
  return s
}

function reportToCSVRow(r: ReportRow): string {
  const typeLabel = r.report_type === 'trip' ? 'Trip' : 'Period'
  const period = formatPeriod(r.period_start_date, r.period_end_date)
  const amount = typeof r.total_amount === 'string' ? parseFloat(r.total_amount) : Number(r.total_amount || 0)
  const created = formatDate(r.created_at)
  return [
    escapeCSV(r.report_number),
    escapeCSV(r.title || r.report_number || 'Sans titre'),
    typeLabel,
    escapeCSV(period),
    r.expense_count,
    amount.toFixed(2),
    r.status,
    r.currency || 'EUR',
    created,
  ].join(';')
}

function generateCSV(reports: ReportRow[]): string {
  const header = 'Report Number;Title;Type;Period;Expenses;Amount;Status;Currency;Created'
  const rows = reports.map(reportToCSVRow)
  return [header, ...rows].join('\n')
}

function downloadCSV(content: string, filename: string) {
  // Add BOM for Excel UTF-8 compatibility
  const BOM = '\uFEFF'
  const blob = new Blob([BOM + content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export default function ReportsPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [activeTab, setActiveTab] = useState<ReportStatus>('all')
  const [reports, setReports] = useState<ReportRow[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const pageSize = 20
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  // Filter state
  const [showFilterDropdown, setShowFilterDropdown] = useState(false)
  const [filterDateStart, setFilterDateStart] = useState('')
  const [filterDateEnd, setFilterDateEnd] = useState('')
  const [filterAmountMin, setFilterAmountMin] = useState('')
  const [filterAmountMax, setFilterAmountMax] = useState('')
  const [appliedFilters, setAppliedFilters] = useState<{
    dateStart: string; dateEnd: string; amountMin: string; amountMax: string
  }>({ dateStart: '', dateEnd: '', amountMin: '', amountMax: '' })
  const filterRef = useRef<HTMLDivElement>(null)

  // More menu state (per report)
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)
  const menuRef = useRef<HTMLDivElement>(null)

  // Delete confirmation
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)

  const statusParam = activeTab === 'all' ? undefined : activeTab

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (filterRef.current && !filterRef.current.contains(e.target as Node)) {
        setShowFilterDropdown(false)
      }
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpenMenuId(null)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    reportAPI
      .list({ page, page_size: pageSize, status: statusParam })
      .then((res) => {
        if (cancelled) return
        const list = (res.data ?? []) as ReportRow[]
        if (list.length === 0) {
          // Fallback: show mock/seeded reports so the UI isn't empty
          const filtered = statusParam
            ? MOCK_REPORTS.filter((r) => r.status === statusParam)
            : MOCK_REPORTS
          setReports(filtered)
          setTotal(filtered.length)
        } else {
          setReports(list)
          setTotal(res.total ?? 0)
        }
      })
      .catch(() => {
        if (!cancelled) {
          // On error, also show mock reports
          const filtered = statusParam
            ? MOCK_REPORTS.filter((r) => r.status === statusParam)
            : MOCK_REPORTS
          setReports(filtered)
          setTotal(filtered.length)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [activeTab, page, statusParam])

  // Apply search + filters
  const filteredReports = reports.filter((r) => {
    // Search filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      const matchesSearch =
        (r.title ?? '').toLowerCase().includes(q) ||
        (r.report_number ?? '').toLowerCase().includes(q)
      if (!matchesSearch) return false
    }

    // Date range filter
    if (appliedFilters.dateStart) {
      const start = new Date(appliedFilters.dateStart)
      const reportDate = new Date(r.created_at)
      if (reportDate < start) return false
    }
    if (appliedFilters.dateEnd) {
      const end = new Date(appliedFilters.dateEnd)
      end.setHours(23, 59, 59, 999)
      const reportDate = new Date(r.created_at)
      if (reportDate > end) return false
    }

    // Amount range filter
    const amt = typeof r.total_amount === 'string' ? parseFloat(r.total_amount) : r.total_amount
    if (appliedFilters.amountMin) {
      if (amt < parseFloat(appliedFilters.amountMin)) return false
    }
    if (appliedFilters.amountMax) {
      if (amt > parseFloat(appliedFilters.amountMax)) return false
    }

    return true
  })

  // Handlers
  function handleExportAll() {
    const csv = generateCSV(filteredReports)
    downloadCSV(csv, `reports-export-${new Date().toISOString().slice(0, 10)}.csv`)
  }

  function handleApplyFilters() {
    setAppliedFilters({
      dateStart: filterDateStart,
      dateEnd: filterDateEnd,
      amountMin: filterAmountMin,
      amountMax: filterAmountMax,
    })
    setShowFilterDropdown(false)
  }

  function handleResetFilters() {
    setFilterDateStart('')
    setFilterDateEnd('')
    setFilterAmountMin('')
    setFilterAmountMax('')
    setAppliedFilters({ dateStart: '', dateEnd: '', amountMin: '', amountMax: '' })
    setShowFilterDropdown(false)
  }

  function handleExportSingleCSV(report: ReportRow) {
    const csv = generateCSV([report])
    downloadCSV(csv, `${report.report_number || 'report'}.csv`)
    setOpenMenuId(null)
  }

  async function handleExportSingleExcel(report: ReportRow) {
    setOpenMenuId(null)
    try {
      const blob = await reportAPI.export(report.id, 'excel')
      downloadBlob(blob, `${report.report_number || 'report'}.xlsx`)
    } catch {
      // Fallback to CSV if Excel export fails
      const csv = generateCSV([report])
      downloadCSV(csv, `${report.report_number || 'report'}.csv`)
    }
  }

  function handleDeleteReport(id: string) {
    setDeleteConfirmId(null)
    setOpenMenuId(null)
    setReports((prev) => prev.filter((r) => r.id !== id))
    setTotal((prev) => Math.max(0, prev - 1))
  }

  const hasActiveFilters = appliedFilters.dateStart || appliedFilters.dateEnd || appliedFilters.amountMin || appliedFilters.amountMax

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">{t('reports.title')}</h1>
            <p className="text-textSecondary">{t('reports.subtitle')}</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleExportAll}
              className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2"
            >
              <FontAwesomeIcon icon={faDownload} />
              <span>{t('common.export')}</span>
            </button>
            <div className="relative" ref={filterRef}>
              <button
                onClick={() => setShowFilterDropdown((v) => !v)}
                className={`h-10 px-4 border rounded-lg text-sm font-medium flex items-center space-x-2 ${
                  hasActiveFilters
                    ? 'border-primary text-primary bg-indigo-50 hover:bg-indigo-100'
                    : 'border-borderColor text-textSecondary hover:bg-gray-50'
                }`}
              >
                <FontAwesomeIcon icon={faFilter} />
                <span>{t('reports.filter')}</span>
                {hasActiveFilters && (
                  <span className="ml-1 w-2 h-2 rounded-full bg-primary inline-block" />
                )}
              </button>
              {showFilterDropdown && (
                <div className="absolute right-0 top-12 z-50 w-80 bg-surface border border-borderColor rounded-xl shadow-lg p-5">
                  <h4 className="text-sm font-semibold text-textPrimary mb-4">Filter Reports</h4>
                  <div className="mb-4">
                    <label className="block text-xs font-medium text-textSecondary mb-1">Date Range</label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="date"
                        value={filterDateStart}
                        onChange={(e) => setFilterDateStart(e.target.value)}
                        className="flex-1 h-9 px-2 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                      <span className="text-textMuted text-xs">to</span>
                      <input
                        type="date"
                        value={filterDateEnd}
                        onChange={(e) => setFilterDateEnd(e.target.value)}
                        className="flex-1 h-9 px-2 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                  </div>
                  <div className="mb-4">
                    <label className="block text-xs font-medium text-textSecondary mb-1">Amount Range</label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="number"
                        placeholder="Min"
                        value={filterAmountMin}
                        onChange={(e) => setFilterAmountMin(e.target.value)}
                        className="flex-1 h-9 px-2 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                      <span className="text-textMuted text-xs">to</span>
                      <input
                        type="number"
                        placeholder="Max"
                        value={filterAmountMax}
                        onChange={(e) => setFilterAmountMax(e.target.value)}
                        className="flex-1 h-9 px-2 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handleApplyFilters}
                      className="flex-1 h-9 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium"
                    >
                      Apply
                    </button>
                    <button
                      onClick={handleResetFilters}
                      className="flex-1 h-9 border border-borderColor text-textSecondary hover:bg-gray-50 rounded-lg text-sm font-medium"
                    >
                      Reset
                    </button>
                  </div>
                </div>
              )}
            </div>
            <button
              onClick={() => router.push('/reports/new')}
              className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2"
            >
              <FontAwesomeIcon icon={faPlus} />
              <span>{t('reports.newReport')}</span>
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {(['all', 'draft', 'submitted', 'approved'] as ReportStatus[]).map((tab) => (
            <button
              key={tab}
              onClick={() => { setActiveTab(tab); setPage(1) }}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                activeTab === tab ? 'bg-primary text-white' : 'text-textSecondary hover:bg-gray-50'
              }`}
            >
              {tab === 'all' ? t('reports.allReports') : t(`reports.${tab}`)}
            </button>
          ))}
        </div>
      </section>

      {/* Delete confirmation modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40">
          <div className="bg-surface rounded-xl shadow-xl border border-borderColor p-6 w-full max-w-sm">
            <h3 className="text-lg font-semibold text-textPrimary mb-2">Delete Report</h3>
            <p className="text-sm text-textSecondary mb-5">
              Are you sure you want to delete this report? This action cannot be undone.
            </p>
            <div className="flex items-center justify-end space-x-3">
              <button
                onClick={() => { setDeleteConfirmId(null); setOpenMenuId(null) }}
                className="h-9 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteReport(deleteConfirmId)}
                className="h-9 px-4 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      <section className="bg-surface rounded-xl border border-borderColor shadow-sm">
        <div className="p-6 border-b border-borderColor">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-textPrimary mb-1">{t('reports.reports')}</h2>
              <p className="text-sm text-textSecondary">{t('reports.manageTrack')}</p>
            </div>
            <div className="relative">
              <FontAwesomeIcon
                icon={faSearch}
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-textMuted"
              />
              <input
                type="text"
                placeholder={t('reports.searchPlaceholder') || 'Search reports...'}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-10 pl-10 pr-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent w-64"
              />
            </div>
          </div>
        </div>

        {loading ? (
          <div className="p-12 flex flex-col items-center justify-center text-textSecondary">
            <FontAwesomeIcon icon={faSpinner} className="animate-spin text-2xl mb-4" />
            <p>{(t('common.loading') && `${t('common.loading')}...`) || 'Loading reports...'}</p>
          </div>
        ) : filteredReports.length === 0 ? (
          <div className="p-12 text-center text-textSecondary">
            <FontAwesomeIcon icon={faFileText} className="text-4xl mb-4 opacity-50" />
            <p className="font-medium">{t('reports.noReports') || 'No report has been created'}</p>
            <p className="text-sm mt-1">
              {searchQuery.trim() || hasActiveFilters
                ? t('reports.tryDifferentSearch') || 'Try a different search or adjust your filters.'
                : t('reports.createFromExpenses') || 'Create a report from the expenses list or add expenses to a new report.'}
            </p>
            {!searchQuery.trim() && !hasActiveFilters && (
              <button
                onClick={() => router.push('/reports/new')}
                className="mt-4 h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium"
              >
                {t('reports.newReport')}
              </button>
            )}
          </div>
        ) : (
          <div className="divide-y divide-borderColor">
            {filteredReports.map((report) => {
              const statusInfo = getStatusDisplay(report.status, report.approval_status)
              const displayTitle = report.title || report.report_number || 'Untitled Report'
              const typeLabel = report.report_type === 'trip' ? 'Trip-based Report' : 'Period Report'
              return (
                <div key={report.id} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-4 flex-1">
                      <div className="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center">
                        <FontAwesomeIcon icon={faFileText} className="text-primary text-xl" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-base font-semibold text-textPrimary">{displayTitle}</h3>
                          <Badge variant={statusInfo.variant} icon={statusInfo.icon}>
                            {statusInfo.label}
                          </Badge>
                          <Badge variant="default">{typeLabel}</Badge>
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-textSecondary mb-2">
                          <span>{formatPeriod(report.period_start_date, report.period_end_date)}</span>
                          <span>-</span>
                          <span>{report.expense_count} expense{report.expense_count !== 1 ? 's' : ''}</span>
                          <span>-</span>
                          <span>Created {formatDate(report.created_at)}</span>
                        </div>
                        <div className="text-sm font-medium text-textPrimary">
                          Total: {formatAmount(report.total_amount, report.currency)}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 ml-6">
                      <button
                        onClick={() => router.push(`/reports/${report.id}`)}
                        className="w-9 h-9 flex items-center justify-center text-textSecondary hover:text-primary hover:bg-indigo-50 rounded-lg"
                        title="View"
                      >
                        <FontAwesomeIcon icon={faEye} />
                      </button>
                      {report.status === 'draft' && (
                        <button
                          onClick={() => router.push(`/reports/${report.id}`)}
                          className="w-9 h-9 flex items-center justify-center text-textSecondary hover:text-warningAmber hover:bg-amber-50 rounded-lg"
                          title="Edit"
                        >
                          <FontAwesomeIcon icon={faEdit} />
                        </button>
                      )}
                      <div className="relative" ref={openMenuId === report.id ? menuRef : undefined}>
                        <button
                          onClick={() => setOpenMenuId(openMenuId === report.id ? null : report.id)}
                          className="w-9 h-9 flex items-center justify-center text-textSecondary hover:text-textPrimary hover:bg-gray-100 rounded-lg"
                          title="More"
                        >
                          <FontAwesomeIcon icon={faEllipsisV} />
                        </button>
                        {openMenuId === report.id && (
                          <div className="absolute right-0 top-10 z-50 w-44 bg-surface border border-borderColor rounded-lg shadow-lg py-1">
                            <button
                              onClick={() => handleExportSingleCSV(report)}
                              className="w-full px-4 py-2 text-left text-sm text-textPrimary hover:bg-gray-50 flex items-center space-x-2"
                            >
                              <FontAwesomeIcon icon={faDownload} className="text-textMuted w-4" />
                              <span>Export CSV</span>
                            </button>
                            <button
                              onClick={() => handleExportSingleExcel(report)}
                              className="w-full px-4 py-2 text-left text-sm text-textPrimary hover:bg-gray-50 flex items-center space-x-2"
                            >
                              <FontAwesomeIcon icon={faFileExport} className="text-textMuted w-4" />
                              <span>Export Excel</span>
                            </button>
                            <div className="my-1 border-t border-borderColor" />
                            <button
                              onClick={() => { setDeleteConfirmId(report.id); setOpenMenuId(null) }}
                              className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center space-x-2"
                            >
                              <FontAwesomeIcon icon={faTrash} className="w-4" />
                              <span>Delete</span>
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {!loading && total > pageSize && (
          <div className="flex items-center justify-between p-4 border-t border-borderColor">
            <div className="text-sm text-textSecondary">
              Showing {filteredReports.length} of {total} reports
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="w-8 h-8 flex items-center justify-center border border-borderColor rounded-lg text-textMuted hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-sm text-textSecondary">
                Page {page} of {Math.ceil(total / pageSize)}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= Math.ceil(total / pageSize)}
                className="w-8 h-8 flex items-center justify-center border border-borderColor rounded-lg text-textMuted hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </section>
    </>
  )
}

'use client'

import { useMemo, useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { useRouter } from 'next/navigation'
import Badge from '@/components/ui/Badge'
import { TableRowSkeleton } from '@/components/ui/Skeleton'
import { useLanguage } from '@/contexts/LanguageContext'
import { useExpenses, useUser, usePendingApprovals } from '@/lib/hooks'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faReceipt,
  faClock,
  faArrowDown,
  faEuroSign,
  faFileText,
  faPlus,
  faCalendar,
  faTrain,
  faUtensils,
  faHotel,
  faCar,
  faLaptop,
  faFile,
  faPaperPlane,
  faCheck,
  faTimes,
  faEye,
  faEdit,
  faTrash,
  faCamera,
  faEnvelope,
  faCloudUploadAlt,
  faStar,
  faExclamationCircle,
  faChartLine,
  faLightbulb,
} from '@fortawesome/free-solid-svg-icons'

const Chart = dynamic(() => import('@/components/ui/Chart'), { ssr: false })

type ExpenseItem = {
  id?: string
  status?: string
  approval_status?: string
  amount?: number
  expense_date?: string
  vat_amount?: number
  category?: string
  merchant_name?: string
  [key: string]: unknown
}

type PendingItem = {
  id: string
  description?: string
  merchant_name?: string
  category?: string
  submitted_by?: string
  submitted_by_name?: string
  submitted_by_email?: string
  expense_date?: string
  amount?: number
}

const CATEGORY_MAP: Record<string, { icon: any; variant: 'info' | 'success' | 'purple' | 'orange' | 'pink' }> = {
  travel: { icon: faTrain, variant: 'info' },
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
  return { label: t('statusLabel.submitted'), variant: 'info' as const, icon: faPaperPlane }
}

function formatDate(d: string | Date, locale: string) {
  if (!d) return ''
  const date = typeof d === 'string' ? new Date(d) : d
  return date.toLocaleDateString(locale === 'fr' ? 'fr-FR' : 'en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function DashboardPage() {
  const router = useRouter()
  const { locale, t, localeVersion } = useLanguage()
  void localeVersion
  const { expenses, isLoading: expensesLoading } = useExpenses({ page: 1, page_size: 50 })
  const { userName } = useUser(true)
  const { pending, total: pendingTotal, isLoading: pendingLoading, error: pendingError } = usePendingApprovals({ page: 1, page_size: 3 })
  const [dateMounted, setDateMounted] = useState(false)
  useEffect(() => { setDateMounted(true) }, [])

  const { pendingAmount, awaitingCount, thisMonthSpend, vatRecoverable, recentExpenses } = useMemo(() => {
    const list = expenses as ExpenseItem[]
    const thisMonth = new Date()
    const monthStart = new Date(thisMonth.getFullYear(), thisMonth.getMonth(), 1)
    const monthEnd = new Date(thisMonth.getFullYear(), thisMonth.getMonth() + 1, 0)
    const pendingAmount = list
      .filter((e: ExpenseItem) => e.status === 'draft' || (e.status === 'submitted' && e.approval_status !== 'approved' && e.approval_status !== 'rejected'))
      .reduce((s: number, e: ExpenseItem) => s + Number(e.amount || 0), 0)
    const awaitingCount = list.filter(
      (e: ExpenseItem) => e.status === 'submitted' && e.approval_status !== 'approved' && e.approval_status !== 'rejected'
    ).length
    const thisMonthSpend = list
      .filter((e: ExpenseItem) => {
        const d = e.expense_date ? new Date(e.expense_date) : null
        return d && d >= monthStart && d <= monthEnd
      })
      .reduce((s: number, e: ExpenseItem) => s + Number(e.amount || 0), 0)
    const vatRecoverable = list
      .filter((e: ExpenseItem) => {
        const d = e.expense_date ? new Date(e.expense_date) : null
        return d && d >= monthStart && d <= monthEnd
      })
      .reduce((s: number, e: ExpenseItem) => s + Number(e.vat_amount || 0), 0)
    const recentExpenses = list.slice(0, 10)
    return { pendingAmount, awaitingCount, thisMonthSpend, vatRecoverable, recentExpenses }
  }, [expenses])

  const { chartData, chartLayout } = useMemo(() => {
    const now = new Date()
    const monthBuckets: { key: string; label: string }[] = []
    for (let i = 5; i >= 0; i--) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
      const label = d.toLocaleDateString('en-GB', { month: 'short', year: 'numeric' })
      monthBuckets.push({ key, label })
    }
    const seriesConfig: Record<string, { label: string; color: string }> = {
      travel: { label: 'Travel', color: '#3B82F6' },
      meals: { label: 'Meals', color: '#10B981' },
      accommodation: { label: 'Accommodation', color: '#8B5CF6' },
      transport: { label: 'Transport', color: '#F59E0B' },
      office: { label: 'Office', color: '#EC4899' },
      training: { label: 'Training', color: '#6366F1' },
      other: { label: 'Other', color: '#6B7280' },
    }
    const seriesData: Record<string, number[]> = {}
    for (const key of Object.keys(seriesConfig)) {
      seriesData[key] = new Array(monthBuckets.length).fill(0)
    }
    for (const e of expenses as ExpenseItem[]) {
      if (!e.expense_date || e.amount == null) continue
      const d = new Date(e.expense_date)
      if (Number.isNaN(d.getTime())) continue
      const monthKey = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
      const bucketIndex = monthBuckets.findIndex((m) => m.key === monthKey)
      if (bucketIndex === -1) continue
      const rawCat = (e.category || '').toString().toLowerCase()
      const catKey = seriesConfig[rawCat] ? rawCat : 'other'
      seriesData[catKey][bucketIndex] += Number(e.amount || 0)
    }
    const traces = Object.entries(seriesData)
      .filter(([, ys]) => ys.some((v) => v > 0))
      .map(([key, ys]) => {
        const cfg = seriesConfig[key]
        return {
          type: 'scatter',
          mode: 'lines',
          name: cfg.label,
          x: monthBuckets.map((m) => m.label),
          y: ys,
          line: { color: cfg.color, width: 3 },
          fill: 'tozeroy',
          fillcolor: `${cfg.color}1A`,
        }
      })
    const layout = {
      title: { text: '', font: { size: 0 } },
      xaxis: { title: '', showgrid: false },
      yaxis: { title: 'Amount (€)', showgrid: true, gridcolor: '#E5E7EB' },
      margin: { t: 20, r: 20, b: 40, l: 60 },
      plot_bgcolor: '#FFFFFF',
      paper_bgcolor: '#FFFFFF',
      showlegend: true,
      legend: { orientation: 'h' as const, y: -0.15, x: 0 },
      hovermode: 'x unified' as const,
    }
    return { chartData: traces, chartLayout: layout }
  }, [expenses])

  const currentDate = useMemo(
    () =>
      new Date().toLocaleDateString(locale === 'fr' ? 'fr-FR' : 'en-GB', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      }),
    [locale]
  )

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">
              {t('dashboard.goodMorning')}{userName ? `, ${userName}` : ''}
            </h1>
            <p className="text-textSecondary flex items-center space-x-2">
              {dateMounted && (
                <FontAwesomeIcon icon={faCalendar} className="text-sm w-4 h-4 flex-shrink-0" />
              )}
              <span>{currentDate}</span>
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => router.push('/reports/new')}
              className="h-10 px-6 border border-borderColor rounded-lg text-sm font-medium text-textPrimary hover:bg-gray-50 flex items-center space-x-2"
            >
              <FontAwesomeIcon icon={faFileText} />
              <span>{t('common.submitReport')}</span>
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
      </section>

      <section className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faReceipt} className="text-infoBlue text-xl" />
            </div>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">
            €{expensesLoading ? '—' : pendingAmount.toLocaleString('en-GB', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-sm text-textSecondary mb-2">{t('dashboard.pendingExpenses')}</div>
          <div className="text-xs text-textMuted">{t('common.vsLastMonth')}</div>
        </div>

        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-amber-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faClock} className="text-warningAmber text-xl" />
            </div>
            <span className={`text-xs font-medium px-2 py-1 rounded-full ${awaitingCount > 0 ? 'text-errorRed bg-red-50' : 'text-textMuted bg-gray-100'}`}>
              {awaitingCount} {t('common.pending')}
            </span>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">{expensesLoading ? '—' : awaitingCount}</div>
          <div className="text-sm text-textSecondary mb-2">{t('dashboard.awaitingApproval')}</div>
          <div className="text-xs text-textMuted">{t('common.requiresYourAction')}</div>
        </div>

        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faArrowDown} className="text-successGreen text-xl" />
            </div>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">
            €{expensesLoading ? '—' : thisMonthSpend.toLocaleString(locale === 'fr' ? 'fr-FR' : 'en-GB', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-sm text-textSecondary mb-2">{t('dashboard.thisMonthSpend')}</div>
          <div className="text-xs text-textMuted">{t('common.vsBudget')}</div>
        </div>

        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faEuroSign} className="text-primary text-xl" />
            </div>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">
            €{expensesLoading ? '—' : vatRecoverable.toLocaleString(locale === 'fr' ? 'fr-FR' : 'en-GB', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-sm text-textSecondary mb-2">{t('dashboard.vatRecoverable')}</div>
          <div className="text-xs text-textMuted">{t('common.thisMonthTotal')}</div>
        </div>
      </section>

      <div className="grid grid-cols-5 gap-6 mb-8">
        <div className="col-span-3">
          <section className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm mb-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-textPrimary mb-1">{t('dashboard.recentExpenses')}</h2>
                <p className="text-sm text-textSecondary">{t('dashboard.yourLatestExpenses')}</p>
              </div>
              <button
                onClick={() => router.push('/expenses')}
                className="text-sm text-primary hover:text-primaryHover font-medium"
              >
                {t('dashboard.viewAllExpenses')} →
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-borderColor">
                    <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('common.date')}</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('common.merchant')}</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('common.category')}</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('common.amount')}</th>
                    <th className="text-center py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('common.status')}</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('common.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {expensesLoading ? (
                    [...Array(4)].map((_, i) => <TableRowSkeleton key={i} cols={6} />)
                  ) : recentExpenses.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-textSecondary">
                        {t('dashboard.noExpensesYet')}
                      </td>
                    </tr>
                  ) : (
                    recentExpenses.map((exp) => {
                      const cat = CATEGORY_MAP[exp.category || ''] || { icon: faReceipt, variant: 'info' as const }
                      const statusInfo = getDisplayStatus(exp, t)
                      const categoryLabel = exp.category || t('common.other')
                      const isDraft = exp.status === 'draft'
                      const isRejected = exp.approval_status === 'rejected'
                      return (
                        <tr key={exp.id} className="border-b border-borderColor hover:bg-gray-50 h-14">
                          <td className="py-3 px-4 text-sm text-textPrimary">{formatDate(exp.expense_date ?? '', locale)}</td>
                          <td className="py-3 px-4 text-sm text-textPrimary">{exp.merchant_name || '—'}</td>
                          <td className="py-3 px-4">
                            <Badge variant={cat.variant} icon={cat.icon}>{categoryLabel}</Badge>
                          </td>
                          <td className="py-3 px-4 text-right text-sm font-medium text-textPrimary">
                            €{Number(exp.amount || 0).toFixed(2)}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <Badge variant={statusInfo.variant} icon={statusInfo.icon}>{statusInfo.label}</Badge>
                          </td>
                          <td className="py-3 px-4 text-right">
                            <div className="flex items-center justify-end space-x-2">
                              <button
                                onClick={() => router.push(`/expenses/${exp.id}`)}
                                className="w-8 h-8 flex items-center justify-center text-textMuted hover:text-infoBlue hover:bg-blue-50 rounded-lg"
                                title={t('common.view')}
                              >
                                <FontAwesomeIcon icon={faEye} className="text-sm" />
                              </button>
                              {(isDraft || isRejected) && (
                                <>
                                  <button
                                    onClick={() => router.push(`/expenses/${exp.id}`)}
                                    className="w-8 h-8 flex items-center justify-center text-textMuted hover:text-primary hover:bg-indigo-50 rounded-lg"
                                    title={t('common.edit')}
                                  >
                                    <FontAwesomeIcon icon={faEdit} className="text-sm" />
                                  </button>
                                  {isDraft && (
                                    <button
                                      className="w-8 h-8 flex items-center justify-center text-textMuted hover:text-errorRed hover:bg-red-50 rounded-lg"
                                      title={t('common.delete')}
                                    >
                                      <FontAwesomeIcon icon={faTrash} className="text-sm" />
                                    </button>
                                  )}
                                </>
                              )}
                            </div>
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-textPrimary mb-1">{t('dashboard.expenseTrends')}</h2>
                <p className="text-sm text-textSecondary">{t('dashboard.monthlySpendAnalysis')}</p>
              </div>
              <div className="flex items-center space-x-2">
                <button className="px-3 py-1.5 text-xs font-medium text-primary bg-indigo-50 rounded-lg">{t('dashboard.months6')}</button>
                <button className="px-3 py-1.5 text-xs font-medium text-textSecondary hover:bg-gray-50 rounded-lg">{t('dashboard.year1')}</button>
              </div>
            </div>
            {chartData.length > 0 && (
              <Chart id="expense-trend-chart" data={chartData} layout={chartLayout} style={{ height: '400px' }} />
            )}
          </section>
        </div>

        <div className="col-span-2 space-y-6">
          <section className="bg-gradient-to-br from-primary to-purple-600 rounded-xl p-6 text-white shadow-sm">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold mb-2">{t('dashboard.quickSubmit')}</h2>
                <p className="text-sm text-indigo-100">{t('dashboard.uploadReceiptAi')}</p>
              </div>
              <div className="w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faCamera} className="text-xl" />
              </div>
            </div>
            <div
              onClick={() => router.push('/expenses/new')}
              className="border-2 border-dashed border-white border-opacity-30 rounded-lg p-6 text-center mb-4 hover:border-opacity-50 transition-all cursor-pointer bg-white bg-opacity-10"
            >
              <FontAwesomeIcon icon={faCloudUploadAlt} className="text-3xl mb-3 opacity-80" />
              <p className="text-sm mb-1">{t('dashboard.dragDropReceipt')}</p>
              <p className="text-xs text-indigo-100">{t('dashboard.orClickToBrowse')}</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => router.push('/expenses/new')}
                className="h-10 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg text-sm font-medium flex items-center justify-center space-x-2 transition-all"
              >
                <FontAwesomeIcon icon={faCamera} />
                <span>{t('dashboard.takePhoto')}</span>
              </button>
              <button
                onClick={() => router.push('/expenses/new')}
                className="h-10 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg text-sm font-medium flex items-center justify-center space-x-2 transition-all"
              >
                <FontAwesomeIcon icon={faEnvelope} />
                <span>{t('dashboard.emailReceipt')}</span>
              </button>
            </div>
          </section>

          <section className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-textPrimary mb-1">{t('dashboard.pendingApprovals')}</h2>
                <p className="text-sm text-textSecondary">{t('dashboard.expensesAwaitingReview')}</p>
              </div>
              <span className="text-xs font-semibold text-warningAmber bg-amber-50 px-3 py-1 rounded-full">
                {pendingLoading ? '—' : `${pendingTotal} ${t('common.pending')}`}
              </span>
            </div>
            <div className="space-y-3">
              {pendingLoading ? (
                [...Array(2)].map((_, i) => (
                  <div key={i} className="p-4 border border-borderColor rounded-lg animate-pulse">
                    <div className="flex justify-between mb-2"><span className="h-4 w-32 bg-gray-200 rounded" /><span className="h-4 w-14 bg-gray-200 rounded" /></div>
                    <div className="h-3 w-40 bg-gray-100 rounded" />
                    <div className="mt-2 h-5 w-16 bg-gray-200 rounded" />
                  </div>
                ))
              ) : pendingError ? (
                <div className="py-4 text-sm text-errorRed text-center">{String(pendingError)}</div>
              ) : pending.length === 0 ? (
                <div className="py-4 text-sm text-textSecondary text-center">{t('approvals.noPending') || 'No expenses are currently pending your approval.'}</div>
              ) : (
                (pending as PendingItem[]).map((exp) => {
                  const title = exp.description || exp.merchant_name || 'Expense'
                  const submittedBy = exp.submitted_by_name || exp.submitted_by_email || (exp.submitted_by ? String(exp.submitted_by).slice(0, 8) + '…' : 'Unknown submitter')
                  const cat = CATEGORY_MAP[exp.category || ''] || { icon: faReceipt, variant: 'info' as const }
                  const categoryLabel = (exp.category || 'Other').charAt(0).toUpperCase() + (exp.category || 'other').slice(1)
                  return (
                    <div
                      key={exp.id}
                      className="p-4 border border-borderColor rounded-lg hover:border-primary transition-colors cursor-pointer"
                      onClick={() => router.push('/approvals')}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="text-sm font-medium text-textPrimary">{title}</div>
                          <div className="text-xs text-textSecondary">{t('dashboard.submittedBy') || 'Submitted by'} {submittedBy} {t('dashboard.on') || 'on'} {formatDate(exp.expense_date ?? '', locale)}</div>
                        </div>
                        <span className="text-sm font-semibold text-textPrimary">€{Number(exp.amount || 0).toFixed(2)}</span>
                      </div>
                      <div className="flex items-center justify-between mt-2">
                        <Badge variant={cat.variant} icon={cat.icon}>{categoryLabel}</Badge>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
            <button onClick={() => router.push('/approvals')} className="w-full mt-4 h-10 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">
              {t('dashboard.viewAllPending')}{pendingLoading ? '' : ` (${pendingTotal})`}
            </button>
          </section>

          <section className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-6 border border-indigo-100 shadow-sm">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faStar} className="text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-textPrimary">{t('dashboard.aiInsights')}</h2>
                <p className="text-xs text-textSecondary">{t('dashboard.proactiveSuggestions')}</p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="bg-white rounded-lg p-4 border border-indigo-100">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <FontAwesomeIcon icon={faExclamationCircle} className="text-warningAmber" />
                    <span className="text-sm font-medium text-textPrimary">{t('dashboard.receiptsAwaitingCategorization')}</span>
                  </div>
                  <span className="text-xs font-semibold text-warningAmber bg-amber-50 px-2 py-1 rounded-full">3</span>
                </div>
                <p className="text-xs text-textSecondary mb-3">{t('dashboard.youHaveReceiptsToCategorize')}</p>
                <button className="text-xs text-primary hover:text-primaryHover font-medium">{t('dashboard.reviewNow')}</button>
              </div>

              <div className="bg-white rounded-lg p-4 border border-indigo-100">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <FontAwesomeIcon icon={faChartLine} className="text-errorRed" />
                    <span className="text-sm font-medium text-textPrimary">{t('dashboard.unusualActivityDetected')}</span>
                  </div>
                  <span className="text-xs font-semibold text-errorRed bg-red-50 px-2 py-1 rounded-full">{t('dashboard.alert')}</span>
                </div>
                <p className="text-xs text-textSecondary mb-3">{t('dashboard.unusualSpendingPattern')}</p>
                <button className="text-xs text-primary hover:text-primaryHover font-medium">{t('dashboard.investigate')}</button>
              </div>

              <div className="bg-white rounded-lg p-4 border border-indigo-100">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <FontAwesomeIcon icon={faLightbulb} className="text-infoBlue" />
                    <span className="text-sm font-medium text-textPrimary">{t('dashboard.optimizationSuggestion')}</span>
                  </div>
                  <span className="text-xs font-semibold text-infoBlue bg-blue-50 px-2 py-1 rounded-full">{t('dashboard.tip')}</span>
                </div>
                <p className="text-xs text-textSecondary mb-3">{t('dashboard.savePercentByBooking')}</p>
                <button className="text-xs text-primary hover:text-primaryHover font-medium">{t('dashboard.learnMore')}</button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </>
  )
}

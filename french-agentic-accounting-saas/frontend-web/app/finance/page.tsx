'use client'

import { useEffect, useMemo, useState } from 'react'
import Chart from '@/components/ui/Chart'
import Badge from '@/components/ui/Badge'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faEuroSign,
  faClock,
  faCheckCircle,
  faExclamationCircle,
  faCalendar,
  faFilter,
  faDownload,
  faArrowUp,
  faChevronDown,
} from '@fortawesome/free-solid-svg-icons'
import { adminAPI, anomalyAPI, expensesAPI, getAuthErrorMessage } from '@/lib/api'

type Period = 'month' | 'quarter'

type FinanceSummary = {
  totalSpend: number
  pendingAmount: number
  pendingCount: number
  approvedAmount: number
  approvedCount: number
  violationsAmount: number
  violationsCount: number
}

type CategoryStat = {
  name: string
  amount: number
}

export default function FinanceDashboardPage() {
  const [period, setPeriod] = useState<Period>('month')
  const [summary, setSummary] = useState<FinanceSummary>({
    totalSpend: 0,
    pendingAmount: 0,
    pendingCount: 0,
    approvedAmount: 0,
    approvedCount: 0,
    violationsAmount: 0,
    violationsCount: 0,
  })
  const [categoryStats, setCategoryStats] = useState<CategoryStat[]>([])
  const [policyStats, setPolicyStats] = useState<{
    compliant_percent: number
    violations_percent: number
  } | null>(null)
  const [riskScore, setRiskScore] = useState<number>(0)
  const [chartData, setChartData] = useState<any[]>([])
  const [chartLayout, setChartLayout] = useState<any>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { startDate, endDate, periodLabel } = useMemo(() => {
    const now = new Date()
    const end = now
    const start = new Date(now)
    if (period === 'quarter') {
      const currentQuarter = Math.floor(now.getMonth() / 3)
      start.setMonth(currentQuarter * 3, 1)
    } else {
      start.setDate(1)
    }
    const toIso = (d: Date) => d.toISOString().slice(0, 10)
    return {
      startDate: toIso(start),
      endDate: toIso(end),
      periodLabel: period === 'quarter' ? 'This Quarter' : 'This Month',
    }
  }, [period])

  useEffect(() => {
    const loadFinanceData = async () => {
      setLoading(true)
      setError(null)
      try {
        // 1) Load expenses for the selected period
        const expensesRes: any = await expensesAPI.list({
          page: 1,
          page_size: 100,
          start_date: startDate,
          end_date: endDate,
        })
        const expenses: any[] = Array.isArray(expensesRes?.data)
          ? expensesRes.data
          : Array.isArray(expensesRes)
          ? expensesRes
          : expensesRes?.items ?? []

        const nonDraft = expenses.filter((e) => (e.status || '').toLowerCase() !== 'draft')

        const totalSpend = nonDraft.reduce((sum, e) => sum + Number(e.amount ?? 0), 0)
        const pending = nonDraft.filter(
          (e) =>
            (e.status || '').toLowerCase() === 'submitted' ||
            (e.approval_status || '').toLowerCase() === 'pending',
        )
        const approved = nonDraft.filter((e) => (e.status || '').toLowerCase() === 'approved')

        const pendingAmount = pending.reduce((sum, e) => sum + Number(e.amount ?? 0), 0)
        const approvedAmount = approved.reduce((sum, e) => sum + Number(e.amount ?? 0), 0)

        // Category distribution
        const byCategory = new Map<string, number>()
        nonDraft.forEach((e) => {
          const key = (e.category || 'Uncategorized') as string
          const amt = Number(e.amount ?? 0)
          byCategory.set(key, (byCategory.get(key) ?? 0) + amt)
        })
        const catStats = Array.from(byCategory.entries())
          .map(([name, amount]) => ({ name, amount }))
          .sort((a, b) => b.amount - a.amount)
          .slice(0, 5)

        setCategoryStats(catStats)

        // Expense trends (group by month label)
        const monthKey = (dStr: string) => {
          const d = new Date(dStr)
          return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
        }
        const monthLabels: string[] = []
        const approvedByMonth: Record<string, number> = {}
        const pendingByMonth: Record<string, number> = {}
        const rejectedByMonth: Record<string, number> = {}

        nonDraft.forEach((e) => {
          const label = monthKey(e.expense_date)
          if (!monthLabels.includes(label)) monthLabels.push(label)
          const status = (e.status || '').toLowerCase()
          const amt = Number(e.amount ?? 0)
          if (status === 'approved') {
            approvedByMonth[label] = (approvedByMonth[label] ?? 0) + amt
          } else if (status === 'submitted') {
            pendingByMonth[label] = (pendingByMonth[label] ?? 0) + amt
          } else if (status === 'rejected') {
            rejectedByMonth[label] = (rejectedByMonth[label] ?? 0) + amt
          }
        })

        monthLabels.sort()

        const financeData = [
          {
            type: 'bar',
            name: 'Approved',
            x: monthLabels,
            y: monthLabels.map((m) => approvedByMonth[m] ?? 0),
            marker: { color: '#10B981' },
          },
          {
            type: 'bar',
            name: 'Pending',
            x: monthLabels,
            y: monthLabels.map((m) => pendingByMonth[m] ?? 0),
            marker: { color: '#F59E0B' },
          },
          {
            type: 'bar',
            name: 'Rejected',
            x: monthLabels,
            y: monthLabels.map((m) => rejectedByMonth[m] ?? 0),
            marker: { color: '#EF4444' },
          },
        ]

        const financeLayout = {
          title: { text: '', font: { size: 0 } },
          barmode: 'stack' as const,
          xaxis: { title: 'Period', showgrid: false },
          yaxis: { title: 'Amount (€)', showgrid: true, gridcolor: '#E5E7EB' },
          margin: { t: 20, r: 20, b: 60, l: 60 },
          plot_bgcolor: '#FFFFFF',
          paper_bgcolor: '#FFFFFF',
          showlegend: true,
          legend: { orientation: 'h' as const, y: -0.2 },
        }

        setChartData(financeData)
        setChartLayout(financeLayout)

        // 2) Policy stats & violations
        let violationsAmount = 0
        let violationsCount = 0
        try {
          const violations = await adminAPI.getPolicyViolations(50)
          violationsAmount = violations.reduce((sum, v) => sum + Number(v.amount ?? 0), 0)
          violationsCount = violations.length
        } catch {
          // best-effort only
        }

        try {
          const stats = await adminAPI.getPolicyStats()
          setPolicyStats(stats)
          // Simple risk score derived from violations percent (0–100)
          const rs = stats.violations_percent
          setRiskScore(Number.isFinite(rs) ? rs : 0)
        } catch {
          setPolicyStats(null)
        }

        setSummary({
          totalSpend,
          pendingAmount,
          pendingCount: pending.length,
          approvedAmount,
          approvedCount: approved.length,
          violationsAmount,
          violationsCount,
        })
      } catch (err: unknown) {
        setError(getAuthErrorMessage(err, 'Failed to load finance dashboard data'))
      } finally {
        setLoading(false)
      }
    }

    loadFinanceData()
  }, [startDate, endDate])

  const handleExport = async () => {
    try {
      const expensesRes: any = await expensesAPI.list({
        page: 1,
        page_size: 100,
        start_date: startDate,
        end_date: endDate,
      })
      const expenses: any[] = Array.isArray(expensesRes?.data)
        ? expensesRes.data
        : Array.isArray(expensesRes)
        ? expensesRes
        : expensesRes?.items ?? []

      const header = ['Date', 'Category', 'Merchant', 'Amount', 'Currency', 'Status']
      const rows = expenses.map((e) => [
        e.expense_date,
        e.category || '',
        e.merchant_name || '',
        String(e.amount ?? ''),
        e.currency || '',
        e.status || '',
      ])
      const csv = [header, ...rows].map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n')
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `finance-dashboard-${startDate}-to-${endDate}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err: unknown) {
      alert(getAuthErrorMessage(err, 'Failed to export finance report'))
    }
  }

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">Finance Dashboard</h1>
            <p className="text-textSecondary">Financial overview, analytics, and compliance monitoring</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2"
              onClick={() => setPeriod((prev) => (prev === 'month' ? 'quarter' : 'month'))}
            >
              <FontAwesomeIcon icon={faCalendar} />
              <span>Date Range</span>
            </button>
            <button className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
              <FontAwesomeIcon icon={faFilter} />
              <span>Filter</span>
            </button>
            <button
              onClick={handleExport}
              className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2"
            >
              <FontAwesomeIcon icon={faDownload} />
              <span>Export Report</span>
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center space-x-2">
            <span className="text-textSecondary">Period:</span>
            <button className="px-3 py-1.5 border border-borderColor rounded-lg text-textPrimary hover:bg-gray-50 flex items-center space-x-2">
              <span>{periodLabel}</span>
              <FontAwesomeIcon icon={faChevronDown} className="text-xs" />
            </button>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-textSecondary">Cost Center:</span>
            <button className="px-3 py-1.5 border border-borderColor rounded-lg text-textPrimary hover:bg-gray-50 flex items-center space-x-2">
              <span>All Centers</span>
              <FontAwesomeIcon icon={faChevronDown} className="text-xs" />
            </button>
          </div>
          <div className="h-4 w-px bg-borderColor"></div>
          <div className="text-textMuted">Last updated: 5 minutes ago</div>
        </div>
      </section>

      <section className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faEuroSign} className="text-primary text-xl" />
            </div>
            <span className="text-xs font-medium text-successGreen bg-green-50 px-2 py-1 rounded-full">
              +5.2%
            </span>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">
            €{summary.totalSpend.toLocaleString('fr-FR', { maximumFractionDigits: 2 })}
          </div>
          <div className="text-sm text-textSecondary">Total Spend</div>
          <div className="mt-4 text-xs text-textMuted">{periodLabel}</div>
        </div>

        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-amber-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faClock} className="text-warningAmber text-xl" />
            </div>
            <span className="text-xs font-medium text-warningAmber bg-amber-50 px-2 py-1 rounded-full">
              {summary.pendingCount}
            </span>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">
            €{summary.pendingAmount.toLocaleString('fr-FR', { maximumFractionDigits: 2 })}
          </div>
          <div className="text-sm text-textSecondary">Pending Reimbursement</div>
          <div className="mt-4 text-xs text-textMuted">
            {summary.pendingCount} {summary.pendingCount === 1 ? 'expense awaiting approval' : 'expenses awaiting approval'}
          </div>
        </div>

        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faCheckCircle} className="text-successGreen text-xl" />
            </div>
            <span className="text-xs font-medium text-successGreen bg-green-50 px-2 py-1 rounded-full">
              {summary.totalSpend > 0
                ? `${((summary.approvedAmount / summary.totalSpend) * 100).toFixed(1)}%`
                : '0%'}
            </span>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">
            €{summary.approvedAmount.toLocaleString('fr-FR', { maximumFractionDigits: 2 })}
          </div>
          <div className="text-sm text-textSecondary">Approved & Reimbursed</div>
          <div className="mt-4 text-xs text-textMuted">This month total</div>
        </div>

        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-red-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faExclamationCircle} className="text-errorRed text-xl" />
            </div>
            <span className="text-xs font-medium text-errorRed bg-red-50 px-2 py-1 rounded-full">
              {summary.violationsCount}
            </span>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">
            €{summary.violationsAmount.toLocaleString('fr-FR', { maximumFractionDigits: 2 })}
          </div>
          <div className="text-sm text-textSecondary">Policy Violations</div>
          <div className="mt-4 text-xs text-textMuted">Requires review</div>
        </div>
      </section>

      <section className="grid grid-cols-3 gap-6 mb-8">
        <div className="col-span-2 bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-textPrimary mb-1">Expense Trends</h2>
              <p className="text-sm text-textSecondary">Monthly expense breakdown by status</p>
            </div>
            <div className="flex items-center space-x-2">
              <button className="px-3 py-1.5 text-xs font-medium text-primary bg-indigo-50 rounded-lg">
                Monthly
              </button>
              <button className="px-3 py-1.5 text-xs font-medium text-textSecondary hover:bg-gray-50 rounded-lg">
                Quarterly
              </button>
            </div>
          </div>
          {chartData.length > 0 && (
            <Chart id="finance-chart" data={chartData} layout={chartLayout} style={{ height: '400px' }} />
          )}
        </div>

        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-textPrimary mb-1">Category Distribution</h2>
            <p className="text-sm text-textSecondary">{periodLabel} breakdown</p>
          </div>
          <div className="space-y-4">
            {categoryStats.length === 0 && (
              <div className="text-xs text-textMuted">No expenses found for the selected period.</div>
            )}
            {categoryStats.map((cat, idx) => {
              const max = categoryStats[0]?.amount || 1
              const width = `${Math.max(5, Math.round((cat.amount / max) * 100))}%`
              const barColors = ['bg-infoBlue', 'bg-purple-600', 'bg-successGreen', 'bg-warningAmber', 'bg-errorRed']
              const barColor = barColors[idx] ?? 'bg-infoBlue'
              return (
                <div key={cat.name}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-textPrimary">{cat.name}</span>
                    <span className="text-sm font-medium text-textPrimary">
                      €{cat.amount.toLocaleString('fr-FR', { maximumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className={`h-full ${barColor}`} style={{ width }}></div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-6 mb-8">
        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-textPrimary mb-1">Compliance Status</h2>
              <p className="text-sm text-textSecondary">URSSAF & VAT compliance monitoring</p>
            </div>
            <button className="text-sm text-primary hover:text-primaryHover font-medium">View Details</button>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-lowRisk rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-successGreen rounded-lg flex items-center justify-center">
                  <FontAwesomeIcon icon={faCheckCircle} className="text-white" />
                </div>
                <div>
                  <div className="text-sm font-medium text-textPrimary">URSSAF Compliant</div>
                  <div className="text-xs text-textSecondary">All meal vouchers within limits</div>
                </div>
              </div>
              <span className="text-xs font-semibold text-successGreen">100%</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-lowRisk rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-successGreen rounded-lg flex items-center justify-center">
                  <FontAwesomeIcon icon={faCheckCircle} className="text-white" />
                </div>
                <div>
                  <div className="text-sm font-medium text-textPrimary">VAT Compliance</div>
                  <div className="text-xs text-textSecondary">All receipts properly documented</div>
                </div>
              </div>
              <span className="text-xs font-semibold text-successGreen">98.5%</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-mediumRisk rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-warningAmber rounded-lg flex items-center justify-center">
                  <FontAwesomeIcon icon={faExclamationCircle} className="text-white" />
                </div>
                <div>
                  <div className="text-sm font-medium text-textPrimary">GDPR Data Retention</div>
                  <div className="text-xs text-textSecondary">3 documents require review</div>
                </div>
              </div>
              <span className="text-xs font-semibold text-warningAmber">96.2%</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-highRisk rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-errorRed rounded-lg flex items-center justify-center">
                  <FontAwesomeIcon icon={faExclamationCircle} className="text-white" />
                </div>
                <div>
                  <div className="text-sm font-medium text-textPrimary">Policy Violations</div>
                  <div className="text-xs text-textSecondary">8 expenses exceed limits</div>
                </div>
              </div>
              <span className="text-xs font-semibold text-errorRed">Alert</span>
            </div>
          </div>
        </div>

        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-textPrimary mb-1">Risk Assessment</h2>
              <p className="text-sm text-textSecondary">AI-powered anomaly detection</p>
            </div>
            <button className="text-sm text-primary hover:text-primaryHover font-medium">View All Risks</button>
          </div>

          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-textSecondary">Overall Risk Score</span>
              <span className="text-2xl font-bold text-successGreen">
                {Math.round(riskScore)}/100
              </span>
            </div>
            <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-successGreen to-green-400"
                style={{ width: `${Math.min(100, Math.max(5, riskScore))}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-xs text-textMuted mt-1">
              <span>Low Risk</span>
              <span>High Risk</span>
            </div>
          </div>

          <div className="space-y-3">
            <div className="p-4 border border-borderColor rounded-lg hover:border-primary transition-colors cursor-pointer">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-warningAmber rounded-full"></span>
                  <span className="text-sm font-medium text-textPrimary">Duplicate Receipt Detection</span>
                </div>
                <Badge variant="warning">Medium</Badge>
              </div>
              <p className="text-xs text-textSecondary mb-2">
                2 potential duplicate expenses detected in transport category
              </p>
              <div className="flex items-center justify-between">
                <span className="text-xs text-textMuted">Risk Score: 45</span>
                <button className="text-xs text-primary hover:text-primaryHover font-medium">Investigate</button>
              </div>
            </div>

            <div className="p-4 border border-borderColor rounded-lg hover:border-primary transition-colors cursor-pointer">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-successGreen rounded-full"></span>
                  <span className="text-sm font-medium text-textPrimary">Unusual Spending Pattern</span>
                </div>
                <Badge variant="success">Low</Badge>
              </div>
              <p className="text-xs text-textSecondary mb-2">
                Employee meal expenses 15% above average this month
              </p>
              <div className="flex items-center justify-between">
                <span className="text-xs text-textMuted">Risk Score: 28</span>
                <button className="text-xs text-primary hover:text-primaryHover font-medium">Review</button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}

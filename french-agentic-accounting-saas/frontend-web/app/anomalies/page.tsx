'use client'

import { useEffect, useState } from 'react'
import Chart from '@/components/ui/Chart'
import Badge from '@/components/ui/Badge'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faExclamationTriangle,
  faExclamationCircle,
  faUsers,
  faStore,
  faDownload,
  faFilter,
  faBrain,
  faChevronDown,
  faEuroSign,
  faChartLine,
  faClock,
  faReceipt,
  faFileCircleXmark,
  faLightbulb,
  faShield,
} from '@fortawesome/free-solid-svg-icons'

export default function AnomaliesPage() {
  const [chartData, setChartData] = useState<any[]>([])
  const [chartLayout, setChartLayout] = useState<any>({})

  useEffect(() => {
    const riskData = [
      {
        type: 'scatter',
        mode: 'lines+markers',
        name: 'High Risk',
        x: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        y: [3, 5, 4, 8],
        line: { color: '#EF4444', width: 3 },
        marker: { color: '#EF4444', size: 8 },
      },
      {
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Medium Risk',
        x: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        y: [8, 12, 10, 15],
        line: { color: '#F59E0B', width: 3 },
        marker: { color: '#F59E0B', size: 8 },
      },
      {
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Low Risk',
        x: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        y: [15, 18, 20, 22],
        line: { color: '#10B981', width: 3 },
        marker: { color: '#10B981', size: 8 },
      },
    ]

    const riskLayout = {
      title: { text: '', font: { size: 0 } },
      xaxis: { title: 'Week', showgrid: false },
      yaxis: { title: 'Number of Anomalies', showgrid: true, gridcolor: '#E5E7EB' },
      margin: { t: 20, r: 20, b: 60, l: 60 },
      plot_bgcolor: '#FFFFFF',
      paper_bgcolor: '#FFFFFF',
      showlegend: true,
      legend: { orientation: 'h' as const, y: -0.2 },
    }

    setChartData(riskData)
    setChartLayout(riskLayout)
  }, [])

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">Anomaly Detection & Risk Dashboard</h1>
            <p className="text-textSecondary">AI-powered detection of suspicious patterns and policy violations</p>
          </div>
          <div className="flex items-center space-x-3">
            <button className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
              <FontAwesomeIcon icon={faDownload} />
              <span>Export Report</span>
            </button>
            <button className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
              <FontAwesomeIcon icon={faFilter} />
              <span>Filter</span>
            </button>
            <button className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2">
              <FontAwesomeIcon icon={faBrain} />
              <span>Run AI Analysis</span>
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center space-x-2">
            <span className="text-textSecondary">Time Range:</span>
            <button className="px-3 py-1.5 border border-borderColor rounded-lg text-textPrimary hover:bg-gray-50 flex items-center space-x-2">
              <span>Last 30 days</span>
              <FontAwesomeIcon icon={faChevronDown} className="text-xs" />
            </button>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-textSecondary">Risk Level:</span>
            <button className="px-3 py-1.5 border border-borderColor rounded-lg text-textPrimary hover:bg-gray-50 flex items-center space-x-2">
              <span>All Levels</span>
              <FontAwesomeIcon icon={faChevronDown} className="text-xs" />
            </button>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-textSecondary">Status:</span>
            <button className="px-3 py-1.5 border border-borderColor rounded-lg text-textPrimary hover:bg-gray-50 flex items-center space-x-2">
              <span>Pending Review</span>
              <FontAwesomeIcon icon={faChevronDown} className="text-xs" />
            </button>
          </div>
          <div className="h-4 w-px bg-borderColor"></div>
          <div className="text-textMuted">Last AI scan: 5 minutes ago</div>
        </div>
      </section>

      <section className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-surface rounded-xl p-6 border-2 border-errorRed shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-red-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faExclamationTriangle} className="text-errorRed text-xl" />
            </div>
            <span className="text-xs font-semibold text-errorRed bg-red-50 px-3 py-1 rounded-full">Critical</span>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">8</div>
          <div className="text-sm text-textSecondary mb-3">High Risk Expenses</div>
          <div className="text-xl font-semibold text-errorRed">€12,847</div>
          <div className="mt-4 flex items-center space-x-2">
            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div className="h-full bg-errorRed" style={{ width: '35%' }}></div>
            </div>
            <span className="text-xs font-medium text-errorRed">+35%</span>
          </div>
        </div>

        <div className="bg-surface rounded-xl p-6 border border-warningAmber shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-amber-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faExclamationCircle} className="text-warningAmber text-xl" />
            </div>
            <span className="text-xs font-semibold text-warningAmber bg-amber-50 px-3 py-1 rounded-full">
              Warning
            </span>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">15</div>
          <div className="text-sm text-textSecondary mb-3">Medium Risk Expenses</div>
          <div className="text-xl font-semibold text-warningAmber">€8,234</div>
          <div className="mt-4 flex items-center space-x-2">
            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div className="h-full bg-warningAmber" style={{ width: '22%' }}></div>
            </div>
            <span className="text-xs font-medium text-warningAmber">+22%</span>
          </div>
        </div>

        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-purple-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faUsers} className="text-purple-600 text-xl" />
            </div>
            <span className="text-xs font-semibold text-purple-600 bg-purple-50 px-3 py-1 rounded-full">
              Flagged
            </span>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">12</div>
          <div className="text-sm text-textSecondary mb-3">Flagged Employees</div>
          <div className="text-sm text-textMuted mt-3">Multiple violations detected</div>
          <div className="mt-4 flex items-center space-x-2">
            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div className="h-full bg-purple-600" style={{ width: '18%' }}></div>
            </div>
            <span className="text-xs font-medium text-purple-600">+18%</span>
          </div>
        </div>

        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-orange-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faStore} className="text-orange-600 text-xl" />
            </div>
            <span className="text-xs font-semibold text-orange-600 bg-orange-50 px-3 py-1 rounded-full">
              Alert
            </span>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">5</div>
          <div className="text-sm text-textSecondary mb-3">Suspicious Merchants</div>
          <div className="text-xs text-textMuted mt-3">
            <div className="flex items-center space-x-1 mb-1">
              <span>•</span>
              <span>Restaurant XYZ (3 flags)</span>
            </div>
            <div className="flex items-center space-x-1">
              <span>•</span>
              <span>Hotel ABC (2 flags)</span>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-textPrimary mb-1">Risk Distribution Over Time</h2>
            <p className="text-sm text-textSecondary">Anomaly detection trends by severity level</p>
          </div>
          <div className="flex items-center space-x-2">
            <button className="px-3 py-1.5 text-xs font-medium text-primary bg-indigo-50 rounded-lg">Weekly</button>
            <button className="px-3 py-1.5 text-xs font-medium text-textSecondary hover:bg-gray-50 rounded-lg">
              Monthly
            </button>
            <button className="px-3 py-1.5 text-xs font-medium text-textSecondary hover:bg-gray-50 rounded-lg">
              Quarterly
            </button>
          </div>
        </div>
        {chartData.length > 0 && (
          <Chart id="anomaly-chart" data={chartData} layout={chartLayout} style={{ height: '400px' }} />
        )}
      </section>

      <section className="grid grid-cols-3 gap-6 mb-8">
        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-textPrimary">Anomaly Types</h2>
            <button className="text-sm text-primary hover:text-primaryHover font-medium">View All</button>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 border border-borderColor rounded-lg hover:border-errorRed cursor-pointer transition-colors">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-red-50 rounded-lg flex items-center justify-center">
                  <FontAwesomeIcon icon={faEuroSign} className="text-errorRed" />
                </div>
                <div>
                  <div className="text-sm font-medium text-textPrimary">Amount Anomaly</div>
                  <div className="text-xs text-textSecondary">Unusual spending</div>
                </div>
              </div>
              <span className="text-lg font-bold text-errorRed">8</span>
            </div>

            <div className="flex items-center justify-between p-3 border border-borderColor rounded-lg hover:border-warningAmber cursor-pointer transition-colors">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-amber-50 rounded-lg flex items-center justify-center">
                  <FontAwesomeIcon icon={faChartLine} className="text-warningAmber" />
                </div>
                <div>
                  <div className="text-sm font-medium text-textPrimary">Pattern Anomaly</div>
                  <div className="text-xs text-textSecondary">Repeated behavior</div>
                </div>
              </div>
              <span className="text-lg font-bold text-warningAmber">6</span>
            </div>

            <div className="flex items-center justify-between p-3 border border-borderColor rounded-lg hover:border-purple-600 cursor-pointer transition-colors">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center">
                  <FontAwesomeIcon icon={faClock} className="text-purple-600" />
                </div>
                <div>
                  <div className="text-sm font-medium text-textPrimary">Timing Anomaly</div>
                  <div className="text-xs text-textSecondary">Unusual submission time</div>
                </div>
              </div>
              <span className="text-lg font-bold text-purple-600">4</span>
            </div>

            <div className="flex items-center justify-between p-3 border border-borderColor rounded-lg hover:border-orange-600 cursor-pointer transition-colors">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-orange-50 rounded-lg flex items-center justify-center">
                  <FontAwesomeIcon icon={faReceipt} className="text-orange-600" />
                </div>
                <div>
                  <div className="text-sm font-medium text-textPrimary">VAT Anomaly</div>
                  <div className="text-xs text-textSecondary">Missing or incorrect</div>
                </div>
              </div>
              <span className="text-lg font-bold text-orange-600">3</span>
            </div>

            <div className="flex items-center justify-between p-3 border border-borderColor rounded-lg hover:border-pink-600 cursor-pointer transition-colors">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-pink-50 rounded-lg flex items-center justify-center">
                  <FontAwesomeIcon icon={faFileCircleXmark} className="text-pink-600" />
                </div>
                <div>
                  <div className="text-sm font-medium text-textPrimary">Document Anomaly</div>
                  <div className="text-xs text-textSecondary">Missing receipts</div>
                </div>
              </div>
              <span className="text-lg font-bold text-pink-600">2</span>
            </div>
          </div>
        </div>

        <div className="col-span-2 bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-textPrimary">AI Detection Insights</h2>
              <p className="text-sm text-textSecondary">Machine learning analysis summary</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-100">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                  <FontAwesomeIcon icon={faBrain} className="text-white" />
                </div>
                <div>
                  <div className="text-xs text-textMuted">Detection Accuracy</div>
                  <div className="text-xl font-bold text-textPrimary">94.8%</div>
                </div>
              </div>
              <p className="text-xs text-textSecondary">AI model confidence score for current analysis</p>
            </div>

            <div className="p-4 bg-green-50 rounded-lg border border-green-100">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-10 h-10 bg-successGreen rounded-lg flex items-center justify-center">
                  <FontAwesomeIcon icon={faShield} className="text-white" />
                </div>
                <div>
                  <div className="text-xs text-textMuted">False Positive Rate</div>
                  <div className="text-xl font-bold text-textPrimary">2.3%</div>
                </div>
              </div>
              <p className="text-xs text-textSecondary">Reduced by 45% with latest model update</p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="p-4 bg-gradient-to-r from-red-50 to-amber-50 rounded-lg border border-red-100">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <FontAwesomeIcon icon={faLightbulb} className="text-warningAmber" />
                  <span className="text-sm font-semibold text-textPrimary">Top Risk Pattern Detected</span>
                </div>
                <span className="text-xs font-medium text-errorRed bg-red-100 px-2 py-1 rounded-full">
                  High Priority
                </span>
              </div>
              <p className="text-xs text-textSecondary mb-3">
                Employee &quot;Marie Laurent&quot; has submitted 5 expenses exceeding daily meal limits in the past
                7 days. Pattern suggests potential policy violation.
              </p>
              <button className="text-xs text-primary hover:text-primaryHover font-medium">Investigate →</button>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}

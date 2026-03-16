'use client'

import { useState } from 'react'
import Badge from '@/components/ui/Badge'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faClipboardCheck,
  faHourglassHalf,
  faCheckCircle,
  faBrain,
  faFilter,
  faDownload,
  faPlus,
  faSearch,
  faSortAmountDown,
  faEye,
  faEdit,
  faShareAlt,
  faEllipsisV,
  faFileAlt,
  faCalendar,
  faShieldAlt,
  faBuilding,
} from '@fortawesome/free-solid-svg-icons'

export default function AuditReportsPage() {
  const [activeTab, setActiveTab] = useState('all')

  const reports = [
    {
      id: 1,
      name: 'Q4 2024 Expense Audit',
      description: 'Comprehensive quarterly review',
      type: 'Periodic',
      typeIcon: faCalendar,
      typeVariant: 'info' as const,
      period: 'Oct - Dec 2024',
      periodDetail: '3 months',
      entity: 'Dou France SAS',
      entityDetail: 'All departments',
      status: 'Completed',
      statusVariant: 'success' as const,
      created: 'Jan 10, 2025',
      createdDetail: '5 days ago',
      createdBy: 'Jean Dupont',
      createdByAvatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-2.jpg',
      iconBg: 'bg-primary bg-opacity-10',
      iconColor: 'text-primary',
    },
    {
      id: 2,
      name: 'URSSAF Compliance Check',
      description: 'Meal voucher & benefits audit',
      type: 'URSSAF Prep',
      typeIcon: faShieldAlt,
      typeVariant: 'success' as const,
      period: 'Jan 2025',
      periodDetail: '1 month',
      entity: 'Dou France SAS',
      entityDetail: 'All entities',
      status: 'In Progress',
      statusVariant: 'warning' as const,
      created: 'Jan 12, 2025',
      createdDetail: '3 days ago',
      createdBy: 'Sophie Martin',
      createdByAvatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-5.jpg',
      iconBg: 'bg-amber-50',
      iconColor: 'text-warningAmber',
    },
    {
      id: 3,
      name: 'External Audit Preparation',
      description: 'Annual financial audit support',
      type: 'External Audit',
      typeIcon: faBuilding,
      typeVariant: 'purple' as const,
      period: 'FY 2024',
      periodDetail: '12 months',
      entity: 'Dou France SAS',
      entityDetail: 'All entities',
      status: 'In Progress',
      statusVariant: 'warning' as const,
      created: 'Jan 8, 2025',
      createdDetail: '7 days ago',
      createdBy: 'Thomas Bernard',
      createdByAvatar: 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-4.jpg',
      iconBg: 'bg-purple-50',
      iconColor: 'text-purple-600',
    },
  ]

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">Audit Reports</h1>
            <p className="text-textSecondary">Generate and manage comprehensive audit reports with AI-powered insights</p>
          </div>
          <div className="flex items-center space-x-3">
            <button className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
              <FontAwesomeIcon icon={faFilter} />
              <span>Filter</span>
            </button>
            <button className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
              <FontAwesomeIcon icon={faDownload} />
              <span>Export</span>
            </button>
            <button className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2">
              <FontAwesomeIcon icon={faPlus} />
              <span>New Audit Report</span>
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-4 py-2 text-sm font-medium rounded-lg ${
              activeTab === 'all' ? 'text-primary bg-indigo-50' : 'text-textSecondary hover:bg-gray-50'
            }`}
          >
            All Reports
          </button>
          <button
            onClick={() => setActiveTab('draft')}
            className={`px-4 py-2 text-sm font-medium rounded-lg ${
              activeTab === 'draft' ? 'text-primary bg-indigo-50' : 'text-textSecondary hover:bg-gray-50'
            }`}
          >
            Draft
          </button>
          <button
            onClick={() => setActiveTab('in-progress')}
            className={`px-4 py-2 text-sm font-medium rounded-lg ${
              activeTab === 'in-progress' ? 'text-primary bg-indigo-50' : 'text-textSecondary hover:bg-gray-50'
            }`}
          >
            In Progress
          </button>
          <button
            onClick={() => setActiveTab('completed')}
            className={`px-4 py-2 text-sm font-medium rounded-lg ${
              activeTab === 'completed' ? 'text-primary bg-indigo-50' : 'text-textSecondary hover:bg-gray-50'
            }`}
          >
            Completed
          </button>
          <button
            onClick={() => setActiveTab('archived')}
            className={`px-4 py-2 text-sm font-medium rounded-lg ${
              activeTab === 'archived' ? 'text-primary bg-indigo-50' : 'text-textSecondary hover:bg-gray-50'
            }`}
          >
            Archived
          </button>
          <div className="h-4 w-px bg-borderColor"></div>
          <div className="text-sm text-textMuted">24 total reports</div>
        </div>
      </section>

      <section className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faClipboardCheck} className="text-primary text-xl" />
            </div>
            <span className="text-xs font-medium text-successGreen bg-green-50 px-2 py-1 rounded-full">
              +3 this month
            </span>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">24</div>
          <div className="text-sm text-textSecondary">Total Reports</div>
          <div className="mt-4 text-xs text-textMuted">15 completed, 9 in progress</div>
        </div>

        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-amber-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faHourglassHalf} className="text-warningAmber text-xl" />
            </div>
            <span className="text-xs font-medium text-warningAmber bg-amber-50 px-2 py-1 rounded-full">Active</span>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">5</div>
          <div className="text-sm text-textSecondary">In Progress</div>
          <div className="mt-4 text-xs text-textMuted">2 due this week</div>
        </div>

        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faCheckCircle} className="text-successGreen text-xl" />
            </div>
            <span className="text-xs font-medium text-successGreen bg-green-50 px-2 py-1 rounded-full">100%</span>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">15</div>
          <div className="text-sm text-textSecondary">Completed</div>
          <div className="mt-4 text-xs text-textMuted">All findings addressed</div>
        </div>

        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-purple-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faBrain} className="text-purple-600 text-xl" />
            </div>
            <span className="text-xs font-medium text-purple-600 bg-purple-50 px-2 py-1 rounded-full">
              AI Powered
            </span>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">847</div>
          <div className="text-sm text-textSecondary">AI Insights Generated</div>
          <div className="mt-4 text-xs text-textMuted">Across all reports</div>
        </div>
      </section>

      <section className="bg-surface rounded-xl border border-borderColor shadow-sm mb-8">
        <div className="p-6 border-b border-borderColor">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-textPrimary mb-1">Audit Reports</h2>
              <p className="text-sm text-textSecondary">Manage and track all audit reports</p>
            </div>
            <div className="flex items-center space-x-3">
              <div className="relative">
                <FontAwesomeIcon
                  icon={faSearch}
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 text-textMuted"
                />
                <input
                  type="text"
                  placeholder="Search reports..."
                  className="h-10 pl-10 pr-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>
              <button className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">
                <FontAwesomeIcon icon={faSortAmountDown} className="mr-2" />
                Sort
              </button>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-borderColor bg-gray-50">
                <th className="text-left py-4 px-6 text-xs font-semibold text-textMuted uppercase tracking-wide">
                  <input type="checkbox" className="rounded border-borderColor" />
                </th>
                <th className="text-left py-4 px-6 text-xs font-semibold text-textMuted uppercase tracking-wide">
                  Report Name
                </th>
                <th className="text-left py-4 px-6 text-xs font-semibold text-textMuted uppercase tracking-wide">
                  Type
                </th>
                <th className="text-left py-4 px-6 text-xs font-semibold text-textMuted uppercase tracking-wide">
                  Period
                </th>
                <th className="text-left py-4 px-6 text-xs font-semibold text-textMuted uppercase tracking-wide">
                  Entity
                </th>
                <th className="text-center py-4 px-6 text-xs font-semibold text-textMuted uppercase tracking-wide">
                  Status
                </th>
                <th className="text-left py-4 px-6 text-xs font-semibold text-textMuted uppercase tracking-wide">
                  Created
                </th>
                <th className="text-left py-4 px-6 text-xs font-semibold text-textMuted uppercase tracking-wide">
                  Created By
                </th>
                <th className="text-right py-4 px-6 text-xs font-semibold text-textMuted uppercase tracking-wide">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id} className="border-b border-borderColor hover:bg-gray-50">
                  <td className="py-4 px-6">
                    <input type="checkbox" className="rounded border-borderColor" />
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center space-x-3">
                      <div className={`w-10 h-10 ${report.iconBg} rounded-lg flex items-center justify-center`}>
                        <FontAwesomeIcon icon={faFileAlt} className={report.iconColor} />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-textPrimary">{report.name}</div>
                        <div className="text-xs text-textSecondary">{report.description}</div>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <Badge variant={report.typeVariant} icon={report.typeIcon}>
                      {report.type}
                    </Badge>
                  </td>
                  <td className="py-4 px-6">
                    <div className="text-sm text-textPrimary">{report.period}</div>
                    <div className="text-xs text-textSecondary">{report.periodDetail}</div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="text-sm text-textPrimary">{report.entity}</div>
                    <div className="text-xs text-textSecondary">{report.entityDetail}</div>
                  </td>
                  <td className="py-4 px-6 text-center">
                    {report.status === 'Completed' ? (
                      <Badge variant="success" icon={faCheckCircle}>
                        {report.status}
                      </Badge>
                    ) : (
                      <Badge variant="warning" icon={faHourglassHalf}>
                        {report.status}
                      </Badge>
                    )}
                  </td>
                  <td className="py-4 px-6">
                    <div className="text-sm text-textPrimary">{report.created}</div>
                    <div className="text-xs text-textSecondary">{report.createdDetail}</div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center space-x-2">
                      <img src={report.createdByAvatar} alt="User" className="w-8 h-8 rounded-full" />
                      <div className="text-sm text-textPrimary">{report.createdBy}</div>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        className="w-8 h-8 flex items-center justify-center text-textSecondary hover:text-primary hover:bg-indigo-50 rounded-lg"
                        title="View"
                      >
                        <FontAwesomeIcon icon={faEye} />
                      </button>
                      {report.status === 'In Progress' && (
                        <button
                          className="w-8 h-8 flex items-center justify-center text-textSecondary hover:text-warningAmber hover:bg-amber-50 rounded-lg"
                          title="Edit"
                        >
                          <FontAwesomeIcon icon={faEdit} />
                        </button>
                      )}
                      <button
                        className="w-8 h-8 flex items-center justify-center text-textSecondary hover:text-infoBlue hover:bg-blue-50 rounded-lg"
                        title="Download"
                      >
                        <FontAwesomeIcon icon={faDownload} />
                      </button>
                      <button
                        className="w-8 h-8 flex items-center justify-center text-textSecondary hover:text-successGreen hover:bg-green-50 rounded-lg"
                        title="Share"
                      >
                        <FontAwesomeIcon icon={faShareAlt} />
                      </button>
                      <button className="w-8 h-8 flex items-center justify-center text-textSecondary hover:text-textPrimary hover:bg-gray-100 rounded-lg">
                        <FontAwesomeIcon icon={faEllipsisV} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}

'use client'

import { useState } from 'react'
import Badge from '@/components/ui/Badge'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faInfo,
  faHistory,
  faQuestionCircle,
  faChevronDown,
  faCheckCircle,
  faFileAlt,
  faReceipt,
  faChartBar,
  faShieldAlt,
  faDownload,
  faEye,
  faTimes,
  faPlus,
  faSpinner,
} from '@fortawesome/free-solid-svg-icons'

export default function EvidencePackPage() {
  const [step, setStep] = useState(1)
  const [selectedReport, setSelectedReport] = useState('Q4 2024 Compliance Audit - AR-2024-Q4-001')
  const [packName, setPackName] = useState('Q4_2024_Compliance_Evidence_Pack')
  const [isGenerating, setIsGenerating] = useState(false)

  const evidenceItems = [
    {
      id: 1,
      type: 'Expense Reports',
      count: 156,
      size: '45.2 MB',
      status: 'ready',
      icon: faReceipt,
    },
    {
      id: 2,
      type: 'Receipt Images',
      count: 234,
      size: '128.7 MB',
      status: 'ready',
      icon: faFileAlt,
    },
    {
      id: 3,
      type: 'Audit Trail Logs',
      count: 1,
      size: '2.1 MB',
      status: 'ready',
      icon: faChartBar,
    },
    {
      id: 4,
      type: 'Compliance Certificates',
      count: 3,
      size: '856 KB',
      status: 'ready',
      icon: faShieldAlt,
    },
  ]

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">Evidence Pack Generator</h1>
            <p className="text-textSecondary">
              Compile comprehensive audit evidence packages for external review and compliance
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
              <FontAwesomeIcon icon={faHistory} />
              <span>View History</span>
            </button>
            <button className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
              <FontAwesomeIcon icon={faQuestionCircle} />
              <span>Help</span>
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-4 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
            <FontAwesomeIcon icon={faInfo} className="text-white" />
          </div>
          <div className="flex-1">
            <p className="text-sm text-textPrimary font-medium mb-1">Secure Evidence Compilation</p>
            <p className="text-sm text-textSecondary">
              All generated packs include encrypted documents, complete audit trails, and tamper-proof metadata for
              regulatory compliance.
            </p>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <section className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-textPrimary mb-1">Pack Configuration</h2>
                <p className="text-sm text-textSecondary">Configure evidence pack parameters and content selection</p>
              </div>
              <span className="text-xs font-medium text-infoBlue bg-blue-50 px-3 py-1 rounded-full">
                Step {step} of 3
              </span>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-textPrimary mb-2">
                  Audit Report <span className="text-errorRed">*</span>
                </label>
                <div className="relative">
                  <select
                    value={selectedReport}
                    onChange={(e) => setSelectedReport(e.target.value)}
                    className="w-full h-10 px-3 pr-10 border border-borderColor rounded-lg text-sm text-textPrimary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent appearance-none"
                  >
                    <option>Select audit report to compile evidence for</option>
                    <option>Q4 2024 Compliance Audit - AR-2024-Q4-001</option>
                    <option>Travel Expense Review - AR-2024-12-015</option>
                    <option>Department Budget Audit - AR-2024-11-028</option>
                    <option>URSSAF Compliance Check - AR-2024-10-042</option>
                    <option>VAT Documentation Audit - AR-2024-09-033</option>
                  </select>
                  <FontAwesomeIcon
                    icon={faChevronDown}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-textMuted text-xs pointer-events-none"
                  />
                </div>
                <p className="text-xs text-textMuted mt-1">
                  Select the audit report for which you want to generate an evidence pack
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-textPrimary mb-2">
                  Pack Name <span className="text-errorRed">*</span>
                </label>
                <input
                  type="text"
                  value={packName}
                  onChange={(e) => setPackName(e.target.value)}
                  className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm text-textPrimary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
                <p className="text-xs text-textMuted mt-1">This name will be used for the ZIP file and folder structure</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-textPrimary mb-2">Evidence Types to Include</label>
                <div className="space-y-3">
                  {evidenceItems.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between p-4 border border-borderColor rounded-lg hover:border-primary transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-indigo-50 rounded-lg flex items-center justify-center">
                          <FontAwesomeIcon icon={item.icon} className="text-primary" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-textPrimary">{item.type}</div>
                          <div className="text-xs text-textSecondary">
                            {item.count} items • {item.size}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <Badge variant={item.status === 'ready' ? 'success' : 'warning'}>
                          {item.status === 'ready' ? 'Ready' : 'Processing'}
                        </Badge>
                        <input type="checkbox" defaultChecked className="w-4 h-4 text-primary border-borderColor rounded focus:ring-primary" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-borderColor">
                <button
                  onClick={() => setStep(Math.max(1, step - 1))}
                  disabled={step === 1}
                  className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  onClick={() => {
                    if (step < 3) setStep(step + 1)
                    else {
                      setIsGenerating(true)
                      setTimeout(() => setIsGenerating(false), 3000)
                    }
                  }}
                  className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium"
                >
                  {step < 3 ? 'Next Step' : isGenerating ? 'Generating...' : 'Generate Pack'}
                </button>
              </div>
            </div>
          </section>
        </div>

        <div className="col-span-1">
          <section className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm sticky top-24">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-textPrimary mb-1">Pack Summary</h2>
              <p className="text-sm text-textSecondary">Overview of evidence pack contents</p>
            </div>

            <div className="space-y-4 mb-6">
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-xs text-textMuted mb-1">Total Items</div>
                <div className="text-2xl font-bold text-textPrimary">394</div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-xs text-textMuted mb-1">Total Size</div>
                <div className="text-2xl font-bold text-textPrimary">176.8 MB</div>
              </div>
            </div>

            <div className="space-y-3 mb-6">
              <div className="flex items-center justify-between text-sm">
                <span className="text-textSecondary">Expense Reports</span>
                <span className="font-medium text-textPrimary">156</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-textSecondary">Receipt Images</span>
                <span className="font-medium text-textPrimary">234</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-textSecondary">Audit Trails</span>
                <span className="font-medium text-textPrimary">1</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-textSecondary">Certificates</span>
                <span className="font-medium text-textPrimary">3</span>
              </div>
            </div>

            <div className="pt-6 border-t border-borderColor">
              <div className="flex items-center space-x-2 mb-4">
                <FontAwesomeIcon icon={faCheckCircle} className="text-successGreen" />
                <span className="text-sm font-medium text-textPrimary">All items verified</span>
              </div>
              <p className="text-xs text-textSecondary mb-4">
                All selected evidence items have been verified and are ready for compilation.
              </p>
              <button className="w-full h-10 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center justify-center space-x-2">
                <FontAwesomeIcon icon={faDownload} />
                <span>Download Preview</span>
              </button>
            </div>
          </section>
        </div>
      </div>
    </>
  )
}

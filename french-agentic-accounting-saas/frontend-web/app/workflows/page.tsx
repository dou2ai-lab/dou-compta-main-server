'use client'

import { useState } from 'react'
import Badge from '@/components/ui/Badge'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faProjectDiagram,
  faPlus,
  faPlay,
  faPause,
  faEdit,
  faTrash,
  faCopy,
  faCheckCircle,
  faClock,
  faUsers,
} from '@fortawesome/free-solid-svg-icons'

export default function WorkflowsPage() {
  const workflows = [
    {
      id: 1,
      name: 'Standard Expense Approval',
      status: 'Active',
      description: 'Default workflow for expense approvals under €500',
      steps: 3,
      approvers: 2,
      lastModified: 'Jan 10, 2025',
    },
    {
      id: 2,
      name: 'High Value Approval',
      status: 'Active',
      description: 'Multi-level approval for expenses over €500',
      steps: 5,
      approvers: 3,
      lastModified: 'Jan 8, 2025',
    },
    {
      id: 3,
      name: 'Executive Approval',
      status: 'Draft',
      description: 'Workflow for executive-level expense approvals',
      steps: 2,
      approvers: 1,
      lastModified: 'Jan 5, 2025',
    },
  ]

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">Approval Workflow Configuration</h1>
            <p className="text-textSecondary">Design and manage expense approval workflows</p>
          </div>
          <div className="flex items-center space-x-3">
            <button className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2">
              <FontAwesomeIcon icon={faPlus} />
              <span>Create Workflow</span>
            </button>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-3 gap-6 mb-8">
        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faProjectDiagram} className="text-primary text-xl" />
            </div>
            <Badge variant="success">Active</Badge>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">3</div>
          <div className="text-sm text-textSecondary">Active Workflows</div>
        </div>

        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-amber-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faClock} className="text-warningAmber text-xl" />
            </div>
            <Badge variant="warning">Draft</Badge>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">1</div>
          <div className="text-sm text-textSecondary">Draft Workflows</div>
        </div>

        <div className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
              <FontAwesomeIcon icon={faUsers} className="text-successGreen text-xl" />
            </div>
          </div>
          <div className="text-2xl font-bold text-textPrimary mb-1">6</div>
          <div className="text-sm text-textSecondary">Total Approvers</div>
        </div>
      </section>

      <section className="bg-surface rounded-xl border border-borderColor shadow-sm">
        <div className="p-6 border-b border-borderColor">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-textPrimary mb-1">Approval Workflows</h2>
              <p className="text-sm text-textSecondary">Configure multi-step approval processes</p>
            </div>
          </div>
        </div>

        <div className="divide-y divide-borderColor">
          {workflows.map((workflow) => (
            <div key={workflow.id} className="p-6 hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-textPrimary">{workflow.name}</h3>
                    {workflow.status === 'Active' ? (
                      <Badge variant="success" icon={faCheckCircle}>
                        {workflow.status}
                      </Badge>
                    ) : (
                      <Badge variant="warning" icon={faClock}>
                        {workflow.status}
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-textSecondary mb-4">{workflow.description}</p>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <div className="text-xs text-textMuted mb-1">Steps</div>
                      <div className="text-sm font-medium text-textPrimary">{workflow.steps}</div>
                    </div>
                    <div>
                      <div className="text-xs text-textMuted mb-1">Approvers</div>
                      <div className="text-sm font-medium text-textPrimary">{workflow.approvers}</div>
                    </div>
                    <div>
                      <div className="text-xs text-textMuted mb-1">Last Modified</div>
                      <div className="text-sm font-medium text-textPrimary">{workflow.lastModified}</div>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2 ml-6">
                  {workflow.status === 'Active' ? (
                    <button className="w-9 h-9 flex items-center justify-center text-textSecondary hover:text-warningAmber hover:bg-amber-50 rounded-lg">
                      <FontAwesomeIcon icon={faPause} />
                    </button>
                  ) : (
                    <button className="w-9 h-9 flex items-center justify-center text-textSecondary hover:text-successGreen hover:bg-green-50 rounded-lg">
                      <FontAwesomeIcon icon={faPlay} />
                    </button>
                  )}
                  <button className="w-9 h-9 flex items-center justify-center text-textSecondary hover:text-primary hover:bg-indigo-50 rounded-lg">
                    <FontAwesomeIcon icon={faEdit} />
                  </button>
                  <button className="w-9 h-9 flex items-center justify-center text-textSecondary hover:text-infoBlue hover:bg-blue-50 rounded-lg">
                    <FontAwesomeIcon icon={faCopy} />
                  </button>
                  <button className="w-9 h-9 flex items-center justify-center text-textSecondary hover:text-errorRed hover:bg-red-50 rounded-lg">
                    <FontAwesomeIcon icon={faTrash} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
  )
}

'use client'

import { useState } from 'react'
import Badge from '@/components/ui/Badge'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faPlug, faPlus, faBook, faCheckCircle, faCircle, faCog, faFlask, faEllipsisV, faFileAlt, faPlay, faTimes } from '@fortawesome/free-solid-svg-icons'
import { faMicrosoft, faGoogle } from '@fortawesome/free-brands-svg-icons'

const CATEGORY_TABS = [
  { key: 'all', label: 'All Integrations' },
  { key: 'auth', label: 'Authentication', icon: 'fa-user-shield' },
  { key: 'erp', label: 'ERP Systems', icon: 'fa-building' },
  { key: 'hr', label: 'HR Systems', icon: 'fa-users' },
  { key: 'banking', label: 'Banking', icon: 'fa-university' },
  { key: 'cards', label: 'Corporate Cards', icon: 'fa-credit-card' },
  { key: 'storage', label: 'Storage', icon: 'fa-cloud' },
]

const AUTH_INTEGRATIONS = [
  { id: 'azure', name: 'Azure AD', desc: 'Microsoft Azure Active Directory', icon: faMicrosoft, iconBg: 'bg-blue-50', iconColor: 'text-infoBlue', status: 'Connected', lastSync: '2 minutes ago', usersSynced: 247 },
  { id: 'google', name: 'Google Workspace', desc: 'Google Cloud Identity', icon: faGoogle, iconBg: 'bg-red-50', iconColor: 'text-red-500', status: 'Connected', lastSync: '15 minutes ago', usersSynced: 247 },
  { id: 'okta', name: 'Okta', desc: 'Identity & Access Management', icon: null, iconBg: 'bg-blue-50', iconColor: 'text-infoBlue', status: 'Not Connected', setupStatus: 'Not Started', estTime: '15 minutes', difficulty: 'Easy' },
]

const ERP_INTEGRATIONS = [
  { id: 'sap', name: 'SAP ERP', desc: 'SAP S/4HANA Integration', status: 'Connected', lastSync: '5 minutes ago', glMapped: 156, statusLabel: 'Syncing' },
  { id: 'oracle', name: 'Oracle ERP', desc: 'Oracle Cloud ERP', status: 'Pending', progress: 50, step: 'Step 3 of 6', startedBy: 'Jean Dupont' },
  { id: 'netsuite', name: 'NetSuite', desc: 'Oracle NetSuite ERP', status: 'Not Connected', setupStatus: 'Not Started', estTime: '30 minutes', difficulty: 'Medium' },
]

export default function IntegrationsPage() {
  const [category, setCategory] = useState('all')

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">Integrations Hub</h1>
            <p className="text-textSecondary">Connect and manage external system integrations</p>
          </div>
          <div className="flex items-center space-x-3">
            <button className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
              <FontAwesomeIcon icon={faBook} />
              <span>Documentation</span>
            </button>
            <button className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2">
              <FontAwesomeIcon icon={faPlus} />
              <span>Add Integration</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4">
          <div className="bg-surface border border-borderColor rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">Active</span>
              <div className="w-2 h-2 bg-successGreen rounded-full" />
            </div>
            <div className="text-2xl font-bold text-textPrimary">12</div>
            <div className="text-xs text-textMuted mt-1">Connected integrations</div>
          </div>
          <div className="bg-surface border border-borderColor rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">Pending</span>
              <div className="w-2 h-2 bg-warningAmber rounded-full pulse-dot" />
            </div>
            <div className="text-2xl font-bold text-textPrimary">3</div>
            <div className="text-xs text-textMuted mt-1">Setup in progress</div>
          </div>
          <div className="bg-surface border border-borderColor rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">Errors</span>
              <div className="w-2 h-2 bg-errorRed rounded-full" />
            </div>
            <div className="text-2xl font-bold text-textPrimary">1</div>
            <div className="text-xs text-textMuted mt-1">Requires attention</div>
          </div>
          <div className="bg-surface border border-borderColor rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">Available</span>
              <FontAwesomeIcon icon={faPlus} className="text-textMuted" />
            </div>
            <div className="text-2xl font-bold text-textPrimary">24</div>
            <div className="text-xs text-textMuted mt-1">Ready to connect</div>
          </div>
        </div>
      </section>

      <section className="mb-8">
        <div className="flex items-center space-x-2 overflow-x-auto pb-2">
          {CATEGORY_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setCategory(tab.key)}
              className={`px-4 py-2 whitespace-nowrap rounded-lg text-sm font-medium ${
                category === tab.key ? 'bg-primary text-white' : 'bg-surface border border-borderColor text-textSecondary hover:bg-gray-50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </section>

      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-textPrimary">Authentication & SSO</h2>
          <button className="text-sm text-primary hover:text-primaryHover font-medium">View All</button>
        </div>
        <div className="grid grid-cols-3 gap-6">
          {AUTH_INTEGRATIONS.map((int) => (
            <div key={int.id} className="bg-surface border border-borderColor rounded-xl p-6 hover:border-primary transition-colors cursor-pointer">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <div className={`w-14 h-14 ${int.iconBg} rounded-xl flex items-center justify-center`}>
                    {int.icon ? <FontAwesomeIcon icon={int.icon} className={`text-2xl ${int.iconColor}`} /> : <FontAwesomeIcon icon={faPlug} className={`text-2xl ${int.iconColor}`} />}
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-textPrimary">{int.name}</h3>
                    <p className="text-xs text-textSecondary">{int.desc}</p>
                  </div>
                </div>
                <span className={`inline-flex items-center text-xs font-medium px-2 py-1 rounded-full ${int.status === 'Connected' ? 'text-successGreen bg-green-50' : 'text-textMuted bg-gray-100'}`}>
                  {int.status === 'Connected' ? <FontAwesomeIcon icon={faCheckCircle} className="mr-1" /> : <FontAwesomeIcon icon={faCircle} className="mr-1" />}
                  {int.status}
                </span>
              </div>
              <div className="space-y-2 mb-4">
                {'lastSync' in int && (
                  <>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-textSecondary">Last Sync</span>
                      <span className="text-textPrimary font-medium">{int.lastSync}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-textSecondary">Users Synced</span>
                      <span className="text-textPrimary font-medium">{int.usersSynced}</span>
                    </div>
                  </>
                )}
                {'setupStatus' in int && (
                  <>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-textSecondary">Setup Status</span>
                      <span className="text-textPrimary font-medium">{int.setupStatus}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-textSecondary">Estimated Time</span>
                      <span className="text-textPrimary font-medium">{int.estTime}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-textSecondary">Difficulty</span>
                      <span className="text-textPrimary font-medium">{int.difficulty}</span>
                    </div>
                  </>
                )}
                <div className="flex items-center justify-between text-sm">
                  <span className="text-textSecondary">Status</span>
                  <div className="flex items-center space-x-1">
                    <div className={`w-2 h-2 rounded-full ${int.status === 'Connected' ? 'bg-successGreen' : 'bg-gray-300'}`} />
                    <span className="text-textPrimary font-medium">{int.status === 'Connected' ? 'Active' : int.status}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2 pt-4 border-t border-borderColor">
                {int.status === 'Connected' ? (
                  <>
                    <button className="flex-1 h-9 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">
                      <FontAwesomeIcon icon={faCog} className="mr-1" />
                      Configure
                    </button>
                    <button className="flex-1 h-9 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">
                      <FontAwesomeIcon icon={faFlask} className="mr-1" />
                      Test
                    </button>
                  </>
                ) : (
                  <button className="flex-1 h-9 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium">
                    <FontAwesomeIcon icon={faPlug} className="mr-1" />
                    Connect
                  </button>
                )}
                <button className="h-9 w-9 border border-borderColor rounded-lg text-sm text-textSecondary hover:bg-gray-50 flex items-center justify-center">
                  <FontAwesomeIcon icon={faEllipsisV} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-textPrimary">ERP Systems</h2>
          <button className="text-sm text-primary hover:text-primaryHover font-medium">View All</button>
        </div>
        <div className="grid grid-cols-3 gap-6">
          {ERP_INTEGRATIONS.map((int) => (
            <div key={int.id} className="bg-surface border border-borderColor rounded-xl p-6 hover:border-primary transition-colors cursor-pointer">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <div className="w-14 h-14 bg-blue-50 rounded-xl flex items-center justify-center">
                    <FontAwesomeIcon icon={faPlug} className="text-2xl text-infoBlue" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-textPrimary">{int.name}</h3>
                    <p className="text-xs text-textSecondary">{int.desc}</p>
                  </div>
                </div>
                <span
                  className={`inline-flex items-center text-xs font-medium px-2 py-1 rounded-full ${
                    int.status === 'Connected' ? 'text-successGreen bg-green-50' : int.status === 'Pending' ? 'text-warningAmber bg-amber-50' : 'text-textMuted bg-gray-100'
                  }`}
                >
                  {int.status === 'Connected' && <FontAwesomeIcon icon={faCheckCircle} className="mr-1" />}
                  {int.status === 'Pending' && <FontAwesomeIcon icon={faCircle} className="mr-1" />}
                  {int.status}
                </span>
              </div>
              <div className="space-y-2 mb-4">
                {'lastSync' in int && (
                  <>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-textSecondary">Last Sync</span>
                      <span className="text-textPrimary font-medium">{int.lastSync}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-textSecondary">GL Codes Mapped</span>
                      <span className="text-textPrimary font-medium">{int.glMapped}</span>
                    </div>
                  </>
                )}
                {'progress' in int && (
                  <>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-textSecondary">Setup Progress</span>
                      <span className="text-textPrimary font-medium">{int.step}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-textSecondary">Started By</span>
                      <span className="text-textPrimary font-medium">{int.startedBy}</span>
                    </div>
                    <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-warningAmber" style={{ width: `${int.progress}%` }} />
                    </div>
                  </>
                )}
                {'setupStatus' in int && 'estTime' in int && (
                  <>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-textSecondary">Setup Status</span>
                      <span className="text-textPrimary font-medium">{int.setupStatus}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-textSecondary">Estimated Time</span>
                      <span className="text-textPrimary font-medium">{int.estTime}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-textSecondary">Difficulty</span>
                      <span className="text-textPrimary font-medium">{int.difficulty}</span>
                    </div>
                  </>
                )}
                <div className="flex items-center justify-between text-sm">
                  <span className="text-textSecondary">Status</span>
                  <div className="flex items-center space-x-1">
                    <div
                      className={`w-2 h-2 rounded-full ${int.status === 'Connected' ? 'bg-successGreen' : int.status === 'Pending' ? 'bg-warningAmber pulse-dot' : 'bg-gray-300'}`}
                    />
                    <span className="text-textPrimary font-medium">{'statusLabel' in int ? int.statusLabel : int.status}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2 pt-4 border-t border-borderColor">
                {int.status === 'Connected' && (
                  <>
                    <button className="flex-1 h-9 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">
                      <FontAwesomeIcon icon={faCog} className="mr-1" />
                      Configure
                    </button>
                    <button className="flex-1 h-9 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">
                      <FontAwesomeIcon icon={faFileAlt} className="mr-1" />
                      Logs
                    </button>
                  </>
                )}
                {int.status === 'Pending' && (
                  <>
                    <button className="flex-1 h-9 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium">
                      <FontAwesomeIcon icon={faPlay} className="mr-1" />
                      Continue Setup
                    </button>
                    <button className="h-9 w-9 border border-borderColor rounded-lg text-sm text-textSecondary hover:bg-gray-50 flex items-center justify-center">
                      <FontAwesomeIcon icon={faTimes} />
                    </button>
                  </>
                )}
                {int.status === 'Not Connected' && (
                  <>
                    <button className="flex-1 h-9 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium">
                      <FontAwesomeIcon icon={faPlug} className="mr-1" />
                      Connect
                    </button>
                    <button className="h-9 w-9 border border-borderColor rounded-lg text-sm text-textSecondary hover:bg-gray-50 flex items-center justify-center">
                      <FontAwesomeIcon icon={faEllipsisV} />
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
  )
}

'use client'

import { useState, useEffect, useCallback } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faPlug,
  faPlus,
  faBook,
  faCheckCircle,
  faCircle,
  faCog,
  faFlask,
  faEllipsisV,
  faFileAlt,
  faPlay,
  faTimes,
  faUserShield,
  faBuilding,
  faUsers,
  faUniversity,
  faCreditCard,
  faCloud,
  faShieldAlt,
  faDatabase,
  faChartLine,
  faCube,
  faBriefcase,
  faUserTie,
  faExchangeAlt,
  faDownload,
  faSync,
  faChartBar,
  faExclamationCircle,
  faWrench,
  faCheck,
  faExclamationTriangle,
  faQuestionCircle,
  faVideo,
  faHeadset,
  faSpinner,
  faKey,
  faArrowRight,
  faArrowLeft,
  faClock,
  faInfoCircle,
} from '@fortawesome/free-solid-svg-icons'
import { faMicrosoft, faGoogle, faStripe, faAws, faCcVisa, faCcMastercard, faCcAmex } from '@fortawesome/free-brands-svg-icons'
import { useLanguage } from '@/contexts/LanguageContext'

type CardStatus = 'connected' | 'pending' | 'error' | 'not_connected'
type ModalType = 'configure' | 'test' | 'connect' | 'logs' | 'fix' | 'usage' | null

interface Integration {
  id: string
  name: string
  desc: string
  icon: any
  iconBg: string
  iconColor: string
  category: string
  status: CardStatus
  lastSync: string
  details: { label: string; value: string }[]
  progress?: number
  statusLabel?: string
}

interface ToastState {
  message: string
  type: 'success' | 'error' | 'info'
}

interface ModalState {
  type: ModalType
  integrationId: string
}

const INITIAL_INTEGRATIONS: Integration[] = [
  { id: 'azure-ad', name: 'Azure AD', desc: 'Microsoft Azure Active Directory', icon: faMicrosoft, iconBg: 'bg-blue-50', iconColor: 'text-infoBlue', category: 'auth', status: 'connected', lastSync: '2 minutes ago', details: [{ label: 'Last Sync', value: '2 minutes ago' }, { label: 'Users Synced', value: '247' }] },
  { id: 'google-workspace', name: 'Google Workspace', desc: 'Google Cloud Identity', icon: faGoogle, iconBg: 'bg-red-50', iconColor: 'text-red-500', category: 'auth', status: 'connected', lastSync: '15 minutes ago', details: [{ label: 'Last Sync', value: '15 minutes ago' }, { label: 'Users Synced', value: '247' }] },
  { id: 'okta', name: 'Okta', desc: 'Identity & Access Management', icon: faShieldAlt, iconBg: 'bg-blue-50', iconColor: 'text-infoBlue', category: 'auth', status: 'not_connected', lastSync: 'Never', details: [{ label: 'Setup Status', value: 'Not Started' }, { label: 'Estimated Time', value: '15 minutes' }, { label: 'Difficulty', value: 'Easy' }] },
  { id: 'sap-erp', name: 'SAP ERP', desc: 'SAP S/4HANA Integration', icon: faBuilding, iconBg: 'bg-blue-50', iconColor: 'text-infoBlue', category: 'erp', status: 'connected', lastSync: '5 minutes ago', statusLabel: 'Syncing', details: [{ label: 'Last Sync', value: '5 minutes ago' }, { label: 'GL Codes Mapped', value: '156' }] },
  { id: 'oracle-erp', name: 'Oracle ERP', desc: 'Oracle Cloud ERP', icon: faDatabase, iconBg: 'bg-red-50', iconColor: 'text-red-600', category: 'erp', status: 'pending', lastSync: 'Never', details: [{ label: 'Setup Progress', value: 'Step 3 of 6' }, { label: 'Started By', value: 'Jean Dupont' }], progress: 50 },
  { id: 'netsuite', name: 'NetSuite', desc: 'Oracle NetSuite ERP', icon: faChartLine, iconBg: 'bg-orange-50', iconColor: 'text-orange-600', category: 'erp', status: 'not_connected', lastSync: 'Never', details: [{ label: 'Setup Status', value: 'Not Started' }, { label: 'Estimated Time', value: '30 minutes' }, { label: 'Difficulty', value: 'Medium' }] },
  { id: 'odoo', name: 'Odoo', desc: 'Open Source ERP', icon: faCube, iconBg: 'bg-purple-50', iconColor: 'text-purple-600', category: 'erp', status: 'connected', lastSync: '1 hour ago', details: [{ label: 'Last Sync', value: '1 hour ago' }, { label: 'Expenses Synced', value: '1,247' }] },
  { id: 'workday', name: 'Workday', desc: 'HR & Finance Management', icon: faBriefcase, iconBg: 'bg-blue-50', iconColor: 'text-infoBlue', category: 'hr', status: 'connected', lastSync: '30 minutes ago', details: [{ label: 'Last Sync', value: '30 minutes ago' }, { label: 'Employees Synced', value: '247' }] },
  { id: 'bamboohr', name: 'BambooHR', desc: 'HR Management Software', icon: faUsers, iconBg: 'bg-green-50', iconColor: 'text-successGreen', category: 'hr', status: 'not_connected', lastSync: 'Never', details: [{ label: 'Setup Status', value: 'Not Started' }, { label: 'Estimated Time', value: '20 minutes' }, { label: 'Difficulty', value: 'Easy' }] },
  { id: 'personio', name: 'Personio', desc: 'HR Platform for Europe', icon: faUserTie, iconBg: 'bg-purple-50', iconColor: 'text-purple-600', category: 'hr', status: 'connected', lastSync: '1 hour ago', details: [{ label: 'Last Sync', value: '1 hour ago' }, { label: 'Employees Synced', value: '247' }] },
  { id: 'sepa-export', name: 'SEPA Export', desc: 'European Payment Integration', icon: faUniversity, iconBg: 'bg-blue-50', iconColor: 'text-infoBlue', category: 'banking', status: 'connected', lastSync: 'Yesterday', details: [{ label: 'Last Export', value: 'Yesterday' }, { label: 'Total Exported', value: '\u20ac45,847' }] },
  { id: 'bank-feeds', name: 'Bank Feeds', desc: 'Real-time Transaction Sync', icon: faExchangeAlt, iconBg: 'bg-green-50', iconColor: 'text-successGreen', category: 'banking', status: 'pending', lastSync: 'Never', statusLabel: 'Setup Required', details: [{ label: 'Setup Progress', value: 'Step 2 of 6' }, { label: 'Bank Accounts', value: '0 connected' }], progress: 33 },
  { id: 'stripe', name: 'Stripe', desc: 'Payment Processing', icon: faStripe, iconBg: 'bg-purple-50', iconColor: 'text-purple-600', category: 'banking', status: 'not_connected', lastSync: 'Never', details: [{ label: 'Setup Status', value: 'Not Started' }, { label: 'Estimated Time', value: '10 minutes' }, { label: 'Difficulty', value: 'Easy' }] },
  { id: 'visa-corporate', name: 'Visa Corporate', desc: 'Corporate Card Integration', icon: faCcVisa, iconBg: 'bg-blue-50', iconColor: 'text-infoBlue', category: 'cards', status: 'connected', lastSync: '10 minutes ago', statusLabel: 'Syncing', details: [{ label: 'Last Sync', value: '10 minutes ago' }, { label: 'Cards Linked', value: '47' }] },
  { id: 'mastercard-business', name: 'Mastercard Business', desc: 'Business Card Integration', icon: faCcMastercard, iconBg: 'bg-red-50', iconColor: 'text-red-600', category: 'cards', status: 'connected', lastSync: '5 minutes ago', details: [{ label: 'Last Sync', value: '5 minutes ago' }, { label: 'Cards Linked', value: '32' }] },
  { id: 'american-express', name: 'American Express', desc: 'Corporate Card Program', icon: faCcAmex, iconBg: 'bg-blue-50', iconColor: 'text-infoBlue', category: 'cards', status: 'not_connected', lastSync: 'Never', details: [{ label: 'Setup Status', value: 'Not Started' }, { label: 'Estimated Time', value: '15 minutes' }, { label: 'Difficulty', value: 'Easy' }] },
  { id: 'aws-s3', name: 'AWS S3', desc: 'Amazon Web Services Storage', icon: faAws, iconBg: 'bg-orange-50', iconColor: 'text-orange-600', category: 'storage', status: 'connected', lastSync: 'Just now', details: [{ label: 'Storage Used', value: '124.5 GB' }, { label: 'Files Stored', value: '12,847' }] },
  { id: 'azure-blob', name: 'Azure Blob', desc: 'Microsoft Azure Storage', icon: faMicrosoft, iconBg: 'bg-blue-50', iconColor: 'text-infoBlue', category: 'storage', status: 'error', lastSync: '2 hours ago', details: [{ label: 'Last Attempt', value: '2 hours ago' }, { label: 'Error Code', value: 'AUTH_EXPIRED' }] },
  { id: 'google-cloud-storage', name: 'Google Cloud Storage', desc: 'GCS Bucket Integration', icon: faGoogle, iconBg: 'bg-red-50', iconColor: 'text-red-500', category: 'storage', status: 'not_connected', lastSync: 'Never', details: [{ label: 'Setup Status', value: 'Not Started' }, { label: 'Estimated Time', value: '10 minutes' }, { label: 'Difficulty', value: 'Medium' }] },
]

const CATEGORY_TABS = [
  { key: 'all', label: 'All Integrations' },
  { key: 'auth', label: 'Authentication', icon: faUserShield },
  { key: 'erp', label: 'ERP Systems', icon: faBuilding },
  { key: 'hr', label: 'HR Systems', icon: faUsers },
  { key: 'banking', label: 'Banking', icon: faUniversity },
  { key: 'cards', label: 'Corporate Cards', icon: faCreditCard },
  { key: 'storage', label: 'Storage', icon: faCloud },
]

const CATEGORY_TITLES: Record<string, string> = {
  auth: 'Authentication & SSO',
  erp: 'ERP Systems',
  hr: 'HR Systems',
  banking: 'Banking & Payment Systems',
  cards: 'Corporate Card Integrations',
  storage: 'Cloud Storage',
}

const SAMPLE_LOGS = [
  { time: '2026-03-16 10:32:15', level: 'INFO', message: 'Sync started - fetching remote data' },
  { time: '2026-03-16 10:32:18', level: 'INFO', message: 'Retrieved 247 records from remote API' },
  { time: '2026-03-16 10:32:20', level: 'WARN', message: '3 records skipped due to missing fields' },
  { time: '2026-03-16 10:32:22', level: 'INFO', message: 'Mapped 244 records to local schema' },
  { time: '2026-03-16 10:32:25', level: 'INFO', message: 'Sync completed successfully - 244 records updated' },
  { time: '2026-03-16 09:15:00', level: 'INFO', message: 'Scheduled sync triggered' },
  { time: '2026-03-16 09:15:04', level: 'INFO', message: 'Retrieved 245 records from remote API' },
  { time: '2026-03-16 09:15:08', level: 'INFO', message: 'Sync completed successfully - 245 records updated' },
]

const RECENT_ACTIVITY = [
  { icon: faCheck, iconBg: 'bg-green-50', iconColor: 'text-successGreen', title: 'SAP ERP sync completed successfully', time: '5 min ago', detail: '156 GL codes synchronized with 247 expense records', badge: 'Success', by: 'By System' },
  { icon: faSync, iconBg: 'bg-blue-50', iconColor: 'text-infoBlue', title: 'Azure AD user sync initiated', time: '15 min ago', detail: 'Syncing 247 users from Azure Active Directory', badge: 'In Progress', by: 'By Jean Dupont' },
  { icon: faCog, iconBg: 'bg-amber-50', iconColor: 'text-warningAmber', title: 'Visa Corporate card configuration updated', time: '1 hour ago', detail: 'Updated transaction sync frequency to real-time', badge: 'Configuration', by: 'By Jean Dupont' },
  { icon: faExclamationTriangle, iconBg: 'bg-red-50', iconColor: 'text-errorRed', title: 'Azure Blob storage authentication failed', time: '2 hours ago', detail: 'Access token expired - requires re-authentication', badge: 'Error', by: null, fix: true },
  { icon: faPlug, iconBg: 'bg-purple-50', iconColor: 'text-purple-600', title: 'New integration: Personio connected', time: 'Yesterday', detail: 'Successfully connected HR system with 247 employee records', badge: 'New Integration', by: 'By Jean Dupont' },
]

function IntegrationCard({
  name, desc, icon, iconBg, iconColor, status, statusLabel, statusBadge, rows, progress, buttons,
}: {
  name: string; desc: string; icon: any; iconBg: string; iconColor: string; status: CardStatus
  statusLabel?: string; statusBadge: React.ReactNode; rows: { label: string; value: React.ReactNode }[]
  progress?: number; buttons: React.ReactNode
}) {
  const defaultLabel = status === 'connected' ? 'Active' : status === 'pending' ? 'In Progress' : status === 'error' ? 'Needs Attention' : 'Not Started'
  return (
    <div className="bg-surface border border-borderColor rounded-xl p-6 hover:border-primary transition-colors cursor-pointer">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-4">
          <div className={`w-14 h-14 ${iconBg} rounded-xl flex items-center justify-center`}>
            <FontAwesomeIcon icon={icon} className={`text-2xl ${iconColor}`} />
          </div>
          <div>
            <h3 className="text-base font-semibold text-textPrimary">{name}</h3>
            <p className="text-xs text-textSecondary">{desc}</p>
          </div>
        </div>
        {statusBadge}
      </div>
      <div className="space-y-2 mb-4">
        {rows.map((r, i) => (
          <div key={i} className="flex items-center justify-between text-sm">
            <span className="text-textSecondary">{r.label}</span>
            <span className="text-textPrimary font-medium">{r.value}</span>
          </div>
        ))}
        <div className="flex items-center justify-between text-sm">
          <span className="text-textSecondary">Status</span>
          <div className="flex items-center space-x-1">
            <div className={`w-2 h-2 rounded-full ${status === 'connected' ? 'bg-successGreen' : status === 'pending' ? 'bg-warningAmber animate-pulse' : status === 'error' ? 'bg-errorRed' : 'bg-gray-300'}`} />
            <span className="text-textPrimary font-medium">{statusLabel ?? defaultLabel}</span>
          </div>
        </div>
      </div>
      {progress !== undefined && (
        <div className="mb-4">
          <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
            <div className="h-full bg-warningAmber rounded-full transition-all" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}
      <div className="flex items-center space-x-2 pt-4 border-t border-borderColor">{buttons}</div>
    </div>
  )
}

function StatusBadge({ status }: { status: CardStatus }) {
  if (status === 'connected') return <span className="inline-flex items-center text-xs font-medium text-successGreen bg-green-50 px-2 py-1 rounded-full"><FontAwesomeIcon icon={faCheckCircle} className="mr-1" />Connected</span>
  if (status === 'pending') return <span className="inline-flex items-center text-xs font-medium text-warningAmber bg-amber-50 px-2 py-1 rounded-full"><FontAwesomeIcon icon={faCircle} className="mr-1" />Pending</span>
  if (status === 'error') return <span className="inline-flex items-center text-xs font-medium text-errorRed bg-red-50 px-2 py-1 rounded-full"><FontAwesomeIcon icon={faExclamationCircle} className="mr-1" />Error</span>
  return <span className="inline-flex items-center text-xs font-medium text-textMuted bg-gray-100 px-2 py-1 rounded-full"><FontAwesomeIcon icon={faCircle} className="mr-1" />Not Connected</span>
}

export default function AdminIntegrationsPage() {
  const { t } = useLanguage()
  const [category, setCategory] = useState('all')
  const [integrations, setIntegrations] = useState<Integration[]>(INITIAL_INTEGRATIONS)
  const [toast, setToast] = useState<ToastState | null>(null)
  const [modal, setModal] = useState<ModalState | null>(null)
  const [syncingIds, setSyncingIds] = useState<Set<string>>(new Set())
  const [testingIds, setTestingIds] = useState<Set<string>>(new Set())
  const [wizardStep, setWizardStep] = useState(1)
  const [configForm, setConfigForm] = useState({ apiKey: '', syncFrequency: 'hourly', autoMap: true })

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 4000)
      return () => clearTimeout(timer)
    }
  }, [toast])

  const showToast = useCallback((message: string, type: ToastState['type']) => {
    setToast({ message, type })
  }, [])

  const getIntegration = (id: string) => integrations.find(i => i.id === id)

  const updateIntegration = useCallback((id: string, updates: Partial<Integration>) => {
    setIntegrations(prev => prev.map(i => i.id === id ? { ...i, ...updates } : i))
  }, [])

  const handleConfigure = (id: string) => {
    const integ = getIntegration(id)
    if (integ) {
      setConfigForm({ apiKey: integ.status === 'connected' ? 'sk-****-****-****-' + id.slice(0, 4) : '', syncFrequency: 'hourly', autoMap: true })
      setModal({ type: 'configure', integrationId: id })
    }
  }

  const handleSaveConfigure = () => {
    if (modal) {
      showToast(`Configuration saved for ${getIntegration(modal.integrationId)?.name}`, 'success')
      setModal(null)
    }
  }

  const handleTest = (id: string) => {
    setTestingIds(prev => new Set(prev).add(id))
    setTimeout(() => {
      setTestingIds(prev => { const n = new Set(prev); n.delete(id); return n })
      const success = Math.random() > 0.2
      if (success) {
        showToast(`Connection test passed for ${getIntegration(id)?.name}`, 'success')
      } else {
        showToast(`Connection test failed for ${getIntegration(id)?.name} - check credentials`, 'error')
      }
    }, 2000)
  }

  const handleConnect = (id: string) => {
    setWizardStep(1)
    setConfigForm({ apiKey: '', syncFrequency: 'hourly', autoMap: true })
    setModal({ type: 'connect', integrationId: id })
  }

  const handleFinishConnect = () => {
    if (modal) {
      updateIntegration(modal.integrationId, {
        status: 'connected',
        lastSync: 'Just now',
        details: [{ label: 'Last Sync', value: 'Just now' }, { label: 'Records', value: '0' }],
        progress: undefined,
      })
      showToast(`${getIntegration(modal.integrationId)?.name} connected successfully!`, 'success')
      setModal(null)
    }
  }

  const handleSync = (id: string) => {
    setSyncingIds(prev => new Set(prev).add(id))
    showToast(`Syncing ${getIntegration(id)?.name}...`, 'info')
    setTimeout(() => {
      setSyncingIds(prev => { const n = new Set(prev); n.delete(id); return n })
      updateIntegration(id, {
        lastSync: 'Just now',
        details: (getIntegration(id)?.details || []).map(d =>
          (d.label === 'Last Sync' || d.label === 'Last Export') ? { ...d, value: 'Just now' } : d
        ),
      })
      showToast(`${getIntegration(id)?.name} sync completed successfully`, 'success')
    }, 2500)
  }

  const handleContinueSetup = (id: string) => {
    const integ = getIntegration(id)
    const currentStep = integ?.details.find(d => d.label === 'Setup Progress')
    const step = currentStep ? parseInt(currentStep.value.match(/\d+/)?.[0] || '1') : 1
    setWizardStep(step)
    setConfigForm({ apiKey: '', syncFrequency: 'hourly', autoMap: true })
    setModal({ type: 'connect', integrationId: id })
  }

  const handleFixConnection = (id: string) => {
    setConfigForm({ apiKey: '', syncFrequency: 'hourly', autoMap: true })
    setModal({ type: 'fix', integrationId: id })
  }

  const handleSaveFix = () => {
    if (modal) {
      updateIntegration(modal.integrationId, {
        status: 'connected',
        lastSync: 'Just now',
        details: [{ label: 'Last Sync', value: 'Just now' }, { label: 'Status', value: 'Reconnected' }],
      })
      showToast(`${getIntegration(modal.integrationId)?.name} connection restored!`, 'success')
      setModal(null)
    }
  }

  const handleLogs = (id: string) => {
    setModal({ type: 'logs', integrationId: id })
  }

  const handleExport = (id: string) => {
    showToast(`Export download started for ${getIntegration(id)?.name}`, 'info')
  }

  const handleUsage = (id: string) => {
    setModal({ type: 'usage', integrationId: id })
  }

  const handleCancelSetup = (id: string) => {
    updateIntegration(id, { status: 'not_connected', progress: undefined, details: [{ label: 'Setup Status', value: 'Not Started' }, { label: 'Estimated Time', value: '30 minutes' }, { label: 'Difficulty', value: 'Medium' }] })
    showToast(`Setup cancelled for ${getIntegration(id)?.name}`, 'info')
  }

  // Build rows for a card, using live integration data
  const buildRows = (integ: Integration): { label: string; value: React.ReactNode }[] => {
    return integ.details.map(d => ({
      label: d.label,
      value: d.label === 'Error Code' && integ.status === 'error'
        ? <span className="text-errorRed font-medium">{d.value}</span>
        : d.value
    }))
  }

  // Build buttons for a card based on its original button layout
  const buildButtons = (integ: Integration): React.ReactNode => {
    const isSyncing = syncingIds.has(integ.id)
    const isTesting = testingIds.has(integ.id)
    const syncBtn = (label = 'Sync Now') => (
      <button type="button" onClick={() => handleSync(integ.id)} disabled={isSyncing}
        className="flex-1 h-9 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 disabled:opacity-50">
        <FontAwesomeIcon icon={isSyncing ? faSpinner : faSync} className={`mr-1 ${isSyncing ? 'animate-spin' : ''}`} />{isSyncing ? 'Syncing...' : label}
      </button>
    )
    const configBtn = (
      <button type="button" onClick={() => handleConfigure(integ.id)}
        className="flex-1 h-9 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">
        <FontAwesomeIcon icon={faCog} className="mr-1" />Configure
      </button>
    )
    const testBtn = (
      <button type="button" onClick={() => handleTest(integ.id)} disabled={isTesting}
        className="flex-1 h-9 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 disabled:opacity-50">
        <FontAwesomeIcon icon={isTesting ? faSpinner : faFlask} className={`mr-1 ${isTesting ? 'animate-spin' : ''}`} />{isTesting ? 'Testing...' : 'Test'}
      </button>
    )
    const menuBtn = (
      <button type="button" onClick={() => handleLogs(integ.id)}
        className="h-9 w-9 border border-borderColor rounded-lg text-textSecondary hover:bg-gray-50 flex items-center justify-center">
        <FontAwesomeIcon icon={faEllipsisV} />
      </button>
    )
    const connectBtn = (
      <button type="button" onClick={() => handleConnect(integ.id)}
        className="flex-1 h-9 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium">
        <FontAwesomeIcon icon={faPlug} className="mr-1" />Connect
      </button>
    )

    // Auth integrations
    if (integ.id === 'azure-ad' || integ.id === 'google-workspace') {
      return <>{configBtn}{testBtn}{menuBtn}</>
    }
    if (integ.id === 'okta' || integ.id === 'netsuite' || integ.id === 'bamboohr' || integ.id === 'stripe' || integ.id === 'american-express' || integ.id === 'google-cloud-storage') {
      if (integ.status === 'connected') {
        return <>{configBtn}{syncBtn('Sync')}{menuBtn}</>
      }
      return <>{connectBtn}{menuBtn}</>
    }
    // SAP ERP
    if (integ.id === 'sap-erp') {
      return <>{configBtn}<button type="button" onClick={() => handleLogs(integ.id)} className="flex-1 h-9 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50"><FontAwesomeIcon icon={faFileAlt} className="mr-1" />Logs</button>{menuBtn}</>
    }
    // Oracle ERP / Bank Feeds (pending with continue setup)
    if (integ.id === 'oracle-erp' || integ.id === 'bank-feeds') {
      if (integ.status === 'pending') {
        return <>
          <button type="button" onClick={() => handleContinueSetup(integ.id)} className="flex-1 h-9 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium"><FontAwesomeIcon icon={faPlay} className="mr-1" />Continue Setup</button>
          <button type="button" onClick={() => handleCancelSetup(integ.id)} className="h-9 w-9 border border-borderColor rounded-lg text-textSecondary hover:bg-gray-50 flex items-center justify-center"><FontAwesomeIcon icon={faTimes} /></button>
        </>
      }
      if (integ.status === 'connected') {
        return <>{configBtn}{syncBtn('Sync')}{menuBtn}</>
      }
      return <>{connectBtn}{menuBtn}</>
    }
    // Odoo, Workday, Personio, Visa Corporate, Mastercard Business
    if (['odoo', 'workday', 'personio', 'visa-corporate', 'mastercard-business'].includes(integ.id)) {
      const label = integ.id === 'odoo' ? 'Sync Now' : 'Sync'
      return <>{configBtn}{syncBtn(label)}{menuBtn}</>
    }
    // SEPA Export
    if (integ.id === 'sepa-export') {
      return <>{configBtn}<button type="button" onClick={() => handleExport(integ.id)} className="flex-1 h-9 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50"><FontAwesomeIcon icon={faDownload} className="mr-1" />Export</button>{menuBtn}</>
    }
    // AWS S3
    if (integ.id === 'aws-s3') {
      return <>{configBtn}<button type="button" onClick={() => handleUsage(integ.id)} className="flex-1 h-9 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50"><FontAwesomeIcon icon={faChartBar} className="mr-1" />Usage</button>{menuBtn}</>
    }
    // Azure Blob
    if (integ.id === 'azure-blob') {
      if (integ.status === 'error') {
        return <>
          <button type="button" onClick={() => handleFixConnection(integ.id)} className="flex-1 h-9 bg-errorRed hover:bg-red-600 text-white rounded-lg text-sm font-medium"><FontAwesomeIcon icon={faWrench} className="mr-1" />Fix Connection</button>
          <button type="button" onClick={() => handleLogs(integ.id)} className="h-9 w-9 border border-borderColor rounded-lg text-textSecondary hover:bg-gray-50 flex items-center justify-center"><FontAwesomeIcon icon={faFileAlt} /></button>
        </>
      }
      return <>{configBtn}{syncBtn('Sync')}{menuBtn}</>
    }
    // Fallback
    return <>{configBtn}{menuBtn}</>
  }

  const filteredCategories = category === 'all'
    ? ['auth', 'erp', 'hr', 'banking', 'cards', 'storage']
    : [category]

  const countByStatus = (s: CardStatus) => integrations.filter(i => i.status === s).length

  const modalIntegration = modal ? getIntegration(modal.integrationId) : null

  return (
    <div className="min-w-0 w-full max-w-full">
      {/* Header */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">{t('integrations.title') || 'Integrations Hub'}</h1>
            <p className="text-textSecondary">{t('integrations.subtitle') || 'Connect and manage external system integrations'}</p>
          </div>
          <div className="flex items-center space-x-3">
            <button type="button" className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
              <FontAwesomeIcon icon={faBook} />
              <span>{t('integrations.documentation') || 'Documentation'}</span>
            </button>
            <button type="button" className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2">
              <FontAwesomeIcon icon={faPlus} />
              <span>{t('integrations.addIntegration') || 'Add Integration'}</span>
            </button>
          </div>
        </div>
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-surface border border-borderColor rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">{t('integrations.active') || 'Active'}</span>
              <div className="w-2 h-2 bg-successGreen rounded-full" />
            </div>
            <div className="text-2xl font-bold text-textPrimary">{countByStatus('connected')}</div>
            <div className="text-xs text-textMuted mt-1">{t('integrations.connectedIntegrations') || 'Connected integrations'}</div>
          </div>
          <div className="bg-surface border border-borderColor rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">{t('integrations.pending') || 'Pending'}</span>
              <div className="w-2 h-2 bg-warningAmber rounded-full animate-pulse" />
            </div>
            <div className="text-2xl font-bold text-textPrimary">{countByStatus('pending')}</div>
            <div className="text-xs text-textMuted mt-1">{t('integrations.setupInProgress') || 'Setup in progress'}</div>
          </div>
          <div className="bg-surface border border-borderColor rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">{t('integrations.errors') || 'Errors'}</span>
              <div className="w-2 h-2 bg-errorRed rounded-full" />
            </div>
            <div className="text-2xl font-bold text-textPrimary">{countByStatus('error')}</div>
            <div className="text-xs text-textMuted mt-1">{t('integrations.requiresAttention') || 'Requires attention'}</div>
          </div>
          <div className="bg-surface border border-borderColor rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">{t('integrations.available') || 'Available'}</span>
              <FontAwesomeIcon icon={faPlus} className="text-textMuted" />
            </div>
            <div className="text-2xl font-bold text-textPrimary">{countByStatus('not_connected')}</div>
            <div className="text-xs text-textMuted mt-1">{t('integrations.readyToConnect') || 'Ready to connect'}</div>
          </div>
        </div>
      </section>

      {/* Category Tabs */}
      <section className="mb-8">
        <div className="flex items-center space-x-2 overflow-x-auto pb-2">
          {CATEGORY_TABS.map((tab) => (
            <button key={tab.key} type="button" onClick={() => setCategory(tab.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap flex items-center space-x-2 ${category === tab.key ? 'bg-primary text-white' : 'bg-surface border border-borderColor text-textSecondary hover:bg-gray-50'}`}>
              {tab.icon && <FontAwesomeIcon icon={tab.icon} />}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Integration Cards by Category */}
      {filteredCategories.map(cat => {
        const catIntegrations = integrations.filter(i => i.category === cat)
        if (catIntegrations.length === 0) return null
        const titleKey = cat === 'auth' ? 'integrations.authSso' : cat === 'erp' ? 'integrations.erpSystems' : cat === 'hr' ? 'integrations.hrSystems' : cat === 'banking' ? 'integrations.bankingPayments' : cat === 'cards' ? 'integrations.corporateCards' : 'integrations.cloudStorage'
        return (
          <section key={cat} className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-textPrimary">{t(titleKey) || CATEGORY_TITLES[cat]}</h2>
              <button type="button" className="text-sm text-primary hover:text-primaryHover font-medium">{t('integrations.viewAll') || 'View All'}</button>
            </div>
            <div className="grid grid-cols-3 gap-6">
              {catIntegrations.map(integ => (
                <IntegrationCard
                  key={integ.id}
                  name={integ.name}
                  desc={integ.desc}
                  icon={integ.icon}
                  iconBg={integ.iconBg}
                  iconColor={integ.iconColor}
                  status={integ.status}
                  statusLabel={integ.statusLabel}
                  statusBadge={<StatusBadge status={integ.status} />}
                  rows={buildRows(integ)}
                  progress={integ.progress}
                  buttons={buildButtons(integ)}
                />
              ))}
            </div>
          </section>
        )
      })}

      {/* Recent Activity */}
      <section className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-textPrimary mb-1">{t('integrations.recentActivity') || 'Recent Integration Activity'}</h2>
            <p className="text-sm text-textSecondary">{t('integrations.recentActivityDesc') || 'Latest sync and configuration changes'}</p>
          </div>
          <button type="button" className="text-sm text-primary hover:text-primaryHover font-medium">{t('integrations.viewAllActivity') || 'View All Activity'}</button>
        </div>
        <div className="space-y-4">
          {RECENT_ACTIVITY.map((a, i) => (
            <div key={i} className={`flex items-start space-x-4 ${i < RECENT_ACTIVITY.length - 1 ? 'pb-4 border-b border-borderColor' : ''}`}>
              <div className={`w-10 h-10 ${a.iconBg} rounded-lg flex items-center justify-center flex-shrink-0`}>
                <FontAwesomeIcon icon={a.icon} className={a.iconColor} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-textPrimary">{a.title}</span>
                  <span className="text-xs text-textMuted">{a.time}</span>
                </div>
                <p className="text-sm text-textSecondary mb-2">{a.detail}</p>
                <div className="flex items-center space-x-2 flex-wrap gap-1">
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${a.badge === 'Success' ? 'text-successGreen bg-green-50' : a.badge === 'In Progress' ? 'text-infoBlue bg-blue-50' : a.badge === 'Configuration' ? 'text-warningAmber bg-amber-50' : a.badge === 'Error' ? 'text-errorRed bg-red-50' : 'text-purple-600 bg-purple-50'}`}>{a.badge}</span>
                  {a.by && <span className="text-xs text-textMuted">• {a.by}</span>}
                  {a.fix && <button type="button" onClick={() => handleFixConnection('azure-blob')} className="text-xs text-primary hover:text-primaryHover font-medium">Fix Now →</button>}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Help Section */}
      <section className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-8 border border-indigo-100">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center">
                <FontAwesomeIcon icon={faQuestionCircle} className="text-white text-xl" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-textPrimary">{t('integrations.needHelp') || 'Need Help with Integrations?'}</h2>
                <p className="text-sm text-textSecondary">{t('integrations.needHelpDesc') || 'Our support team is here to assist you'}</p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-white rounded-lg p-4">
                <div className="flex items-center space-x-3 mb-2">
                  <FontAwesomeIcon icon={faBook} className="text-primary" />
                  <span className="text-sm font-medium text-textPrimary">{t('integrations.documentation') || 'Documentation'}</span>
                </div>
                <p className="text-xs text-textSecondary">{t('integrations.docsDesc') || 'Step-by-step integration guides'}</p>
              </div>
              <div className="bg-white rounded-lg p-4">
                <div className="flex items-center space-x-3 mb-2">
                  <FontAwesomeIcon icon={faVideo} className="text-primary" />
                  <span className="text-sm font-medium text-textPrimary">{t('integrations.videoTutorials') || 'Video Tutorials'}</span>
                </div>
                <p className="text-xs text-textSecondary">{t('integrations.videoDesc') || 'Watch setup demonstrations'}</p>
              </div>
              <div className="bg-white rounded-lg p-4">
                <div className="flex items-center space-x-3 mb-2">
                  <FontAwesomeIcon icon={faHeadset} className="text-primary" />
                  <span className="text-sm font-medium text-textPrimary">{t('integrations.liveSupport') || 'Live Support'}</span>
                </div>
                <p className="text-xs text-textSecondary">{t('integrations.supportDesc') || 'Chat with our experts'}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button type="button" className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium">{t('integrations.contactSupport') || 'Contact Support'}</button>
              <button type="button" className="h-10 px-6 border-2 border-primary text-primary hover:bg-indigo-50 rounded-lg text-sm font-medium">{t('integrations.viewDocumentation') || 'View Documentation'}</button>
            </div>
          </div>
        </div>
      </section>

      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-4">
          <div className={`flex items-center space-x-3 px-5 py-3 rounded-xl shadow-lg border ${toast.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' : toast.type === 'error' ? 'bg-red-50 border-red-200 text-red-800' : 'bg-blue-50 border-blue-200 text-blue-800'}`}>
            <FontAwesomeIcon icon={toast.type === 'success' ? faCheckCircle : toast.type === 'error' ? faExclamationCircle : faInfoCircle} />
            <span className="text-sm font-medium">{toast.message}</span>
            <button type="button" onClick={() => setToast(null)} className="ml-2 opacity-60 hover:opacity-100">
              <FontAwesomeIcon icon={faTimes} />
            </button>
          </div>
        </div>
      )}

      {/* Modals */}
      {modal && modalIntegration && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setModal(null)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>

            {/* Configure Modal */}
            {modal.type === 'configure' && (
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 ${modalIntegration.iconBg} rounded-lg flex items-center justify-center`}>
                      <FontAwesomeIcon icon={modalIntegration.icon} className={modalIntegration.iconColor} />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-textPrimary">Configure {modalIntegration.name}</h3>
                      <p className="text-xs text-textSecondary">Manage integration settings</p>
                    </div>
                  </div>
                  <button type="button" onClick={() => setModal(null)} className="text-textMuted hover:text-textPrimary"><FontAwesomeIcon icon={faTimes} /></button>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-textPrimary mb-1">API Key</label>
                    <div className="relative">
                      <FontAwesomeIcon icon={faKey} className="absolute left-3 top-1/2 -translate-y-1/2 text-textMuted" />
                      <input type="text" value={configForm.apiKey} onChange={e => setConfigForm(p => ({ ...p, apiKey: e.target.value }))}
                        className="w-full pl-10 pr-4 py-2.5 border border-borderColor rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary" placeholder="Enter API key..." />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-textPrimary mb-1">Sync Frequency</label>
                    <select value={configForm.syncFrequency} onChange={e => setConfigForm(p => ({ ...p, syncFrequency: e.target.value }))}
                      className="w-full px-4 py-2.5 border border-borderColor rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary">
                      <option value="realtime">Real-time</option>
                      <option value="hourly">Every Hour</option>
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                    </select>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium text-textPrimary">Auto-map Fields</span>
                      <p className="text-xs text-textSecondary">Automatically map remote fields to local schema</p>
                    </div>
                    <button type="button" onClick={() => setConfigForm(p => ({ ...p, autoMap: !p.autoMap }))}
                      className={`w-11 h-6 rounded-full transition-colors ${configForm.autoMap ? 'bg-primary' : 'bg-gray-300'}`}>
                      <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${configForm.autoMap ? 'translate-x-5' : 'translate-x-0.5'}`} />
                    </button>
                  </div>
                  <div className="pt-2 border-t border-borderColor">
                    <h4 className="text-sm font-medium text-textPrimary mb-2">Current Details</h4>
                    {modalIntegration.details.map((d, i) => (
                      <div key={i} className="flex justify-between text-sm py-1">
                        <span className="text-textSecondary">{d.label}</span>
                        <span className="text-textPrimary font-medium">{d.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex items-center space-x-3 mt-6">
                  <button type="button" onClick={handleSaveConfigure} className="flex-1 h-10 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium">Save Configuration</button>
                  <button type="button" onClick={() => setModal(null)} className="flex-1 h-10 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">Cancel</button>
                </div>
              </div>
            )}

            {/* Connect Wizard Modal */}
            {modal.type === 'connect' && (
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 ${modalIntegration.iconBg} rounded-lg flex items-center justify-center`}>
                      <FontAwesomeIcon icon={modalIntegration.icon} className={modalIntegration.iconColor} />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-textPrimary">Connect {modalIntegration.name}</h3>
                      <p className="text-xs text-textSecondary">Step {wizardStep} of 3</p>
                    </div>
                  </div>
                  <button type="button" onClick={() => setModal(null)} className="text-textMuted hover:text-textPrimary"><FontAwesomeIcon icon={faTimes} /></button>
                </div>
                {/* Progress */}
                <div className="flex items-center space-x-2 mb-6">
                  {[1, 2, 3].map(s => (
                    <div key={s} className="flex-1">
                      <div className={`h-1.5 rounded-full ${s <= wizardStep ? 'bg-primary' : 'bg-gray-200'}`} />
                      <p className={`text-xs mt-1 ${s <= wizardStep ? 'text-primary font-medium' : 'text-textMuted'}`}>
                        {s === 1 ? 'Credentials' : s === 2 ? 'Configure' : 'Done'}
                      </p>
                    </div>
                  ))}
                </div>
                {wizardStep === 1 && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-textPrimary mb-1">API Key / Client ID</label>
                      <input type="text" value={configForm.apiKey} onChange={e => setConfigForm(p => ({ ...p, apiKey: e.target.value }))}
                        className="w-full px-4 py-2.5 border border-borderColor rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary" placeholder="Enter your API key..." />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-textPrimary mb-1">Client Secret</label>
                      <input type="password" className="w-full px-4 py-2.5 border border-borderColor rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary" placeholder="Enter client secret..." />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-textPrimary mb-1">Environment</label>
                      <select className="w-full px-4 py-2.5 border border-borderColor rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary">
                        <option>Production</option>
                        <option>Sandbox</option>
                      </select>
                    </div>
                  </div>
                )}
                {wizardStep === 2 && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-textPrimary mb-1">Sync Frequency</label>
                      <select value={configForm.syncFrequency} onChange={e => setConfigForm(p => ({ ...p, syncFrequency: e.target.value }))}
                        className="w-full px-4 py-2.5 border border-borderColor rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary">
                        <option value="realtime">Real-time</option>
                        <option value="hourly">Every Hour</option>
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                      </select>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-sm font-medium text-textPrimary">Auto-map Fields</span>
                        <p className="text-xs text-textSecondary">Automatically map remote fields</p>
                      </div>
                      <button type="button" onClick={() => setConfigForm(p => ({ ...p, autoMap: !p.autoMap }))}
                        className={`w-11 h-6 rounded-full transition-colors ${configForm.autoMap ? 'bg-primary' : 'bg-gray-300'}`}>
                        <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${configForm.autoMap ? 'translate-x-5' : 'translate-x-0.5'}`} />
                      </button>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-sm font-medium text-textPrimary">Enable Webhooks</span>
                        <p className="text-xs text-textSecondary">Receive real-time event notifications</p>
                      </div>
                      <button type="button" className="w-11 h-6 rounded-full bg-primary">
                        <div className="w-5 h-5 bg-white rounded-full shadow translate-x-5" />
                      </button>
                    </div>
                  </div>
                )}
                {wizardStep === 3 && (
                  <div className="text-center py-6">
                    <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
                      <FontAwesomeIcon icon={faCheckCircle} className="text-successGreen text-3xl" />
                    </div>
                    <h4 className="text-lg font-semibold text-textPrimary mb-2">Ready to Connect!</h4>
                    <p className="text-sm text-textSecondary mb-4">All settings are configured. Click &quot;Finish&quot; to activate the integration.</p>
                  </div>
                )}
                <div className="flex items-center space-x-3 mt-6">
                  {wizardStep > 1 && (
                    <button type="button" onClick={() => setWizardStep(s => s - 1)} className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-1">
                      <FontAwesomeIcon icon={faArrowLeft} /><span>Back</span>
                    </button>
                  )}
                  <div className="flex-1" />
                  {wizardStep < 3 ? (
                    <button type="button" onClick={() => setWizardStep(s => s + 1)} className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-1">
                      <span>Next</span><FontAwesomeIcon icon={faArrowRight} />
                    </button>
                  ) : (
                    <button type="button" onClick={handleFinishConnect} className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-1">
                      <FontAwesomeIcon icon={faCheck} /><span>Finish</span>
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Fix Connection Modal */}
            {modal.type === 'fix' && (
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-red-50 rounded-lg flex items-center justify-center">
                      <FontAwesomeIcon icon={faExclamationCircle} className="text-errorRed" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-textPrimary">Fix {modalIntegration.name}</h3>
                      <p className="text-xs text-textSecondary">Re-authenticate to restore connection</p>
                    </div>
                  </div>
                  <button type="button" onClick={() => setModal(null)} className="text-textMuted hover:text-textPrimary"><FontAwesomeIcon icon={faTimes} /></button>
                </div>
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                  <div className="flex items-center space-x-2 mb-1">
                    <FontAwesomeIcon icon={faExclamationTriangle} className="text-errorRed" />
                    <span className="text-sm font-medium text-red-800">Authentication Error</span>
                  </div>
                  <p className="text-sm text-red-700">The access token has expired. Please provide new credentials to restore the connection.</p>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-textPrimary mb-1">New API Key / Token</label>
                    <input type="text" value={configForm.apiKey} onChange={e => setConfigForm(p => ({ ...p, apiKey: e.target.value }))}
                      className="w-full px-4 py-2.5 border border-borderColor rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary" placeholder="Enter new access token..." />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-textPrimary mb-1">Secret Key</label>
                    <input type="password" className="w-full px-4 py-2.5 border border-borderColor rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary" placeholder="Enter secret key..." />
                  </div>
                </div>
                <div className="flex items-center space-x-3 mt-6">
                  <button type="button" onClick={handleSaveFix} className="flex-1 h-10 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium">Reconnect</button>
                  <button type="button" onClick={() => setModal(null)} className="flex-1 h-10 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">Cancel</button>
                </div>
              </div>
            )}

            {/* Logs Modal */}
            {modal.type === 'logs' && (
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 ${modalIntegration.iconBg} rounded-lg flex items-center justify-center`}>
                      <FontAwesomeIcon icon={modalIntegration.icon} className={modalIntegration.iconColor} />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-textPrimary">{modalIntegration.name} Logs</h3>
                      <p className="text-xs text-textSecondary">Recent sync activity</p>
                    </div>
                  </div>
                  <button type="button" onClick={() => setModal(null)} className="text-textMuted hover:text-textPrimary"><FontAwesomeIcon icon={faTimes} /></button>
                </div>
                <div className="bg-gray-900 rounded-lg p-4 font-mono text-xs space-y-1 max-h-80 overflow-y-auto">
                  {SAMPLE_LOGS.map((log, i) => (
                    <div key={i} className="flex">
                      <span className="text-gray-500 mr-2 shrink-0">{log.time}</span>
                      <span className={`mr-2 shrink-0 ${log.level === 'INFO' ? 'text-green-400' : log.level === 'WARN' ? 'text-yellow-400' : 'text-red-400'}`}>[{log.level}]</span>
                      <span className="text-gray-300">{log.message}</span>
                    </div>
                  ))}
                </div>
                <div className="flex items-center space-x-3 mt-6">
                  <button type="button" onClick={() => { handleExport(modal.integrationId); setModal(null) }} className="flex-1 h-10 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center justify-center space-x-1">
                    <FontAwesomeIcon icon={faDownload} /><span>Export Logs</span>
                  </button>
                  <button type="button" onClick={() => setModal(null)} className="flex-1 h-10 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium">Close</button>
                </div>
              </div>
            )}

            {/* Usage Modal */}
            {modal.type === 'usage' && (
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 ${modalIntegration.iconBg} rounded-lg flex items-center justify-center`}>
                      <FontAwesomeIcon icon={modalIntegration.icon} className={modalIntegration.iconColor} />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-textPrimary">{modalIntegration.name} Usage</h3>
                      <p className="text-xs text-textSecondary">Storage and usage statistics</p>
                    </div>
                  </div>
                  <button type="button" onClick={() => setModal(null)} className="text-textMuted hover:text-textPrimary"><FontAwesomeIcon icon={faTimes} /></button>
                </div>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-blue-50 rounded-lg p-4">
                      <p className="text-xs text-textSecondary mb-1">Storage Used</p>
                      <p className="text-xl font-bold text-textPrimary">124.5 GB</p>
                      <p className="text-xs text-textMuted">of 500 GB limit</p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4">
                      <p className="text-xs text-textSecondary mb-1">Files Stored</p>
                      <p className="text-xl font-bold text-textPrimary">12,847</p>
                      <p className="text-xs text-textMuted">across 34 buckets</p>
                    </div>
                    <div className="bg-amber-50 rounded-lg p-4">
                      <p className="text-xs text-textSecondary mb-1">API Calls (Today)</p>
                      <p className="text-xl font-bold text-textPrimary">2,481</p>
                      <p className="text-xs text-textMuted">avg 1,856/day</p>
                    </div>
                    <div className="bg-purple-50 rounded-lg p-4">
                      <p className="text-xs text-textSecondary mb-1">Bandwidth</p>
                      <p className="text-xl font-bold text-textPrimary">8.2 GB</p>
                      <p className="text-xs text-textMuted">this month</p>
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-textPrimary mb-2">Storage Breakdown</h4>
                    <div className="space-y-2">
                      {[
                        { label: 'Receipts', pct: 45, color: 'bg-blue-500' },
                        { label: 'Invoices', pct: 30, color: 'bg-green-500' },
                        { label: 'Reports', pct: 15, color: 'bg-amber-500' },
                        { label: 'Other', pct: 10, color: 'bg-gray-400' },
                      ].map((item, i) => (
                        <div key={i}>
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-textSecondary">{item.label}</span>
                            <span className="text-textPrimary font-medium">{item.pct}%</span>
                          </div>
                          <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div className={`h-full ${item.color} rounded-full`} style={{ width: `${item.pct}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-3 mt-6">
                  <button type="button" onClick={() => setModal(null)} className="flex-1 h-10 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium">Close</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

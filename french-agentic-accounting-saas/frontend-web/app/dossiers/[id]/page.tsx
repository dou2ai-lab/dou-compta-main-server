'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faArrowLeft,
  faBuilding,
  faFileAlt,
  faClock,
  faChartLine,
  faEdit,
} from '@fortawesome/free-solid-svg-icons'
import Link from 'next/link'
import { dossierAPI } from '@/lib/api'

type TabView = 'overview' | 'documents' | 'timeline'

export default function DossierDetailPage() {
  const params = useParams()
  const dossierId = params.id as string
  const [tab, setTab] = useState<TabView>('overview')
  const [summary, setSummary] = useState<any>(null)
  const [documents, setDocuments] = useState<any[]>([])
  const [timeline, setTimeline] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadSummary() }, [dossierId])
  useEffect(() => {
    if (tab === 'documents') loadDocuments()
    if (tab === 'timeline') loadTimeline()
  }, [tab])

  async function loadSummary() {
    setLoading(true)
    try {
      const res = await dossierAPI.getSummary(dossierId)
      setSummary(res)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  async function loadDocuments() {
    try {
      const res = await dossierAPI.listDocuments(dossierId)
      setDocuments(res || [])
    } catch (err) { console.error(err) }
  }

  async function loadTimeline() {
    try {
      const res = await dossierAPI.getTimeline(dossierId)
      setTimeline(res || [])
    } catch (err) { console.error(err) }
  }

  const fmt = (n: number) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n)

  if (loading) return <div className="p-6 text-center text-textSecondary">Chargement...</div>
  if (!summary) return <div className="p-6 text-center text-textSecondary">Dossier non trouve. <Link href="/dossiers" className="text-primary">Retour</Link></div>

  const d = summary.dossier

  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link href="/dossiers" className="text-textSecondary hover:text-textPrimary"><FontAwesomeIcon icon={faArrowLeft} /></Link>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-textPrimary flex items-center gap-3">
            <FontAwesomeIcon icon={faBuilding} className="text-primary" />
            {d.client_name}
          </h1>
          <p className="text-sm text-textSecondary mt-1">
            {d.legal_form && `${d.legal_form} - `}{d.siren && `SIREN ${d.siren}`}
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg border border-borderColor">
          <div className="text-xs text-textSecondary uppercase mb-1">Documents</div>
          <div className="text-2xl font-bold">{summary.document_count}</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-borderColor">
          <div className="text-xs text-textSecondary uppercase mb-1">Ecritures</div>
          <div className="text-2xl font-bold">{summary.entry_count}</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-borderColor">
          <div className="text-xs text-textSecondary uppercase mb-1">Total Debit</div>
          <div className="text-lg font-semibold text-green-600">{fmt(summary.total_debit)}</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-borderColor">
          <div className="text-xs text-textSecondary uppercase mb-1">Total Credit</div>
          <div className="text-lg font-semibold text-blue-600">{fmt(summary.total_credit)}</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {[
          { key: 'overview', icon: faChartLine, label: 'Apercu' },
          { key: 'documents', icon: faFileAlt, label: 'Documents' },
          { key: 'timeline', icon: faClock, label: 'Historique' },
        ].map(t => (
          <button key={t.key} onClick={() => setTab(t.key as TabView)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === t.key ? 'bg-white shadow text-primary' : 'text-textSecondary hover:text-textPrimary'}`}>
            <FontAwesomeIcon icon={t.icon} className="mr-2" />{t.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {tab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-borderColor p-5">
            <h3 className="font-semibold text-sm mb-4">Informations generales</h3>
            <dl className="space-y-2 text-sm">
              {[
                ['SIREN', d.siren], ['SIRET', d.siret], ['Forme juridique', d.legal_form],
                ['Regime TVA', d.regime_tva], ['Regime IS', d.regime_is],
                ['Email', d.email], ['Telephone', d.phone],
                ['Adresse', [d.address_line1, d.postal_code, d.city].filter(Boolean).join(', ')],
              ].filter(([, v]) => v).map(([label, value]) => (
                <div key={label as string} className="flex">
                  <dt className="w-32 text-textSecondary">{label}</dt>
                  <dd className="text-textPrimary">{value}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div className="bg-white rounded-xl border border-borderColor p-5">
            <h3 className="font-semibold text-sm mb-4">Activite recente</h3>
            {summary.recent_events?.length > 0 ? (
              <div className="space-y-3">
                {summary.recent_events.slice(0, 5).map((e: any) => (
                  <div key={e.id} className="flex gap-3 text-sm">
                    <div className="w-2 h-2 rounded-full bg-primary mt-1.5 shrink-0" />
                    <div>
                      <p className="text-textPrimary">{e.title}</p>
                      <p className="text-xs text-textSecondary">{new Date(e.created_at).toLocaleDateString('fr-FR')}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-textSecondary">Aucune activite recente</p>
            )}
          </div>
        </div>
      )}

      {/* Documents Tab */}
      {tab === 'documents' && (
        <div className="bg-white rounded-xl border border-borderColor overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-borderColor">
                <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Type</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Titre</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Date</th>
              </tr>
            </thead>
            <tbody>
              {documents.length === 0 ? (
                <tr><td colSpan={3} className="text-center py-8 text-textSecondary">Aucun document</td></tr>
              ) : documents.map((doc: any) => (
                <tr key={doc.id} className="border-b border-borderColor hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm"><span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs">{doc.document_type}</span></td>
                  <td className="px-4 py-3 text-sm text-textPrimary">{doc.title}</td>
                  <td className="px-4 py-3 text-sm text-textSecondary">{new Date(doc.created_at).toLocaleDateString('fr-FR')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Timeline Tab */}
      {tab === 'timeline' && (
        <div className="bg-white rounded-xl border border-borderColor p-5">
          {timeline.length === 0 ? (
            <p className="text-center py-8 text-textSecondary">Aucun evenement</p>
          ) : (
            <div className="space-y-4">
              {timeline.map((e: any) => (
                <div key={e.id} className="flex gap-4 pb-4 border-b border-borderColor last:border-0">
                  <div className="w-8 h-8 rounded-full bg-indigo-50 flex items-center justify-center shrink-0">
                    <FontAwesomeIcon icon={faClock} className="text-primary text-xs" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-textPrimary">{e.title}</p>
                    {e.description && <p className="text-xs text-textSecondary mt-1">{e.description}</p>}
                    <p className="text-xs text-textMuted mt-1">{new Date(e.created_at).toLocaleString('fr-FR')}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

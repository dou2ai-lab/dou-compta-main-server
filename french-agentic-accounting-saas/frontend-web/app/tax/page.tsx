'use client'

import { useState, useEffect } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faFileInvoiceDollar,
  faCalendarAlt,
  faExclamationTriangle,
  faPlus,
  faChevronLeft,
  faChevronRight,
} from '@fortawesome/free-solid-svg-icons'
import Link from 'next/link'
import { taxAPI } from '@/lib/api'

const TYPE_LABELS: Record<string, string> = {
  CA3: 'TVA mensuelle (CA3)',
  CA12: 'TVA annuelle (CA12)',
  IS: 'Impot sur les societes',
  CVAE: 'CVAE',
  CFE: 'CFE',
  DAS2: 'DAS2 - Honoraires',
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  computed: 'bg-blue-100 text-blue-800',
  validated: 'bg-green-100 text-green-800',
  submitted: 'bg-purple-100 text-purple-800',
  accepted: 'bg-green-200 text-green-900',
  rejected: 'bg-red-100 text-red-800',
}

const STATUS_LABELS: Record<string, string> = {
  draft: 'Brouillon',
  computed: 'Calculee',
  validated: 'Validee',
  submitted: 'Deposee',
  accepted: 'Acceptee',
  rejected: 'Rejetee',
}

type TabView = 'declarations' | 'calendar' | 'penalties'

export default function TaxPage() {
  const [tab, setTab] = useState<TabView>('declarations')
  const [declarations, setDeclarations] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [calendar, setCalendar] = useState<any[]>([])
  const [penalties, setPenalties] = useState<any[]>([])
  const [typeFilter, setTypeFilter] = useState('')

  useEffect(() => { loadDeclarations() }, [page, typeFilter])
  useEffect(() => {
    if (tab === 'calendar') loadCalendar()
    if (tab === 'penalties') loadPenalties()
  }, [tab])

  async function loadDeclarations() {
    setLoading(true)
    try {
      const params: any = { page, page_size: 20 }
      if (typeFilter) params.type = typeFilter
      const res = await taxAPI.listDeclarations(params)
      setDeclarations(res.data || [])
      setTotal(res.total || 0)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  async function loadCalendar() {
    try {
      const res = await taxAPI.getCalendar()
      setCalendar(res || [])
    } catch (err) { console.error(err) }
  }

  async function loadPenalties() {
    try {
      const res = await taxAPI.getPenalties()
      setPenalties(res || [])
    } catch (err) { console.error(err) }
  }

  const fmt = (n: number) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n)
  const totalPages = Math.ceil(total / 20)

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-textPrimary">Fiscalite</h1>
          <p className="text-sm text-textSecondary mt-1">Declarations fiscales et echeances</p>
        </div>
        <Link href="/tax/compute" className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary/90">
          <FontAwesomeIcon icon={faPlus} /> Nouvelle declaration
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {[
          { key: 'declarations', icon: faFileInvoiceDollar, label: 'Declarations' },
          { key: 'calendar', icon: faCalendarAlt, label: 'Echeancier' },
          { key: 'penalties', icon: faExclamationTriangle, label: 'Alertes' },
        ].map(t => (
          <button key={t.key} onClick={() => setTab(t.key as TabView)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === t.key ? 'bg-white shadow text-primary' : 'text-textSecondary hover:text-textPrimary'}`}>
            <FontAwesomeIcon icon={t.icon} className="mr-2" />{t.label}
          </button>
        ))}
      </div>

      {/* Declarations Tab */}
      {tab === 'declarations' && (
        <>
          <div className="flex gap-3 mb-4">
            <select value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1) }}
              className="px-3 py-2 border border-borderColor rounded-lg text-sm">
              <option value="">Tous les types</option>
              {Object.entries(TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div className="bg-white rounded-xl border border-borderColor overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-borderColor">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Type</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Periode</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Echeance</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Montant</th>
                  <th className="text-center px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Statut</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={5} className="text-center py-12 text-textSecondary">Chargement...</td></tr>
                ) : declarations.length === 0 ? (
                  <tr><td colSpan={5} className="text-center py-12 text-textSecondary">Aucune declaration</td></tr>
                ) : declarations.map((d) => (
                  <tr key={d.id} className="border-b border-borderColor hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link href={`/tax/declarations/${d.id}`} className="text-sm font-medium text-primary hover:underline">
                        {TYPE_LABELS[d.type] || d.type}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-sm text-textSecondary">
                      {new Date(d.period_start).toLocaleDateString('fr-FR')} - {new Date(d.period_end).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="px-4 py-3 text-sm text-textSecondary">
                      {d.due_date ? new Date(d.due_date).toLocaleDateString('fr-FR') : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-medium">{fmt(d.total_amount)}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[d.status] || 'bg-gray-100'}`}>
                        {STATUS_LABELS[d.status] || d.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-borderColor">
                <span className="text-sm text-textSecondary">Page {page} / {totalPages}</span>
                <div className="flex gap-2">
                  <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1 border rounded text-sm disabled:opacity-50"><FontAwesomeIcon icon={faChevronLeft} /></button>
                  <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="px-3 py-1 border rounded text-sm disabled:opacity-50"><FontAwesomeIcon icon={faChevronRight} /></button>
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {/* Calendar Tab */}
      {tab === 'calendar' && (
        <div className="bg-white rounded-xl border border-borderColor overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-borderColor">
                <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Echeance</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Type</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Statut</th>
              </tr>
            </thead>
            <tbody>
              {calendar.length === 0 ? (
                <tr><td colSpan={3} className="text-center py-12 text-textSecondary">Aucune echeance configuree</td></tr>
              ) : calendar.map((c) => (
                <tr key={c.id} className="border-b border-borderColor hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium">{new Date(c.due_date).toLocaleDateString('fr-FR')}</td>
                  <td className="px-4 py-3 text-sm text-textSecondary">{TYPE_LABELS[c.declaration_type] || c.declaration_type}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      c.status === 'overdue' ? 'bg-red-100 text-red-800' :
                      c.status === 'due' ? 'bg-yellow-100 text-yellow-800' :
                      c.status === 'completed' ? 'bg-green-100 text-green-800' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {c.status === 'overdue' ? 'En retard' : c.status === 'due' ? 'A deposer' : c.status === 'completed' ? 'Fait' : 'A venir'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Penalties Tab */}
      {tab === 'penalties' && (
        <div className="space-y-4">
          {penalties.length === 0 ? (
            <div className="bg-green-50 rounded-xl border border-green-200 p-6 text-center">
              <p className="text-green-800 font-medium">Aucune alerte - toutes les declarations sont a jour</p>
            </div>
          ) : penalties.map((p, i) => (
            <div key={i} className="bg-red-50 rounded-xl border border-red-200 p-5">
              <div className="flex items-start gap-3">
                <FontAwesomeIcon icon={faExclamationTriangle} className="text-red-500 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-red-900">{TYPE_LABELS[p.declaration_type] || p.declaration_type}</p>
                  <p className="text-sm text-red-800 mt-1">{p.message}</p>
                  <div className="flex gap-4 mt-2 text-xs text-red-700">
                    <span>Echeance: {new Date(p.due_date).toLocaleDateString('fr-FR')}</span>
                    <span>Retard: {p.days_overdue} jours</span>
                    <span>Penalite estimee: {fmt(p.estimated_penalty)}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

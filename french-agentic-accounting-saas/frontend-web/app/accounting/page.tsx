'use client'

import { useState, useEffect } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faBook,
  faBalanceScale,
  faFileExport,
  faCheck,
  faFilter,
  faPlus,
  faSearch,
  faChevronLeft,
  faChevronRight,
} from '@fortawesome/free-solid-svg-icons'
import Link from 'next/link'
import { accountingAPI } from '@/lib/api'

const JOURNAL_LABELS: Record<string, string> = {
  ACH: 'Achats',
  VTE: 'Ventes',
  BNQ: 'Banque',
  OD: 'Ops Diverses',
  SAL: 'Salaires',
  AN: 'A Nouveaux',
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-yellow-100 text-yellow-800',
  validated: 'bg-green-100 text-green-800',
  posted: 'bg-blue-100 text-blue-800',
}

type TabView = 'entries' | 'trial-balance'

export default function AccountingPage() {
  const [tab, setTab] = useState<TabView>('entries')
  const [entries, setEntries] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [loading, setLoading] = useState(true)
  const [journalFilter, setJournalFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [fiscalYear, setFiscalYear] = useState(new Date().getFullYear())

  // Trial balance state
  const [trialBalance, setTrialBalance] = useState<any>(null)
  const [tbLoading, setTbLoading] = useState(false)

  useEffect(() => {
    loadEntries()
  }, [page, journalFilter, statusFilter, fiscalYear])

  async function loadEntries() {
    setLoading(true)
    try {
      const params: any = { page, page_size: pageSize }
      if (journalFilter) params.journal_code = journalFilter
      if (statusFilter) params.status = statusFilter
      if (fiscalYear) params.fiscal_year = fiscalYear
      const res = await accountingAPI.listEntries(params)
      setEntries(res.data || [])
      setTotal(res.total || 0)
    } catch (err) {
      console.error('Failed to load entries', err)
    } finally {
      setLoading(false)
    }
  }

  async function loadTrialBalance() {
    setTbLoading(true)
    try {
      const res = await accountingAPI.getTrialBalance(fiscalYear)
      setTrialBalance(res)
    } catch (err) {
      console.error('Failed to load trial balance', err)
    } finally {
      setTbLoading(false)
    }
  }

  useEffect(() => {
    if (tab === 'trial-balance') loadTrialBalance()
  }, [tab, fiscalYear])

  const totalPages = Math.ceil(total / pageSize)
  const fmt = (n: number) =>
    new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n)

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-textPrimary">Comptabilite</h1>
          <p className="text-sm text-textSecondary mt-1">
            Journal des ecritures comptables - PCG 2025
          </p>
        </div>
        <div className="flex gap-3">
          <Link
            href="/accounting/fec"
            className="flex items-center gap-2 px-4 py-2 bg-white border border-borderColor rounded-lg text-sm hover:bg-gray-50"
          >
            <FontAwesomeIcon icon={faFileExport} />
            Export FEC
          </Link>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        <button
          onClick={() => setTab('entries')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            tab === 'entries' ? 'bg-white shadow text-primary' : 'text-textSecondary hover:text-textPrimary'
          }`}
        >
          <FontAwesomeIcon icon={faBook} className="mr-2" />
          Ecritures
        </button>
        <button
          onClick={() => setTab('trial-balance')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            tab === 'trial-balance' ? 'bg-white shadow text-primary' : 'text-textSecondary hover:text-textPrimary'
          }`}
        >
          <FontAwesomeIcon icon={faBalanceScale} className="mr-2" />
          Balance des comptes
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6 flex-wrap">
        <select
          value={fiscalYear}
          onChange={(e) => setFiscalYear(Number(e.target.value))}
          className="px-3 py-2 border border-borderColor rounded-lg text-sm"
        >
          {[2026, 2025, 2024, 2023].map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
        {tab === 'entries' && (
          <>
            <select
              value={journalFilter}
              onChange={(e) => { setJournalFilter(e.target.value); setPage(1) }}
              className="px-3 py-2 border border-borderColor rounded-lg text-sm"
            >
              <option value="">Tous les journaux</option>
              {Object.entries(JOURNAL_LABELS).map(([code, label]) => (
                <option key={code} value={code}>{code} - {label}</option>
              ))}
            </select>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
              className="px-3 py-2 border border-borderColor rounded-lg text-sm"
            >
              <option value="">Tous les statuts</option>
              <option value="draft">Brouillon</option>
              <option value="validated">Valide</option>
              <option value="posted">Comptabilise</option>
            </select>
          </>
        )}
      </div>

      {/* Entries Tab */}
      {tab === 'entries' && (
        <div className="bg-white rounded-xl border border-borderColor overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-borderColor">
                <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">N° Ecriture</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Journal</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Date</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Libelle</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Debit</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Credit</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Statut</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} className="text-center py-12 text-textSecondary">Chargement...</td></tr>
              ) : entries.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-12 text-textSecondary">Aucune ecriture trouvee</td></tr>
              ) : (
                entries.map((entry) => (
                  <tr key={entry.id} className="border-b border-borderColor hover:bg-gray-50 cursor-pointer">
                    <td className="px-4 py-3">
                      <Link href={`/accounting/entries/${entry.id}`} className="text-primary font-medium text-sm hover:underline">
                        {entry.entry_number}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700">
                        {entry.journal_code}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-textSecondary">
                      {new Date(entry.entry_date).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="px-4 py-3 text-sm text-textPrimary truncate max-w-[300px]">
                      {entry.description}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-medium">
                      {fmt(entry.total_debit)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-medium">
                      {fmt(entry.total_credit)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[entry.status] || 'bg-gray-100'}`}>
                        {entry.status === 'draft' ? 'Brouillon' : entry.status === 'validated' ? 'Valide' : 'Comptabilise'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-borderColor">
              <span className="text-sm text-textSecondary">
                {total} ecritures - Page {page} / {totalPages}
              </span>
              <div className="flex gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                  className="px-3 py-1 border rounded text-sm disabled:opacity-50"
                >
                  <FontAwesomeIcon icon={faChevronLeft} />
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage(page + 1)}
                  className="px-3 py-1 border rounded text-sm disabled:opacity-50"
                >
                  <FontAwesomeIcon icon={faChevronRight} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Trial Balance Tab */}
      {tab === 'trial-balance' && (
        <div className="bg-white rounded-xl border border-borderColor overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-borderColor">
                <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Compte</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Libelle</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Total Debit</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Total Credit</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Solde</th>
              </tr>
            </thead>
            <tbody>
              {tbLoading ? (
                <tr><td colSpan={5} className="text-center py-12 text-textSecondary">Chargement...</td></tr>
              ) : !trialBalance || !trialBalance.lines?.length ? (
                <tr><td colSpan={5} className="text-center py-12 text-textSecondary">Aucune donnee pour cet exercice</td></tr>
              ) : (
                <>
                  {trialBalance.lines.map((line: any, i: number) => (
                    <tr key={i} className="border-b border-borderColor hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-mono font-medium text-primary">{line.account_code}</td>
                      <td className="px-4 py-3 text-sm text-textPrimary">{line.account_name}</td>
                      <td className="px-4 py-3 text-sm text-right">{fmt(line.total_debit)}</td>
                      <td className="px-4 py-3 text-sm text-right">{fmt(line.total_credit)}</td>
                      <td className={`px-4 py-3 text-sm text-right font-medium ${Number(line.balance) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {fmt(line.balance)}
                      </td>
                    </tr>
                  ))}
                  {/* Totals row */}
                  <tr className="bg-gray-50 font-semibold">
                    <td colSpan={2} className="px-4 py-3 text-sm">TOTAUX</td>
                    <td className="px-4 py-3 text-sm text-right">{fmt(trialBalance.total_debit)}</td>
                    <td className="px-4 py-3 text-sm text-right">{fmt(trialBalance.total_credit)}</td>
                    <td className="px-4 py-3 text-sm text-right">
                      {fmt(Number(trialBalance.total_debit) - Number(trialBalance.total_credit))}
                    </td>
                  </tr>
                </>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

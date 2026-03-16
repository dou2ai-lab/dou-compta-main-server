'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faArrowLeft,
  faSync,
  faUpload,
  faCheck,
  faLink,
  faUnlink,
  faChevronLeft,
  faChevronRight,
} from '@fortawesome/free-solid-svg-icons'
import Link from 'next/link'
import { bankingAPI, accountingAPI } from '@/lib/api'

const STATUS_COLORS: Record<string, string> = {
  unmatched: 'bg-yellow-100 text-yellow-800',
  matched: 'bg-green-100 text-green-800',
  ignored: 'bg-gray-100 text-gray-600',
}

export default function ReconciliationPage() {
  const searchParams = useSearchParams()
  const accountId = searchParams.get('account') || ''

  const [transactions, setTransactions] = useState<any[]>([])
  const [entries, setEntries] = useState<any[]>([])
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [reconciling, setReconciling] = useState(false)
  const [selectedTxn, setSelectedTxn] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    if (accountId) {
      loadData()
      loadSummary()
    }
  }, [accountId, page])

  async function loadData() {
    setLoading(true)
    try {
      const [txnRes, entryRes] = await Promise.all([
        bankingAPI.listTransactions(accountId, { page, page_size: 30 }),
        accountingAPI.listEntries({ journal_code: 'BNQ', page_size: 50 }),
      ])
      setTransactions(txnRes.data || [])
      setTotal(txnRes.total || 0)
      setEntries(entryRes.data || [])
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  async function loadSummary() {
    try {
      const res = await bankingAPI.getReconciliationSummary(accountId)
      setSummary(res)
    } catch { /* ignore */ }
  }

  async function handleReconcile() {
    setReconciling(true)
    try {
      await bankingAPI.reconcile(accountId)
      await loadData()
      await loadSummary()
    } catch (err) { console.error(err) }
    finally { setReconciling(false) }
  }

  async function handleMatch(txnId: string, entryId: string) {
    try {
      await bankingAPI.matchTransaction(txnId, entryId)
      await loadData()
      await loadSummary()
      setSelectedTxn(null)
    } catch (err) { console.error(err) }
  }

  async function handleUnmatch(txnId: string) {
    try {
      await bankingAPI.unmatchTransaction(txnId)
      await loadData()
      await loadSummary()
    } catch (err) { console.error(err) }
  }

  const fmt = (n: number) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n)
  const totalPages = Math.ceil(total / 30)

  return (
    <div className="p-6 max-w-[1600px] mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link href="/banking" className="text-textSecondary hover:text-textPrimary"><FontAwesomeIcon icon={faArrowLeft} /></Link>
          <div>
            <h1 className="text-xl font-bold text-textPrimary">Rapprochement bancaire</h1>
            <p className="text-sm text-textSecondary mt-1">Associer les transactions aux ecritures comptables</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button onClick={handleReconcile} disabled={reconciling}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">
            <FontAwesomeIcon icon={faSync} spin={reconciling} />
            {reconciling ? 'Rapprochement...' : 'Rapprochement auto'}
          </button>
        </div>
      </div>

      {/* Summary bar */}
      {summary && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg border border-borderColor text-center">
            <div className="text-2xl font-bold">{summary.total_transactions}</div>
            <div className="text-xs text-textSecondary">Total</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg border border-green-200 text-center">
            <div className="text-2xl font-bold text-green-700">{summary.matched}</div>
            <div className="text-xs text-green-600">Rapproches</div>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200 text-center">
            <div className="text-2xl font-bold text-yellow-700">{summary.unmatched}</div>
            <div className="text-xs text-yellow-600">Non rapproches</div>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 text-center">
            <div className="text-2xl font-bold text-blue-700">{summary.match_rate}%</div>
            <div className="text-xs text-blue-600">Taux</div>
          </div>
        </div>
      )}

      {/* Two-panel layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Bank Transactions */}
        <div className="bg-white rounded-xl border border-borderColor overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b border-borderColor flex items-center justify-between">
            <h2 className="text-sm font-semibold">Releve bancaire</h2>
            <span className="text-xs text-textSecondary">{total} transactions</span>
          </div>
          <div className="divide-y divide-borderColor max-h-[600px] overflow-y-auto">
            {loading ? (
              <div className="p-8 text-center text-textSecondary">Chargement...</div>
            ) : transactions.length === 0 ? (
              <div className="p-8 text-center text-textSecondary">Aucune transaction</div>
            ) : transactions.map((txn) => (
              <div
                key={txn.id}
                onClick={() => txn.reconciliation_status === 'unmatched' && setSelectedTxn(selectedTxn === txn.id ? null : txn.id)}
                className={`px-4 py-3 cursor-pointer hover:bg-gray-50 ${selectedTxn === txn.id ? 'bg-indigo-50 ring-1 ring-primary' : ''}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-textPrimary truncate">{txn.label}</p>
                    <p className="text-xs text-textSecondary">{new Date(txn.transaction_date).toLocaleDateString('fr-FR')}{txn.counterparty_name ? ` - ${txn.counterparty_name}` : ''}</p>
                  </div>
                  <div className="text-right ml-3">
                    <p className={`text-sm font-semibold ${Number(txn.amount) >= 0 ? 'text-green-600' : 'text-red-600'}`}>{fmt(txn.amount)}</p>
                    <div className="flex items-center gap-1 mt-1">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${STATUS_COLORS[txn.reconciliation_status] || ''}`}>
                        {txn.reconciliation_status === 'matched' ? 'Rapproche' : txn.reconciliation_status === 'unmatched' ? 'En attente' : 'Ignore'}
                      </span>
                      {txn.reconciliation_status === 'matched' && (
                        <button onClick={(e) => { e.stopPropagation(); handleUnmatch(txn.id) }} className="text-red-500 hover:text-red-700" title="Dissocier">
                          <FontAwesomeIcon icon={faUnlink} className="text-[10px]" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-2 border-t border-borderColor">
              <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="text-sm disabled:opacity-50"><FontAwesomeIcon icon={faChevronLeft} /></button>
              <span className="text-xs text-textSecondary">Page {page}/{totalPages}</span>
              <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="text-sm disabled:opacity-50"><FontAwesomeIcon icon={faChevronRight} /></button>
            </div>
          )}
        </div>

        {/* Right: Journal Entries */}
        <div className="bg-white rounded-xl border border-borderColor overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b border-borderColor">
            <h2 className="text-sm font-semibold">Ecritures comptables (BNQ)</h2>
          </div>
          <div className="divide-y divide-borderColor max-h-[600px] overflow-y-auto">
            {entries.length === 0 ? (
              <div className="p-8 text-center text-textSecondary">Aucune ecriture bancaire</div>
            ) : entries.map((entry) => (
              <div key={entry.id} className="px-4 py-3 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-textPrimary">{entry.entry_number}</p>
                    <p className="text-xs text-textSecondary truncate">{entry.description}</p>
                    <p className="text-xs text-textMuted">{new Date(entry.entry_date).toLocaleDateString('fr-FR')}</p>
                  </div>
                  <div className="text-right ml-3">
                    <p className="text-sm font-semibold">{fmt(entry.total_debit)}</p>
                    {selectedTxn && (
                      <button
                        onClick={() => handleMatch(selectedTxn, entry.id)}
                        className="mt-1 text-xs px-2 py-1 bg-primary text-white rounded hover:bg-primary/90 flex items-center gap-1"
                      >
                        <FontAwesomeIcon icon={faLink} /> Associer
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

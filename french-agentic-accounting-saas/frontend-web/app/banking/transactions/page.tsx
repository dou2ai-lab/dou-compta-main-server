'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faChevronLeft, faChevronRight } from '@fortawesome/free-solid-svg-icons'
import Link from 'next/link'
import { bankingAPI } from '@/lib/api'

const STATUS_COLORS: Record<string, string> = {
  unmatched: 'bg-yellow-100 text-yellow-800',
  matched: 'bg-green-100 text-green-800',
  ignored: 'bg-gray-100 text-gray-600',
}

export default function TransactionsPage() {
  const searchParams = useSearchParams()
  const accountId = searchParams.get('account') || ''
  const [transactions, setTransactions] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    if (accountId) loadTransactions()
  }, [accountId, page, statusFilter])

  async function loadTransactions() {
    setLoading(true)
    try {
      const params: any = { page, page_size: 50 }
      if (statusFilter) params.status = statusFilter
      const res = await bankingAPI.listTransactions(accountId, params)
      setTransactions(res.data || [])
      setTotal(res.total || 0)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  const fmt = (n: number) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n)
  const totalPages = Math.ceil(total / 50)

  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/banking" className="text-textSecondary hover:text-textPrimary"><FontAwesomeIcon icon={faArrowLeft} /></Link>
        <div>
          <h1 className="text-xl font-bold text-textPrimary">Transactions bancaires</h1>
          <p className="text-sm text-textSecondary">{total} transactions</p>
        </div>
      </div>

      <div className="flex gap-3 mb-4">
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          className="px-3 py-2 border border-borderColor rounded-lg text-sm">
          <option value="">Tous les statuts</option>
          <option value="unmatched">Non rapproches</option>
          <option value="matched">Rapproches</option>
          <option value="ignored">Ignores</option>
        </select>
      </div>

      <div className="bg-white rounded-xl border border-borderColor overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-borderColor">
              <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Date</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Libelle</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Contrepartie</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Montant</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Statut</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="text-center py-12 text-textSecondary">Chargement...</td></tr>
            ) : transactions.length === 0 ? (
              <tr><td colSpan={5} className="text-center py-12 text-textSecondary">Aucune transaction</td></tr>
            ) : transactions.map((t) => (
              <tr key={t.id} className="border-b border-borderColor hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-textSecondary">{new Date(t.transaction_date).toLocaleDateString('fr-FR')}</td>
                <td className="px-4 py-3 text-sm text-textPrimary truncate max-w-[300px]">{t.label}</td>
                <td className="px-4 py-3 text-sm text-textSecondary">{t.counterparty_name || '-'}</td>
                <td className={`px-4 py-3 text-sm text-right font-medium ${Number(t.amount) >= 0 ? 'text-green-600' : 'text-red-600'}`}>{fmt(t.amount)}</td>
                <td className="px-4 py-3 text-center">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[t.reconciliation_status] || ''}`}>
                    {t.reconciliation_status === 'matched' ? 'Rapproche' : t.reconciliation_status === 'unmatched' ? 'En attente' : 'Ignore'}
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
    </div>
  )
}

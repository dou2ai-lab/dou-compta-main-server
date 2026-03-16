'use client'
import { useState, useEffect } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faFileInvoice, faPlus, faChevronLeft, faChevronRight } from '@fortawesome/free-solid-svg-icons'
import Link from 'next/link'
import { einvoiceAPI } from '@/lib/api'

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800', validated: 'bg-blue-100 text-blue-800',
  sent: 'bg-purple-100 text-purple-800', received: 'bg-indigo-100 text-indigo-800',
  accepted: 'bg-green-100 text-green-800', rejected: 'bg-red-100 text-red-800', paid: 'bg-green-200 text-green-900',
}

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [typeFilter, setTypeFilter] = useState('')

  useEffect(() => { loadInvoices() }, [page, typeFilter])

  async function loadInvoices() {
    setLoading(true)
    try {
      const params: any = { page, page_size: 20 }
      if (typeFilter) params.type = typeFilter
      const res = await einvoiceAPI.list(params)
      setInvoices(res.data || [])
      setTotal(res.total || 0)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  const fmt = (n: number) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n)
  const totalPages = Math.ceil(total / 20)

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-textPrimary">Facturation electronique</h1>
          <p className="text-sm text-textSecondary mt-1">Factur-X / PPF - Conformite 2026</p>
        </div>
        <Link href="/invoices/new" className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary/90">
          <FontAwesomeIcon icon={faPlus} /> Nouvelle facture
        </Link>
      </div>
      <div className="flex gap-3 mb-4">
        <select value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1) }}
          className="px-3 py-2 border border-borderColor rounded-lg text-sm">
          <option value="">Toutes</option>
          <option value="sent">Emises</option>
          <option value="received">Recues</option>
        </select>
      </div>
      <div className="bg-white rounded-xl border border-borderColor overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-borderColor">
              <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">N° Facture</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Type</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Client/Fournisseur</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Date</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-textSecondary uppercase">TTC</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Statut</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="text-center py-12 text-textSecondary">Chargement...</td></tr>
            ) : invoices.length === 0 ? (
              <tr><td colSpan={6} className="text-center py-12 text-textSecondary">Aucune facture</td></tr>
            ) : invoices.map((inv) => (
              <tr key={inv.id} className="border-b border-borderColor hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium text-primary">{inv.invoice_number}</td>
                <td className="px-4 py-3 text-sm">{inv.type === 'sent' ? 'Emise' : 'Recue'}</td>
                <td className="px-4 py-3 text-sm text-textPrimary">{inv.recipient_name || inv.issuer_name}</td>
                <td className="px-4 py-3 text-sm text-textSecondary">{new Date(inv.issue_date).toLocaleDateString('fr-FR')}</td>
                <td className="px-4 py-3 text-sm text-right font-medium">{fmt(inv.total_ttc)}</td>
                <td className="px-4 py-3 text-center">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[inv.status] || 'bg-gray-100'}`}>{inv.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-borderColor">
            <span className="text-sm text-textSecondary">Page {page}/{totalPages}</span>
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

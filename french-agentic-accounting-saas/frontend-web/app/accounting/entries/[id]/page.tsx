'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faArrowLeft,
  faCheck,
  faBook,
  faInfoCircle,
} from '@fortawesome/free-solid-svg-icons'
import Link from 'next/link'
import { accountingAPI } from '@/lib/api'

const JOURNAL_LABELS: Record<string, string> = {
  ACH: 'Journal des Achats',
  VTE: 'Journal des Ventes',
  BNQ: 'Journal de Banque',
  OD: 'Operations Diverses',
  SAL: 'Journal des Salaires',
  AN: 'A Nouveaux',
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  draft: { label: 'Brouillon', color: 'bg-yellow-100 text-yellow-800' },
  validated: { label: 'Valide', color: 'bg-green-100 text-green-800' },
  posted: { label: 'Comptabilise', color: 'bg-blue-100 text-blue-800' },
}

export default function EntryDetailPage() {
  const params = useParams()
  const router = useRouter()
  const entryId = params.id as string

  const [entry, setEntry] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [validating, setValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<any>(null)

  useEffect(() => {
    loadEntry()
  }, [entryId])

  async function loadEntry() {
    setLoading(true)
    try {
      const res = await accountingAPI.getEntry(entryId)
      setEntry(res)
    } catch (err) {
      console.error('Failed to load entry', err)
    } finally {
      setLoading(false)
    }
  }

  async function handleValidate() {
    setValidating(true)
    try {
      const res = await accountingAPI.validateEntry(entryId)
      setValidationResult(res)
      if (res.success) {
        await loadEntry()
      }
    } catch (err) {
      console.error('Validation failed', err)
    } finally {
      setValidating(false)
    }
  }

  const fmt = (n: number) =>
    new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n)

  if (loading) {
    return (
      <div className="p-6 max-w-[1200px] mx-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (!entry) {
    return (
      <div className="p-6 max-w-[1200px] mx-auto text-center py-20">
        <p className="text-textSecondary">Ecriture non trouvee</p>
        <Link href="/accounting" className="text-primary mt-4 inline-block">Retour</Link>
      </div>
    )
  }

  const status = STATUS_LABELS[entry.status] || STATUS_LABELS.draft

  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link href="/accounting" className="text-textSecondary hover:text-textPrimary">
            <FontAwesomeIcon icon={faArrowLeft} />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-textPrimary flex items-center gap-3">
              <FontAwesomeIcon icon={faBook} className="text-primary" />
              {entry.entry_number}
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
                {status.label}
              </span>
            </h1>
            <p className="text-sm text-textSecondary mt-1">
              {JOURNAL_LABELS[entry.journal_code] || entry.journal_code} - {new Date(entry.entry_date).toLocaleDateString('fr-FR')}
            </p>
          </div>
        </div>
        {entry.status === 'draft' && (
          <button
            onClick={handleValidate}
            disabled={validating}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50"
          >
            <FontAwesomeIcon icon={faCheck} />
            {validating ? 'Validation...' : 'Valider'}
          </button>
        )}
      </div>

      {/* Validation messages */}
      {validationResult && (
        <div className={`mb-4 p-4 rounded-lg ${validationResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <p className={`font-medium text-sm ${validationResult.success ? 'text-green-800' : 'text-red-800'}`}>
            {validationResult.success ? 'Ecriture validee avec succes' : 'Erreurs de validation'}
          </p>
          {validationResult.messages?.length > 0 && (
            <ul className="mt-2 space-y-1">
              {validationResult.messages.map((msg: any, i: number) => (
                <li key={i} className={`text-sm ${msg.severity === 'error' ? 'text-red-700' : 'text-yellow-700'}`}>
                  {msg.message}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Entry Info */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg border border-borderColor">
          <div className="text-xs text-textSecondary uppercase mb-1">Exercice</div>
          <div className="text-lg font-semibold">{entry.fiscal_year}</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-borderColor">
          <div className="text-xs text-textSecondary uppercase mb-1">Periode</div>
          <div className="text-lg font-semibold">{entry.fiscal_period}</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-borderColor">
          <div className="text-xs text-textSecondary uppercase mb-1">Total Debit</div>
          <div className="text-lg font-semibold text-green-600">{fmt(entry.total_debit)}</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-borderColor">
          <div className="text-xs text-textSecondary uppercase mb-1">Total Credit</div>
          <div className="text-lg font-semibold text-blue-600">{fmt(entry.total_credit)}</div>
        </div>
      </div>

      {/* Description */}
      {entry.description && (
        <div className="bg-white p-4 rounded-lg border border-borderColor mb-6">
          <div className="flex items-center gap-2 text-sm text-textSecondary mb-2">
            <FontAwesomeIcon icon={faInfoCircle} />
            Libelle
          </div>
          <p className="text-sm text-textPrimary">{entry.description}</p>
        </div>
      )}

      {/* Lines Table */}
      <div className="bg-white rounded-xl border border-borderColor overflow-hidden">
        <div className="px-4 py-3 border-b border-borderColor bg-gray-50">
          <h2 className="text-sm font-semibold text-textPrimary">Lignes d'ecriture</h2>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-borderColor">
              <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">N°</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Compte</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Libelle</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Debit</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Credit</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-textSecondary uppercase">TVA</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-textSecondary uppercase">Lettrage</th>
            </tr>
          </thead>
          <tbody>
            {(entry.lines || []).map((line: any) => (
              <tr key={line.id} className="border-b border-borderColor hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-textSecondary">{line.line_number}</td>
                <td className="px-4 py-3">
                  <div className="text-sm font-mono font-medium text-primary">{line.account_code}</div>
                  <div className="text-xs text-textSecondary">{line.account_name}</div>
                </td>
                <td className="px-4 py-3 text-sm text-textPrimary">{line.label}</td>
                <td className="px-4 py-3 text-sm text-right font-medium">
                  {Number(line.debit) > 0 ? fmt(line.debit) : ''}
                </td>
                <td className="px-4 py-3 text-sm text-right font-medium">
                  {Number(line.credit) > 0 ? fmt(line.credit) : ''}
                </td>
                <td className="px-4 py-3 text-center text-xs">
                  {line.vat_rate ? `${line.vat_rate}%` : ''}
                </td>
                <td className="px-4 py-3 text-center">
                  {line.lettering_code && (
                    <span className="inline-flex px-2 py-0.5 rounded bg-purple-50 text-purple-700 text-xs font-medium">
                      {line.lettering_code}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="bg-gray-50 font-semibold">
              <td colSpan={3} className="px-4 py-3 text-sm">TOTAUX</td>
              <td className="px-4 py-3 text-sm text-right">{fmt(entry.total_debit)}</td>
              <td className="px-4 py-3 text-sm text-right">{fmt(entry.total_credit)}</td>
              <td colSpan={2} className="px-4 py-3 text-center">
                {entry.is_balanced ? (
                  <span className="text-green-600 text-xs">Equilibre</span>
                ) : (
                  <span className="text-red-600 text-xs">Desequilibre</span>
                )}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Source info */}
      {entry.source_type && (
        <div className="mt-4 text-xs text-textSecondary">
          Source: {entry.source_type} {entry.source_id ? `(${entry.source_id})` : ''}
        </div>
      )}
    </div>
  )
}

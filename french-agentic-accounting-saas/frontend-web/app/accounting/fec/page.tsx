'use client'

import { useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faFileExport,
  faArrowLeft,
  faDownload,
  faSpinner,
} from '@fortawesome/free-solid-svg-icons'
import Link from 'next/link'
import { accountingAPI } from '@/lib/api'

export default function FECExportPage() {
  const [fiscalYear, setFiscalYear] = useState(new Date().getFullYear())
  const [siren, setSiren] = useState('')
  const [exporting, setExporting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  async function handleExport() {
    if (!siren || siren.length !== 9) {
      setError('Le SIREN doit contenir exactement 9 chiffres')
      return
    }
    setExporting(true)
    setError('')
    setSuccess(false)
    try {
      const blob = await accountingAPI.exportFEC(fiscalYear, siren)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${siren}FEC${fiscalYear}1231.txt`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      setSuccess(true)
    } catch (err: any) {
      setError(err?.message || "Erreur lors de l'export FEC")
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="p-6 max-w-[800px] mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/accounting" className="text-textSecondary hover:text-textPrimary">
          <FontAwesomeIcon icon={faArrowLeft} />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-textPrimary flex items-center gap-3">
            <FontAwesomeIcon icon={faFileExport} className="text-primary" />
            Export FEC
          </h1>
          <p className="text-sm text-textSecondary mt-1">
            Fichier des Ecritures Comptables - Article A47 A-1
          </p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-borderColor p-6">
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-textPrimary mb-2">
              Exercice fiscal
            </label>
            <select
              value={fiscalYear}
              onChange={(e) => setFiscalYear(Number(e.target.value))}
              className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm"
            >
              {[2026, 2025, 2024, 2023].map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-textPrimary mb-2">
              SIREN de l'entreprise
            </label>
            <input
              type="text"
              value={siren}
              onChange={(e) => setSiren(e.target.value.replace(/\D/g, '').slice(0, 9))}
              placeholder="123456789"
              maxLength={9}
              className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm"
            />
            <p className="text-xs text-textSecondary mt-1">9 chiffres</p>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          {success && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
              FEC exporte avec succes
            </div>
          )}

          <button
            onClick={handleExport}
            disabled={exporting || !siren}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
          >
            <FontAwesomeIcon icon={exporting ? faSpinner : faDownload} spin={exporting} />
            {exporting ? 'Export en cours...' : 'Telecharger le FEC'}
          </button>
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="text-sm font-medium text-blue-900 mb-2">Format FEC</h3>
          <ul className="text-xs text-blue-800 space-y-1">
            <li>Format: fichier texte tabule (TSV), encodage UTF-8</li>
            <li>18 colonnes conformes a l'article A47 A-1 du LPF</li>
            <li>Seules les ecritures validees ou comptabilisees sont incluses</li>
            <li>Nom du fichier: {siren || 'XXXXXXXXX'}FEC{fiscalYear}1231.txt</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

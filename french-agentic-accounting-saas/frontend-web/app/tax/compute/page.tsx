'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faCalculator, faSpinner } from '@fortawesome/free-solid-svg-icons'
import Link from 'next/link'
import { taxAPI } from '@/lib/api'

export default function ComputeDeclarationPage() {
  const router = useRouter()
  const [type, setType] = useState('CA3')
  const [periodStart, setPeriodStart] = useState('')
  const [periodEnd, setPeriodEnd] = useState('')
  const [computing, setComputing] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<any>(null)

  async function handleCompute() {
    if (!periodStart || !periodEnd) {
      setError('Veuillez saisir les dates de debut et fin de periode')
      return
    }
    setComputing(true)
    setError('')
    try {
      const res = await taxAPI.computeDeclaration({
        type, period_start: periodStart, period_end: periodEnd,
      })
      setResult(res)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Erreur lors du calcul')
    } finally {
      setComputing(false)
    }
  }

  const fmt = (n: string | number) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(Number(n))

  return (
    <div className="p-6 max-w-[800px] mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/tax" className="text-textSecondary hover:text-textPrimary"><FontAwesomeIcon icon={faArrowLeft} /></Link>
        <div>
          <h1 className="text-xl font-bold text-textPrimary">Calculer une declaration</h1>
          <p className="text-sm text-textSecondary mt-1">Generer une declaration a partir des ecritures comptables</p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-borderColor p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Type de declaration</label>
          <select value={type} onChange={(e) => setType(e.target.value)}
            className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm">
            <option value="CA3">TVA mensuelle (CA3)</option>
            <option value="CA12">TVA annuelle (CA12)</option>
            <option value="IS">Impot sur les societes</option>
          </select>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Debut de periode</label>
            <input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)}
              className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Fin de periode</label>
            <input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)}
              className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" />
          </div>
        </div>

        {error && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>}

        <button onClick={handleCompute} disabled={computing}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-white rounded-lg text-sm font-medium disabled:opacity-50">
          <FontAwesomeIcon icon={computing ? faSpinner : faCalculator} spin={computing} />
          {computing ? 'Calcul en cours...' : 'Calculer'}
        </button>
      </div>

      {/* Result */}
      {result && result.computed_data && (
        <div className="mt-6 bg-white rounded-xl border border-borderColor p-6">
          <h2 className="text-lg font-bold mb-4">Resultat - {type}</h2>
          <div className="space-y-4">
            {type === 'CA3' && (
              <>
                <div>
                  <h3 className="text-sm font-semibold text-textSecondary mb-2">TVA Collectee</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <span className="text-textSecondary">TVA 20%</span><span className="text-right">{fmt(result.computed_data.collected_vat_20)}</span>
                    <span className="text-textSecondary">TVA 10%</span><span className="text-right">{fmt(result.computed_data.collected_vat_10)}</span>
                    <span className="text-textSecondary">TVA 5.5%</span><span className="text-right">{fmt(result.computed_data.collected_vat_55)}</span>
                    <span className="text-textSecondary">TVA 2.1%</span><span className="text-right">{fmt(result.computed_data.collected_vat_21)}</span>
                    <span className="font-semibold">Total collectee</span><span className="text-right font-semibold">{fmt(result.computed_data.total_collected)}</span>
                  </div>
                </div>
                <div className="border-t pt-4">
                  <h3 className="text-sm font-semibold text-textSecondary mb-2">TVA Deductible</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <span className="text-textSecondary">Sur biens et services</span><span className="text-right">{fmt(result.computed_data.deductible_vat_goods)}</span>
                    <span className="text-textSecondary">Sur immobilisations</span><span className="text-right">{fmt(result.computed_data.deductible_vat_immobilisations)}</span>
                    <span className="font-semibold">Total deductible</span><span className="text-right font-semibold">{fmt(result.computed_data.total_deductible)}</span>
                  </div>
                </div>
                <div className="border-t pt-4 bg-gray-50 -mx-6 px-6 py-4 rounded-b-xl">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {Number(result.computed_data.vat_due) > 0 && (
                      <><span className="font-bold text-red-700">TVA nette a payer</span><span className="text-right font-bold text-red-700">{fmt(result.computed_data.vat_due)}</span></>
                    )}
                    {Number(result.computed_data.credit_vat) > 0 && (
                      <><span className="font-bold text-green-700">Credit de TVA</span><span className="text-right font-bold text-green-700">{fmt(result.computed_data.credit_vat)}</span></>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
          <div className="mt-4 flex justify-end">
            <Link href={`/tax/declarations/${result.id}`} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">
              Voir la declaration
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

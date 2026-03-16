'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faCheck, faFileInvoiceDollar } from '@fortawesome/free-solid-svg-icons'
import Link from 'next/link'
import { taxAPI } from '@/lib/api'

const TYPE_LABELS: Record<string, string> = {
  CA3: 'TVA mensuelle (CA3)', CA12: 'TVA annuelle (CA12)', IS: 'Impot sur les societes',
  CVAE: 'CVAE', CFE: 'CFE', DAS2: 'DAS2',
}
const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800', computed: 'bg-blue-100 text-blue-800',
  validated: 'bg-green-100 text-green-800', submitted: 'bg-purple-100 text-purple-800',
}
const STATUS_LABELS: Record<string, string> = {
  draft: 'Brouillon', computed: 'Calculee', validated: 'Validee', submitted: 'Deposee',
}

export default function DeclarationDetailPage() {
  const params = useParams()
  const id = params.id as string
  const [decl, setDecl] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [validating, setValidating] = useState(false)

  useEffect(() => { loadDeclaration() }, [id])

  async function loadDeclaration() {
    setLoading(true)
    try {
      const res = await taxAPI.getDeclaration(id)
      setDecl(res)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  async function handleValidate() {
    setValidating(true)
    try {
      await taxAPI.validateDeclaration(id)
      await loadDeclaration()
    } catch (err) { console.error(err) }
    finally { setValidating(false) }
  }

  const fmt = (n: string | number) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(Number(n))

  if (loading) return <div className="p-6 text-center text-textSecondary">Chargement...</div>
  if (!decl) return <div className="p-6 text-center text-textSecondary">Declaration non trouvee. <Link href="/tax" className="text-primary">Retour</Link></div>

  const status = STATUS_COLORS[decl.status] || 'bg-gray-100'

  return (
    <div className="p-6 max-w-[1000px] mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link href="/tax" className="text-textSecondary hover:text-textPrimary"><FontAwesomeIcon icon={faArrowLeft} /></Link>
          <div>
            <h1 className="text-xl font-bold text-textPrimary flex items-center gap-3">
              <FontAwesomeIcon icon={faFileInvoiceDollar} className="text-primary" />
              {TYPE_LABELS[decl.type] || decl.type}
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${status}`}>{STATUS_LABELS[decl.status] || decl.status}</span>
            </h1>
            <p className="text-sm text-textSecondary mt-1">
              Periode: {new Date(decl.period_start).toLocaleDateString('fr-FR')} - {new Date(decl.period_end).toLocaleDateString('fr-FR')}
            </p>
          </div>
        </div>
        {decl.status === 'computed' && (
          <button onClick={handleValidate} disabled={validating}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">
            <FontAwesomeIcon icon={faCheck} /> {validating ? 'Validation...' : 'Valider'}
          </button>
        )}
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg border border-borderColor">
          <div className="text-xs text-textSecondary uppercase mb-1">Montant net</div>
          <div className={`text-2xl font-bold ${Number(decl.total_amount) >= 0 ? 'text-red-600' : 'text-green-600'}`}>{fmt(decl.total_amount)}</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-borderColor">
          <div className="text-xs text-textSecondary uppercase mb-1">Echeance</div>
          <div className="text-lg font-semibold">{decl.due_date ? new Date(decl.due_date).toLocaleDateString('fr-FR') : '-'}</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-borderColor">
          <div className="text-xs text-textSecondary uppercase mb-1">Type</div>
          <div className="text-lg font-semibold">{decl.type}</div>
        </div>
      </div>

      {/* Computed data */}
      {decl.computed_data && decl.type === 'CA3' && (
        <div className="bg-white rounded-xl border border-borderColor p-6">
          <h2 className="text-sm font-semibold mb-4">Detail du calcul CA3</h2>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-textSecondary">TVA collectee 20%</span><span className="text-right">{fmt(decl.computed_data.collected_vat_20)}</span>
              <span className="text-textSecondary">TVA collectee 10%</span><span className="text-right">{fmt(decl.computed_data.collected_vat_10)}</span>
              <span className="text-textSecondary">TVA collectee 5.5%</span><span className="text-right">{fmt(decl.computed_data.collected_vat_55)}</span>
              <span className="text-textSecondary">TVA collectee 2.1%</span><span className="text-right">{fmt(decl.computed_data.collected_vat_21)}</span>
              <span className="font-semibold border-t pt-2">Total collectee</span><span className="text-right font-semibold border-t pt-2">{fmt(decl.computed_data.total_collected)}</span>
            </div>
            <div className="border-t pt-3 grid grid-cols-2 gap-2 text-sm">
              <span className="text-textSecondary">TVA deductible (biens/services)</span><span className="text-right">{fmt(decl.computed_data.deductible_vat_goods)}</span>
              <span className="text-textSecondary">TVA deductible (immobilisations)</span><span className="text-right">{fmt(decl.computed_data.deductible_vat_immobilisations)}</span>
              <span className="font-semibold border-t pt-2">Total deductible</span><span className="text-right font-semibold border-t pt-2">{fmt(decl.computed_data.total_deductible)}</span>
            </div>
            <div className="border-t pt-3 bg-gray-50 -mx-6 px-6 py-3 rounded-b-xl">
              <div className="grid grid-cols-2 gap-2 text-sm font-bold">
                <span>TVA nette</span><span className="text-right">{fmt(decl.computed_data.net_amount)}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

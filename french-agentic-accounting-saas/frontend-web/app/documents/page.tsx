'use client'
import { useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faInbox, faUpload, faFileAlt, faCheck } from '@fortawesome/free-solid-svg-icons'
import { collectionAPI } from '@/lib/api'

const ROUTE_LABELS: Record<string, string> = {
  einvoice_service: 'Facturation', banking_service: 'Banque', payroll_service: 'Paie',
  expense: 'Depenses', dossier_service: 'Dossier', tax_service: 'Fiscalite',
}

export default function DocumentsPage() {
  const [textContent, setTextContent] = useState('')
  const [filename, setFilename] = useState('')
  const [result, setResult] = useState<any>(null)
  const [classifying, setClassifying] = useState(false)

  async function handleClassify() {
    if (!textContent) return
    setClassifying(true)
    try {
      const res = await collectionAPI.classify({ text_content: textContent, filename })
      setResult(res)
    } catch (err) { console.error(err) }
    finally { setClassifying(false) }
  }

  return (
    <div className="p-6 max-w-[1000px] mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-textPrimary">Collecte de documents</h1>
        <p className="text-sm text-textSecondary mt-1">Classification automatique et routage</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-borderColor p-6">
          <h2 className="text-sm font-semibold mb-4">Document a classifier</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium mb-1">Nom du fichier</label>
              <input type="text" value={filename} onChange={(e) => setFilename(e.target.value)} placeholder="facture_2026.pdf"
                className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Contenu texte (OCR)</label>
              <textarea rows={10} value={textContent} onChange={(e) => setTextContent(e.target.value)} placeholder="Collez le texte extrait du document..."
                className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm resize-none" />
            </div>
            <button onClick={handleClassify} disabled={classifying || !textContent}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm disabled:opacity-50">
              <FontAwesomeIcon icon={faFileAlt} /> {classifying ? 'Classification...' : 'Classifier'}
            </button>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-borderColor p-6">
          <h2 className="text-sm font-semibold mb-4">Resultat</h2>
          {!result ? (
            <div className="text-center py-12 text-textSecondary">
              <FontAwesomeIcon icon={faInbox} className="text-3xl mb-3" />
              <p>Soumettez un document pour classification</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-green-50 rounded-lg p-4 text-center">
                <FontAwesomeIcon icon={faCheck} className="text-green-600 text-2xl mb-2" />
                <p className="font-semibold text-green-900 capitalize">{result.document_type.replace(/_/g, ' ')}</p>
                <p className="text-sm text-green-700">Confiance: {(result.confidence * 100).toFixed(0)}%</p>
              </div>
              {result.route && (
                <div className="text-sm"><span className="text-textSecondary">Routage:</span> <span className="font-medium">{ROUTE_LABELS[result.route] || result.route}</span></div>
              )}
              {result.alternatives?.length > 0 && (
                <div>
                  <p className="text-xs text-textSecondary mb-1">Alternatives:</p>
                  {result.alternatives.map((a: any, i: number) => (
                    <p key={i} className="text-xs text-textMuted capitalize">{a.type.replace(/_/g, ' ')} (score: {a.score})</p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

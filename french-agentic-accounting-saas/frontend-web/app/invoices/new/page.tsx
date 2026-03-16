'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft, faPlus, faTrash, faSave } from '@fortawesome/free-solid-svg-icons'
import Link from 'next/link'
import { einvoiceAPI } from '@/lib/api'

export default function NewInvoicePage() {
  const router = useRouter()
  const [form, setForm] = useState({ recipient_name: '', recipient_siren: '', recipient_vat_number: '', issue_date: '', due_date: '', notes: '' })
  const [lines, setLines] = useState([{ description: '', quantity: '1', unit_price: '', vat_rate: '20', account_code: '' }])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  function addLine() { setLines([...lines, { description: '', quantity: '1', unit_price: '', vat_rate: '20', account_code: '' }]) }
  function removeLine(i: number) { setLines(lines.filter((_, idx) => idx !== i)) }
  function updateLine(i: number, field: string, value: string) {
    const updated = [...lines]; (updated[i] as any)[field] = value; setLines(updated)
  }

  async function handleSave() {
    if (!form.recipient_name || !form.issue_date || lines.length === 0) { setError('Champs obligatoires manquants'); return }
    setSaving(true); setError('')
    try {
      const payload = { ...form, type: 'sent', lines: lines.map(l => ({ description: l.description, quantity: Number(l.quantity), unit_price: Number(l.unit_price), vat_rate: Number(l.vat_rate), account_code: l.account_code || undefined })) }
      await einvoiceAPI.create(payload)
      router.push('/invoices')
    } catch (err: any) { setError(err?.response?.data?.detail || 'Erreur') }
    finally { setSaving(false) }
  }

  return (
    <div className="p-6 max-w-[900px] mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/invoices" className="text-textSecondary hover:text-textPrimary"><FontAwesomeIcon icon={faArrowLeft} /></Link>
        <h1 className="text-xl font-bold text-textPrimary">Nouvelle facture</h1>
      </div>
      <div className="bg-white rounded-xl border border-borderColor p-6 space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium mb-1">Destinataire *</label>
            <input type="text" value={form.recipient_name} onChange={(e) => setForm({...form, recipient_name: e.target.value})} className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" /></div>
          <div><label className="block text-sm font-medium mb-1">SIREN</label>
            <input type="text" value={form.recipient_siren} onChange={(e) => setForm({...form, recipient_siren: e.target.value})} maxLength={9} className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" /></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium mb-1">Date emission *</label>
            <input type="date" value={form.issue_date} onChange={(e) => setForm({...form, issue_date: e.target.value})} className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" /></div>
          <div><label className="block text-sm font-medium mb-1">Date echeance</label>
            <input type="date" value={form.due_date} onChange={(e) => setForm({...form, due_date: e.target.value})} className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" /></div>
        </div>
        <div>
          <div className="flex items-center justify-between mb-2"><h3 className="text-sm font-semibold">Lignes</h3>
            <button onClick={addLine} className="text-xs text-primary hover:underline flex items-center gap-1"><FontAwesomeIcon icon={faPlus} /> Ajouter</button></div>
          <div className="space-y-2">
            {lines.map((l, i) => (
              <div key={i} className="grid grid-cols-12 gap-2 items-end">
                <div className="col-span-4"><input placeholder="Description" value={l.description} onChange={(e) => updateLine(i, 'description', e.target.value)} className="w-full px-2 py-1.5 border border-borderColor rounded text-sm" /></div>
                <div className="col-span-2"><input type="number" placeholder="Qte" value={l.quantity} onChange={(e) => updateLine(i, 'quantity', e.target.value)} className="w-full px-2 py-1.5 border border-borderColor rounded text-sm" /></div>
                <div className="col-span-2"><input type="number" placeholder="PU HT" value={l.unit_price} onChange={(e) => updateLine(i, 'unit_price', e.target.value)} className="w-full px-2 py-1.5 border border-borderColor rounded text-sm" /></div>
                <div className="col-span-2"><select value={l.vat_rate} onChange={(e) => updateLine(i, 'vat_rate', e.target.value)} className="w-full px-2 py-1.5 border border-borderColor rounded text-sm">
                  <option value="20">20%</option><option value="10">10%</option><option value="5.5">5.5%</option><option value="0">0%</option></select></div>
                <div className="col-span-2 flex justify-end">
                  {lines.length > 1 && <button onClick={() => removeLine(i)} className="text-red-500 hover:text-red-700"><FontAwesomeIcon icon={faTrash} /></button>}
                </div>
              </div>
            ))}
          </div>
        </div>
        {error && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>}
        <button onClick={handleSave} disabled={saving} className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-white rounded-lg text-sm font-medium disabled:opacity-50">
          <FontAwesomeIcon icon={faSave} /> {saving ? 'Enregistrement...' : 'Creer la facture'}
        </button>
      </div>
    </div>
  )
}

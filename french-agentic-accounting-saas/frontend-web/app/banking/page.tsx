'use client'

import { useState, useEffect } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faUniversity,
  faPlus,
  faSync,
  faChevronRight,
  faArrowUp,
  faArrowDown,
} from '@fortawesome/free-solid-svg-icons'
import Link from 'next/link'
import { bankingAPI } from '@/lib/api'

export default function BankingPage() {
  const [accounts, setAccounts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ account_name: '', iban: '', bic: '', bank_name: '', pcg_account_code: '512000' })

  useEffect(() => { loadAccounts() }, [])

  async function loadAccounts() {
    setLoading(true)
    try {
      const res = await bankingAPI.listAccounts()
      setAccounts(res.data || [])
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  async function handleCreate() {
    try {
      await bankingAPI.createAccount(form)
      setShowCreate(false)
      setForm({ account_name: '', iban: '', bic: '', bank_name: '', pcg_account_code: '512000' })
      loadAccounts()
    } catch (err) { console.error(err) }
  }

  const fmt = (n: number) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n)
  const totalBalance = accounts.reduce((sum, a) => sum + Number(a.balance || 0), 0)

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-textPrimary">Banque</h1>
          <p className="text-sm text-textSecondary mt-1">Comptes bancaires et rapprochement</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary/90">
          <FontAwesomeIcon icon={faPlus} /> Ajouter un compte
        </button>
      </div>

      {/* Total balance card */}
      <div className="bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-xl p-6 text-white mb-6">
        <p className="text-sm opacity-80">Solde total</p>
        <p className="text-3xl font-bold mt-1">{fmt(totalBalance)}</p>
        <p className="text-sm opacity-70 mt-1">{accounts.length} compte{accounts.length !== 1 ? 's' : ''} actif{accounts.length !== 1 ? 's' : ''}</p>
      </div>

      {/* Accounts */}
      {loading ? (
        <div className="text-center py-12 text-textSecondary">Chargement...</div>
      ) : accounts.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-borderColor">
          <FontAwesomeIcon icon={faUniversity} className="text-4xl text-textMuted mb-3" />
          <p className="text-textSecondary">Aucun compte bancaire</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {accounts.map((a) => (
            <Link key={a.id} href={`/banking/reconciliation?account=${a.id}`} className="bg-white rounded-xl border border-borderColor p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                    <FontAwesomeIcon icon={faUniversity} className="text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-textPrimary text-sm">{a.account_name}</h3>
                    {a.bank_name && <p className="text-xs text-textSecondary">{a.bank_name}</p>}
                  </div>
                </div>
                <FontAwesomeIcon icon={faChevronRight} className="text-textMuted text-xs" />
              </div>
              <div className="text-xl font-bold text-textPrimary mb-2">{fmt(a.balance)}</div>
              {a.iban && <p className="text-xs text-textSecondary font-mono">{a.iban.replace(/(.{4})/g, '$1 ').trim()}</p>}
              <div className="flex items-center justify-between mt-3 pt-3 border-t border-borderColor">
                <span className="text-xs text-textSecondary">PCG: {a.pcg_account_code}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${a.connection_type === 'api' ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                  {a.connection_type === 'api' ? 'Connecte' : 'Manuel'}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg">
            <h2 className="text-lg font-bold mb-4">Nouveau compte bancaire</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Nom du compte *</label>
                <input type="text" value={form.account_name} onChange={(e) => setForm({...form, account_name: e.target.value})}
                  className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Banque</label>
                <input type="text" value={form.bank_name} onChange={(e) => setForm({...form, bank_name: e.target.value})}
                  className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-1">IBAN</label>
                  <input type="text" value={form.iban} onChange={(e) => setForm({...form, iban: e.target.value.toUpperCase().replace(/\s/g, '')})}
                    className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm font-mono" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">BIC</label>
                  <input type="text" value={form.bic} onChange={(e) => setForm({...form, bic: e.target.value.toUpperCase()})}
                    maxLength={11} className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm font-mono" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Compte PCG</label>
                <input type="text" value={form.pcg_account_code} onChange={(e) => setForm({...form, pcg_account_code: e.target.value})}
                  className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 border border-borderColor rounded-lg text-sm">Annuler</button>
              <button onClick={handleCreate} disabled={!form.account_name} className="px-4 py-2 bg-primary text-white rounded-lg text-sm disabled:opacity-50">Creer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

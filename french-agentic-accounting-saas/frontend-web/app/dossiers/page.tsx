'use client'

import { useState, useEffect } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faFolderOpen,
  faPlus,
  faSearch,
  faBuilding,
  faChevronLeft,
  faChevronRight,
  faEllipsisV,
} from '@fortawesome/free-solid-svg-icons'
import Link from 'next/link'
import { dossierAPI } from '@/lib/api'

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-100 text-green-800',
  archived: 'bg-gray-100 text-gray-800',
  suspended: 'bg-red-100 text-red-800',
}

const REGIME_LABELS: Record<string, string> = {
  reel_normal: 'Reel normal',
  reel_simplifie: 'Reel simplifie',
  mini_reel: 'Mini-reel',
  franchise: 'Franchise de TVA',
}

export default function DossiersPage() {
  const [dossiers, setDossiers] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [form, setForm] = useState({ client_name: '', siren: '', siret: '', legal_form: '', regime_tva: 'reel_normal', email: '', phone: '', city: '' })

  useEffect(() => {
    loadDossiers()
  }, [page, statusFilter])

  async function loadDossiers() {
    setLoading(true)
    try {
      const params: any = { page, page_size: pageSize }
      if (statusFilter) params.status = statusFilter
      if (search) params.search = search
      const res = await dossierAPI.list(params)
      setDossiers(res.data || [])
      setTotal(res.total || 0)
    } catch (err) {
      console.error('Failed to load dossiers', err)
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate() {
    try {
      await dossierAPI.create(form)
      setShowCreateModal(false)
      setForm({ client_name: '', siren: '', siret: '', legal_form: '', regime_tva: 'reel_normal', email: '', phone: '', city: '' })
      loadDossiers()
    } catch (err) {
      console.error('Failed to create dossier', err)
    }
  }

  function handleSearch() {
    setPage(1)
    loadDossiers()
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-textPrimary">Dossiers Clients</h1>
          <p className="text-sm text-textSecondary mt-1">Gestion des dossiers comptables</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary/90"
        >
          <FontAwesomeIcon icon={faPlus} />
          Nouveau dossier
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <div className="flex-1 relative">
          <FontAwesomeIcon icon={faSearch} className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary text-sm" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Rechercher par nom ou SIREN..."
            className="w-full pl-9 pr-4 py-2 border border-borderColor rounded-lg text-sm"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          className="px-3 py-2 border border-borderColor rounded-lg text-sm"
        >
          <option value="">Tous les statuts</option>
          <option value="active">Actif</option>
          <option value="archived">Archive</option>
          <option value="suspended">Suspendu</option>
        </select>
      </div>

      {/* Dossier Cards */}
      {loading ? (
        <div className="text-center py-12 text-textSecondary">Chargement...</div>
      ) : dossiers.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-borderColor">
          <FontAwesomeIcon icon={faFolderOpen} className="text-4xl text-textMuted mb-3" />
          <p className="text-textSecondary">Aucun dossier trouve</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {dossiers.map((d) => (
            <Link
              key={d.id}
              href={`/dossiers/${d.id}`}
              className="bg-white rounded-xl border border-borderColor p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-indigo-50 rounded-lg flex items-center justify-center">
                    <FontAwesomeIcon icon={faBuilding} className="text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-textPrimary text-sm">{d.client_name}</h3>
                    {d.siren && <p className="text-xs text-textSecondary">SIREN: {d.siren}</p>}
                  </div>
                </div>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[d.status] || 'bg-gray-100'}`}>
                  {d.status === 'active' ? 'Actif' : d.status === 'archived' ? 'Archive' : 'Suspendu'}
                </span>
              </div>
              <div className="space-y-1 text-xs text-textSecondary">
                {d.legal_form && <p>Forme: {d.legal_form}</p>}
                {d.regime_tva && <p>TVA: {REGIME_LABELS[d.regime_tva] || d.regime_tva}</p>}
                {d.city && <p>{d.city}{d.postal_code ? ` (${d.postal_code})` : ''}</p>}
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-6">
          <span className="text-sm text-textSecondary">{total} dossiers</span>
          <div className="flex gap-2">
            <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1 border rounded text-sm disabled:opacity-50">
              <FontAwesomeIcon icon={faChevronLeft} />
            </button>
            <span className="px-3 py-1 text-sm">Page {page} / {totalPages}</span>
            <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="px-3 py-1 border rounded text-sm disabled:opacity-50">
              <FontAwesomeIcon icon={faChevronRight} />
            </button>
          </div>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold mb-4">Nouveau dossier</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Nom du client *</label>
                <input type="text" value={form.client_name} onChange={(e) => setForm({...form, client_name: e.target.value})}
                  className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-1">SIREN</label>
                  <input type="text" value={form.siren} onChange={(e) => setForm({...form, siren: e.target.value.replace(/\D/g, '').slice(0, 9)})}
                    maxLength={9} className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Forme juridique</label>
                  <select value={form.legal_form} onChange={(e) => setForm({...form, legal_form: e.target.value})}
                    className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm">
                    <option value="">--</option>
                    <option value="SARL">SARL</option>
                    <option value="SAS">SAS</option>
                    <option value="SASU">SASU</option>
                    <option value="SA">SA</option>
                    <option value="EI">EI</option>
                    <option value="EURL">EURL</option>
                    <option value="SCI">SCI</option>
                    <option value="AUTO">Auto-entrepreneur</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Regime TVA</label>
                <select value={form.regime_tva} onChange={(e) => setForm({...form, regime_tva: e.target.value})}
                  className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm">
                  <option value="reel_normal">Reel normal</option>
                  <option value="reel_simplifie">Reel simplifie</option>
                  <option value="mini_reel">Mini-reel</option>
                  <option value="franchise">Franchise de TVA</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-1">Email</label>
                  <input type="email" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})}
                    className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Ville</label>
                  <input type="text" value={form.city} onChange={(e) => setForm({...form, city: e.target.value})}
                    className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button onClick={() => setShowCreateModal(false)} className="px-4 py-2 border border-borderColor rounded-lg text-sm">Annuler</button>
              <button onClick={handleCreate} disabled={!form.client_name} className="px-4 py-2 bg-primary text-white rounded-lg text-sm disabled:opacity-50">Creer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

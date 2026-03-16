'use client'

import { useState, useEffect } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faChartLine,
  faGauge,
  faChartBar,
  faChartArea,
  faSync,
} from '@fortawesome/free-solid-svg-icons'
import { analysisAPI } from '@/lib/api'

type TabView = 'sig' | 'ratios' | 'scoring' | 'forecast'

export default function AnalysisPage() {
  const [tab, setTab] = useState<TabView>('sig')
  const [fiscalYear, setFiscalYear] = useState(new Date().getFullYear())
  const [sig, setSig] = useState<any>(null)
  const [ratios, setRatios] = useState<any>(null)
  const [scoring, setScoring] = useState<any>(null)
  const [forecast, setForecast] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (tab === 'sig') loadSIG()
    if (tab === 'ratios') loadRatios()
    if (tab === 'scoring') loadScoring()
    if (tab === 'forecast') loadForecast()
  }, [tab, fiscalYear])

  async function loadSIG() {
    setLoading(true)
    try { setSig(await analysisAPI.getSIG(fiscalYear)) } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }
  async function loadRatios() {
    setLoading(true)
    try { setRatios(await analysisAPI.getRatios(fiscalYear)) } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }
  async function loadScoring() {
    setLoading(true)
    try { setScoring(await analysisAPI.getScoring(fiscalYear)) } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }
  async function loadForecast() {
    setLoading(true)
    try { setForecast(await analysisAPI.createForecast(30)) } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  const fmt = (n: string | number | null | undefined) => {
    if (n === null || n === undefined) return '-'
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(Number(n))
  }
  const pct = (n: string | number | null | undefined) => {
    if (n === null || n === undefined) return '-'
    return `${Number(n).toFixed(1)}%`
  }

  const scoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-blue-600'
    if (score >= 40) return 'text-yellow-600'
    return 'text-red-600'
  }

  const categoryLabel = (cat: string) => {
    const labels: Record<string, string> = {
      excellent: 'Excellent', good: 'Bon', average: 'Moyen', weak: 'Faible', critical: 'Critique'
    }
    return labels[cat] || cat
  }

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-textPrimary">Analyse financiere</h1>
          <p className="text-sm text-textSecondary mt-1">SIG, ratios, scoring et previsions</p>
        </div>
        <select value={fiscalYear} onChange={(e) => setFiscalYear(Number(e.target.value))}
          className="px-3 py-2 border border-borderColor rounded-lg text-sm">
          {[2026, 2025, 2024, 2023].map(y => <option key={y} value={y}>{y}</option>)}
        </select>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {([
          { key: 'sig', icon: faChartBar, label: 'SIG' },
          { key: 'ratios', icon: faChartLine, label: 'Ratios' },
          { key: 'scoring', icon: faGauge, label: 'Score' },
          { key: 'forecast', icon: faChartArea, label: 'Previsions' },
        ] as const).map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === t.key ? 'bg-white shadow text-primary' : 'text-textSecondary hover:text-textPrimary'}`}>
            <FontAwesomeIcon icon={t.icon} className="mr-2" />{t.label}
          </button>
        ))}
      </div>

      {loading && <div className="text-center py-12 text-textSecondary">Chargement...</div>}

      {/* SIG Tab */}
      {!loading && tab === 'sig' && sig && (
        <div className="bg-white rounded-xl border border-borderColor p-6">
          <h2 className="text-sm font-semibold mb-4">Soldes Intermediaires de Gestion - {fiscalYear}</h2>
          <div className="space-y-3">
            {[
              { label: "Chiffre d'affaires", value: sig.chiffre_affaires, bg: 'bg-blue-50' },
              { label: 'Marge commerciale', value: sig.marge_commerciale },
              { label: 'Valeur ajoutee', value: sig.valeur_ajoutee, bg: 'bg-indigo-50' },
              { label: 'Excedent Brut d\'Exploitation (EBE)', value: sig.ebe, bg: 'bg-green-50' },
              { label: 'Resultat d\'exploitation', value: sig.resultat_exploitation },
              { label: 'Resultat financier', value: sig.resultat_financier },
              { label: 'Resultat courant', value: sig.resultat_courant, bg: 'bg-yellow-50' },
              { label: 'Resultat exceptionnel', value: sig.resultat_exceptionnel },
              { label: 'Resultat net', value: sig.resultat_net, bg: 'bg-green-100' },
            ].map((row, i) => (
              <div key={i} className={`flex items-center justify-between px-4 py-3 rounded-lg ${row.bg || ''}`}>
                <span className="text-sm text-textPrimary">{row.label}</span>
                <span className={`text-sm font-semibold ${Number(row.value) >= 0 ? 'text-green-700' : 'text-red-700'}`}>{fmt(row.value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Ratios Tab */}
      {!loading && tab === 'ratios' && ratios && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { label: 'BFR', value: fmt(ratios.bfr), desc: 'Besoin en Fonds de Roulement' },
            { label: 'Tresorerie nette', value: fmt(ratios.tresorerie_nette) },
            { label: 'Ratio endettement', value: ratios.ratio_endettement ? `${Number(ratios.ratio_endettement).toFixed(2)}x` : '-', desc: 'Dettes / Capitaux propres' },
            { label: 'Ratio liquidite', value: ratios.ratio_liquidite ? `${Number(ratios.ratio_liquidite).toFixed(2)}x` : '-', desc: 'Actif circulant / Passif court terme' },
            { label: 'Rotation stocks', value: ratios.rotation_stocks ? `${ratios.rotation_stocks}j` : '-' },
            { label: 'Delai clients', value: ratios.delai_clients ? `${ratios.delai_clients}j` : '-' },
            { label: 'Delai fournisseurs', value: ratios.delai_fournisseurs ? `${ratios.delai_fournisseurs}j` : '-' },
            { label: 'Marge nette', value: pct(ratios.marge_nette) },
            { label: 'Rentabilite capitaux', value: pct(ratios.rentabilite_capitaux) },
          ].map((r, i) => (
            <div key={i} className="bg-white rounded-xl border border-borderColor p-5">
              <div className="text-xs text-textSecondary uppercase mb-1">{r.label}</div>
              <div className="text-2xl font-bold text-textPrimary">{r.value}</div>
              {r.desc && <div className="text-xs text-textMuted mt-1">{r.desc}</div>}
            </div>
          ))}
        </div>
      )}

      {/* Scoring Tab */}
      {!loading && tab === 'scoring' && scoring && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-borderColor p-6 text-center">
            <div className={`text-6xl font-bold ${scoreColor(scoring.overall_score)}`}>{scoring.overall_score}</div>
            <div className="text-lg font-medium text-textPrimary mt-2">{categoryLabel(scoring.category)}</div>
            <div className="text-sm text-textSecondary mt-1">Score de sante financiere</div>
            <div className="mt-4 w-full bg-gray-200 rounded-full h-3">
              <div className={`h-3 rounded-full ${scoring.overall_score >= 60 ? 'bg-green-500' : scoring.overall_score >= 40 ? 'bg-yellow-500' : 'bg-red-500'}`}
                style={{ width: `${scoring.overall_score}%` }} />
            </div>
          </div>
          <div className="space-y-4">
            <div className="bg-white rounded-xl border border-borderColor p-5">
              <h3 className="text-sm font-semibold mb-3">Composantes</h3>
              {Object.entries(scoring.components || {}).map(([key, val]) => (
                <div key={key} className="flex items-center justify-between py-2 border-b last:border-0">
                  <span className="text-sm text-textPrimary capitalize">{key === 'profitability' ? 'Rentabilite' : key === 'liquidity' ? 'Liquidite' : key === 'solvency' ? 'Solvabilite' : 'Activite'}</span>
                  <span className="text-sm font-semibold">{val as number}/25</span>
                </div>
              ))}
            </div>
            {scoring.recommendations?.length > 0 && (
              <div className="bg-yellow-50 rounded-xl border border-yellow-200 p-5">
                <h3 className="text-sm font-semibold text-yellow-900 mb-2">Recommandations</h3>
                <ul className="space-y-2">
                  {scoring.recommendations.map((r: string, i: number) => (
                    <li key={i} className="text-sm text-yellow-800">{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Forecast Tab */}
      {!loading && tab === 'forecast' && (
        <div className="bg-white rounded-xl border border-borderColor p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold">Prevision de tresorerie - 30 jours</h2>
            <span className="text-xs text-textSecondary">
              Confiance: {forecast?.confidence ? `${(forecast.confidence * 100).toFixed(0)}%` : '-'}
            </span>
          </div>
          {!forecast || !forecast.data_points?.length ? (
            <div className="text-center py-12 text-textSecondary">Donnees insuffisantes pour les previsions</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left px-3 py-2 text-xs text-textSecondary">Date</th>
                    <th className="text-right px-3 py-2 text-xs text-textSecondary">Prevision</th>
                    <th className="text-right px-3 py-2 text-xs text-textSecondary">Borne basse</th>
                    <th className="text-right px-3 py-2 text-xs text-textSecondary">Borne haute</th>
                  </tr>
                </thead>
                <tbody>
                  {forecast.data_points.slice(0, 30).map((p: any, i: number) => (
                    <tr key={i} className="border-b hover:bg-gray-50">
                      <td className="px-3 py-2 text-sm">{new Date(p.date).toLocaleDateString('fr-FR')}</td>
                      <td className="px-3 py-2 text-sm text-right font-medium">{fmt(p.value)}</td>
                      <td className="px-3 py-2 text-sm text-right text-textSecondary">{fmt(p.lower_bound)}</td>
                      <td className="px-3 py-2 text-sm text-right text-textSecondary">{fmt(p.upper_bound)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

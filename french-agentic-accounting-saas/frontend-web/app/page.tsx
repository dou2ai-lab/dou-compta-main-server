'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faRobot,
  faChartLine,
  faFileInvoiceDollar,
  faBolt,
  faShieldHalved,
  faCloudArrowUp,
  faLink,
  faBrain,
  faArrowRight,
  faCheck,
  faStar,
  faEnvelope,
  faPhone,
  faLocationDot,
  faCalculator,
  faArrowDown,
  faPlay,
  faLock,
  faGlobe,
  faClock,
  faUsers,
  faBuilding,
  faChartBar,
  faGauge,
  faFileExport,
  faHandshake,
  faLightbulb,
  faWandMagicSparkles,
  faCircleCheck,
  faCoins,
  faMoneyBillTrendUp,
  faRocket,
  faMagnifyingGlass,
  faBell,
  faGears,
  faRepeat,
  faScaleBalanced,
} from '@fortawesome/free-solid-svg-icons';

/* ========================================================================== */
/*  Landing Page – DouCompta V4.0 – High-converting redesign                  */
/* ========================================================================== */

export default function LandingPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [dossiers, setDossiers] = useState(10);
  const [heures, setHeures] = useState(40);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [animatedStats, setAnimatedStats] = useState(false);
  const statsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Smooth-scroll polyfill for anchor clicks
    const handler = (e: MouseEvent) => {
      const target = (e.target as HTMLElement).closest('a[href^="#"]');
      if (!target) return;
      e.preventDefault();
      const id = (target as HTMLAnchorElement).getAttribute('href')!.slice(1);
      document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
    };
    document.addEventListener('click', handler);
    return () => document.removeEventListener('click', handler);
  }, []);

  // Animate stats when visible
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setAnimatedStats(true); },
      { threshold: 0.3 }
    );
    if (statsRef.current) observer.observe(statsRef.current);
    return () => observer.disconnect();
  }, []);

  const tempsGagne = Math.round(heures * 0.7 * dossiers / 10);
  const economie = Math.round(tempsGagne * 65 * 12);
  const roi = economie > 0 ? Math.max(1, Math.round((79 * 12) / economie * 12)) : 0;

  return (
    <div className="min-h-screen bg-white font-sans text-textPrimary overflow-x-hidden">
      {/* ================================================================ */}
      {/* NAV                                                              */}
      {/* ================================================================ */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-lg border-b border-borderColor">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <FontAwesomeIcon icon={faCalculator} className="text-white text-sm" />
            </div>
            <span className="text-xl font-bold text-primary">DouCompta</span>
            <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-semibold">V4</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-textSecondary">
            <a href="#agents" className="hover:text-primary transition-colors">Agents IA</a>
            <a href="#features" className="hover:text-primary transition-colors">Fonctionnalites</a>
            <a href="#pricing" className="hover:text-primary transition-colors">Tarifs</a>
            <a href="#testimonials" className="hover:text-primary transition-colors">Temoignages</a>
            <a href="#faq" className="hover:text-primary transition-colors">FAQ</a>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login" className="hidden sm:inline-flex text-sm font-medium text-textSecondary hover:text-primary transition-colors">
              Connexion
            </Link>
            <Link href="/login" className="inline-flex items-center gap-2 bg-primary hover:bg-primaryHover text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
              Commencer
              <FontAwesomeIcon icon={faArrowRight} className="text-xs" />
            </Link>
          </div>
        </div>
      </nav>

      {/* ================================================================ */}
      {/* HERO                                                             */}
      {/* ================================================================ */}
      <section className="relative min-h-screen flex items-center justify-center pt-16 overflow-hidden bg-gradient-to-br from-indigo-950 via-indigo-900 to-purple-900">
        {/* Floating decorative icons */}
        <div className="absolute inset-0 pointer-events-none select-none" aria-hidden="true">
          <div className="absolute top-[12%] left-[8%] animate-bounce text-white/5 text-7xl" style={{ animationDuration: '4s' }}>
            <FontAwesomeIcon icon={faFileInvoiceDollar} />
          </div>
          <div className="absolute top-[20%] right-[10%] animate-bounce text-white/5 text-6xl" style={{ animationDuration: '5s', animationDelay: '0.5s' }}>
            <FontAwesomeIcon icon={faChartLine} />
          </div>
          <div className="absolute bottom-[25%] left-[15%] animate-bounce text-white/5 text-8xl" style={{ animationDuration: '3.5s', animationDelay: '1s' }}>
            <FontAwesomeIcon icon={faRobot} />
          </div>
          <div className="absolute bottom-[35%] right-[6%] animate-bounce text-white/5 text-6xl" style={{ animationDuration: '6s', animationDelay: '0.2s' }}>
            <FontAwesomeIcon icon={faShieldHalved} />
          </div>
        </div>

        <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 text-center">
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white text-sm font-medium px-4 py-2 rounded-full mb-8 border border-white/10">
            <FontAwesomeIcon icon={faBolt} className="text-yellow-300" />
            Propulse par 15 agents IA autonomes
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white leading-tight mb-6">
            L&apos;IA qui fait votre comptabilite
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-yellow-200 via-pink-200 to-purple-200">
              pendant que vous developpez votre entreprise
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-indigo-200 max-w-3xl mx-auto mb-10 leading-relaxed">
            15 agents IA autonomes gerent votre comptabilite, declarations fiscales, rapprochement bancaire
            et facturation. 100% conforme DGFiP. Heberge en France.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <Link
              href="/login"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-white text-primary font-bold text-lg px-8 py-4 rounded-xl shadow-lg hover:shadow-xl hover:scale-105 transition-all"
            >
              Commencer gratuitement
              <FontAwesomeIcon icon={faArrowRight} />
            </Link>
            <a
              href="#demo"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 border-2 border-white/30 text-white font-semibold text-lg px-8 py-4 rounded-xl hover:bg-white/10 transition-all"
            >
              <FontAwesomeIcon icon={faPlay} className="text-sm" />
              Voir la demo
            </a>
          </div>

          {/* Stats row */}
          <div ref={statsRef} className="flex flex-wrap items-center justify-center gap-6 sm:gap-10 mb-16">
            {[
              { value: '98%', label: 'precision' },
              { value: '10x', label: 'plus rapide' },
              { value: '100%', label: 'souverain' },
              { value: '0', label: 'erreur FEC' },
            ].map((s, i) => (
              <div key={s.label} className={`text-center transition-all duration-700 ${animatedStats ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`} style={{ transitionDelay: `${i * 150}ms` }}>
                <p className="text-3xl sm:text-4xl font-extrabold text-white">{s.value}</p>
                <p className="text-indigo-300 text-sm font-medium">{s.label}</p>
              </div>
            ))}
          </div>

          {/* Floating agent activity cards */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            {[
              { agent: 'COMPTAA', msg: 'a genere 12 ecritures', bg: 'rgba(16,185,129,0.2)', text: '#6EE7B7', border: 'rgba(16,185,129,0.3)' },
              { agent: 'BANKA', msg: 'a rapproche 45 transactions', bg: 'rgba(59,130,246,0.2)', text: '#93C5FD', border: 'rgba(59,130,246,0.3)' },
              { agent: 'FISCA', msg: 'CA3 prete', bg: 'rgba(245,158,11,0.2)', text: '#FCD34D', border: 'rgba(245,158,11,0.3)' },
            ].map((c, i) => (
              <div key={c.agent} className="border backdrop-blur-sm rounded-lg px-4 py-2 text-sm font-medium animate-pulse" style={{ animationDuration: `${2 + i * 0.5}s`, backgroundColor: c.bg, color: c.text, borderColor: c.border }}>
                <span className="font-bold">{c.agent}</span> {c.msg}
              </div>
            ))}
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce text-white/40">
          <FontAwesomeIcon icon={faArrowDown} />
        </div>
      </section>

      {/* ================================================================ */}
      {/* PROBLEM / SOLUTION                                               */}
      {/* ================================================================ */}
      <section className="py-20 sm:py-28 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">
            {/* Problem */}
            <div>
              <p className="text-sm font-bold text-red-500 uppercase tracking-widest mb-3">Le probleme</p>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-textPrimary mb-8">La comptabilite manuelle vous ralentit</h2>
              <div className="space-y-4">
                {[
                  { icon: faClock, title: 'Saisie manuelle chronophage', desc: 'Des heures passees a saisir des ecritures qui pourraient etre automatisees.' },
                  { icon: faScaleBalanced, title: 'Erreurs comptables couteuses', desc: 'Les erreurs de saisie entrainent des anomalies FEC et des penalites fiscales.' },
                  { icon: faBell, title: 'Retards de declarations', desc: 'Les echeances fiscales manquees generent des majorations et interets de retard.' },
                ].map((p) => (
                  <div key={p.title} className="flex gap-4 p-4 bg-red-50 rounded-xl border border-red-200">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'rgba(239,68,68,0.1)', color: '#EF4444' }}>
                      <FontAwesomeIcon icon={p.icon} />
                    </div>
                    <div>
                      <h3 className="font-bold text-sm mb-1">{p.title}</h3>
                      <p className="text-sm text-textSecondary">{p.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Solution */}
            <div>
              <p className="text-sm font-bold text-green-500 uppercase tracking-widest mb-3">La solution DouCompta</p>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-textPrimary mb-8">L&apos;IA qui travaille pour vous</h2>
              <div className="space-y-4">
                {[
                  { icon: faWandMagicSparkles, title: 'Automatisation IA complete', desc: '15 agents autonomes qui saisissent, classifient et rapprochent sans intervention.' },
                  { icon: faCircleCheck, title: 'Precision de 98%', desc: 'Des ecritures conformes au PCG 2025, validees automatiquement avant generation.' },
                  { icon: faRocket, title: 'Declarations en 1 clic', desc: 'CA3, IS, CVAE calcules et prepares automatiquement, prets a tele-declarer.' },
                ].map((s) => (
                  <div key={s.title} className="flex gap-4 p-4 bg-green-50 rounded-xl border border-green-200">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'rgba(34,197,94,0.1)', color: '#22C55E' }}>
                      <FontAwesomeIcon icon={s.icon} />
                    </div>
                    <div>
                      <h3 className="font-bold text-sm mb-1">{s.title}</h3>
                      <p className="text-sm text-textSecondary">{s.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================================================================ */}
      {/* AI AGENTS                                                        */}
      {/* ================================================================ */}
      <section id="agents" className="py-20 sm:py-28 bg-bgPage">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <p className="text-sm font-bold text-primary uppercase tracking-widest mb-3">Votre equipe IA</p>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-textPrimary">15 Agents IA qui travaillent pour vous, 24h/24</h2>
            <p className="mt-4 text-textSecondary max-w-2xl mx-auto">
              Chaque agent est specialise dans un domaine comptable precis et collabore avec les autres pour une automatisation de bout en bout.
            </p>
          </div>

          {/* Visual flow */}
          <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-4 mb-16 text-sm font-semibold">
            {[
              { label: 'Document arrive', icon: faFileInvoiceDollar, bg: '#F3F4F6', text: '#6B7280' },
              { label: 'CLASSA classifie', icon: faMagnifyingGlass, bg: '#F3E8FF', text: '#7E22CE' },
              { label: 'COMPTAA ecrit', icon: faCalculator, bg: '#DBEAFE', text: '#1D4ED8' },
              { label: 'BANKA rapproche', icon: faLink, bg: '#D1FAE5', text: '#047857' },
              { label: 'FISCA declare', icon: faFileExport, bg: '#FEF3C7', text: '#B45309' },
            ].map((step, i) => (
              <div key={step.label} className="flex items-center gap-2 sm:gap-4">
                <div className="rounded-lg px-3 py-2 flex items-center gap-2" style={{ backgroundColor: step.bg, color: step.text }}>
                  <FontAwesomeIcon icon={step.icon} />
                  <span className="hidden sm:inline">{step.label}</span>
                  <span className="sm:hidden">{step.label.split(' ')[0]}</span>
                </div>
                {i < 4 && <FontAwesomeIcon icon={faArrowRight} className="text-textMuted" />}
              </div>
            ))}
          </div>

          {/* Agent cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: faCalculator, agent: 'COMPTAA', colorFrom: '#3B82F6', colorTo: '#2563EB', title: 'Comptabilite automatique', desc: 'Genere automatiquement vos ecritures comptables conformes PCG 2025.', example: '12 ecritures generees pour Mars 2026' },
              { icon: faLink, agent: 'BANKA', colorFrom: '#10B981', colorTo: '#059669', title: 'Rapprochement bancaire', desc: 'Rapproche vos releves bancaires avec 3 passes de matching intelligent.', example: '45/47 transactions rapprochees (95.7%)' },
              { icon: faFileExport, agent: 'FISCA', colorFrom: '#F59E0B', colorTo: '#D97706', title: 'Declarations fiscales', desc: 'Calcule et prepare vos CA3/IS/CVAE avec zero erreur.', example: 'CA3 T1 2026: TVA collectee 12 450 EUR' },
              { icon: faChartLine, agent: 'FINA', colorFrom: '#8B5CF6', colorTo: '#7C3AED', title: 'Analyse financiere', desc: 'Analyse vos SIG, ratios et score de sante financiere en temps reel.', example: 'Score sante: 87/100 (+5 pts)' },
              { icon: faMoneyBillTrendUp, agent: 'FORECASTA', colorFrom: '#06B6D4', colorTo: '#0891B2', title: 'Previsions tresorerie', desc: 'Prevoit votre tresorerie a J+7, J+30 et J+90.', example: 'J+30: +24 500 EUR (confiance 92%)' },
              { icon: faMagnifyingGlass, agent: 'CLASSA', colorFrom: '#EC4899', colorTo: '#DB2777', title: 'Classification documents', desc: 'Classifie automatiquement factures, bulletins de paie, releves.', example: '8 factures classees, 2 bulletins paie' },
              { icon: faRepeat, agent: 'RELANCA', colorFrom: '#F97316', colorTo: '#EA580C', title: 'Relance documents', desc: 'Relance les documents manquants avec escalade D+3/D+7/D+14.', example: '3 relances envoyees, 1 reponse recue' },
              { icon: faCoins, agent: 'PAIEA', colorFrom: '#14B8A6', colorTo: '#0D9488', title: 'Ventilation charges', desc: 'Ventile les charges sociales sur les bons comptes PCG.', example: 'URSSAF 4 230 EUR ventile sur 645x' },
            ].map((a) => (
              <div key={a.agent} className="group bg-white rounded-2xl border border-borderColor hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 transition-all overflow-hidden">
                <div className="p-4 flex items-center gap-3" style={{ background: `linear-gradient(to right, ${a.colorFrom}, ${a.colorTo})` }}>
                  <div className="w-10 h-10 rounded-lg bg-white/20 flex items-center justify-center">
                    <FontAwesomeIcon icon={a.icon} className="text-white" />
                  </div>
                  <div>
                    <span className="text-xs font-bold text-white/80 uppercase tracking-wider">{a.agent}</span>
                    <h3 className="text-sm font-bold text-white">{a.title}</h3>
                  </div>
                </div>
                <div className="p-5">
                  <p className="text-sm text-textSecondary leading-relaxed mb-4">{a.desc}</p>
                  <div className="bg-bgPage rounded-lg p-3 text-xs font-mono text-textSecondary border border-borderColor">
                    <span className="text-successGreen font-bold">&#9679;</span> {a.example}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================================================================ */}
      {/* FEATURES GRID                                                    */}
      {/* ================================================================ */}
      <section id="features" className="py-20 sm:py-28 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="text-sm font-bold text-primary uppercase tracking-widest mb-3">Plateforme complete</p>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-textPrimary">Tout ce dont vous avez besoin</h2>
            <p className="mt-4 text-textSecondary max-w-2xl mx-auto">
              Une suite comptable complete, pensee pour les experts-comptables, DAF et dirigeants francais.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[
              { icon: faCalculator, title: 'Comptabilite automatique', desc: 'PCG 2025, ecritures auto, lettrage, journaux et grand livre.' },
              { icon: faLink, title: 'Rapprochement bancaire', desc: 'Import CAMT.053/CSV, matching 3 passes, detection ecarts.' },
              { icon: faFileExport, title: 'Declarations fiscales', desc: 'CA3, IS, CVAE auto-calcules, detection penalites de retard.' },
              { icon: faChartLine, title: 'Analyse financiere', desc: 'SIG, ratios, scoring sante, previsions et tableaux de bord.' },
              { icon: faFileInvoiceDollar, title: 'Facturation electronique', desc: 'Factur-X 2026, integration PPF/PDP, conformite garantie.' },
              { icon: faCoins, title: 'Paie & Social', desc: 'Ventilation charges sociales, URSSAF, retraite, prevoyance.' },
              { icon: faCloudArrowUp, title: 'Collecte intelligente', desc: 'Import email, cloud, OCR avance, classification automatique.' },
              { icon: faUsers, title: 'Dossiers clients', desc: 'Multi-dossier, timeline activite, gestion documents centralisee.' },
              { icon: faScaleBalanced, title: 'FEC conforme', desc: 'Export Article A47 A-1, validation automatique, zero anomalie.' },
              { icon: faBell, title: 'Notifications intelligentes', desc: 'Alertes echeances, anomalies detectees, rappels automatiques.' },
              { icon: faGears, title: 'Agents autonomes', desc: 'Planification, relance, monitoring continu, escalade automatique.' },
              { icon: faGlobe, title: 'API & Integrations', desc: 'SAP, Oracle, Google Workspace, Microsoft 365, open API.' },
            ].map((f) => (
              <div key={f.title} className="group bg-bgPage rounded-2xl p-6 border border-borderColor hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 transition-all">
                <div className="w-12 h-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center mb-4 group-hover:bg-primary group-hover:text-white transition-colors">
                  <FontAwesomeIcon icon={f.icon} className="text-lg" />
                </div>
                <h3 className="text-base font-bold mb-2">{f.title}</h3>
                <p className="text-sm text-textSecondary leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================================================================ */}
      {/* LIVE DEMO                                                        */}
      {/* ================================================================ */}
      <section id="demo" className="py-20 sm:py-28 bg-bgPage">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <p className="text-sm font-bold text-primary uppercase tracking-widest mb-3">En action</p>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-textPrimary">Voyez DouCompta en action</h2>
          </div>

          {/* Tabs */}
          <div className="flex items-center justify-center gap-2 mb-8">
            {['Ecritures comptables', 'Rapprochement', 'Declaration CA3'].map((tab, i) => (
              <button
                key={tab}
                onClick={() => setActiveTab(i)}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
                  activeTab === i ? 'bg-primary text-white' : 'bg-white text-textSecondary hover:bg-gray-100 border border-borderColor'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="bg-white rounded-2xl border border-borderColor shadow-lg overflow-hidden">
            {activeTab === 0 && (
              <div className="p-6">
                <div className="flex items-center gap-2 mb-4 text-sm text-textMuted">
                  <FontAwesomeIcon icon={faRobot} className="text-primary" />
                  <span className="font-semibold text-primary">COMPTAA</span> a genere ces ecritures automatiquement
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-bgPage text-left text-textMuted text-xs uppercase tracking-wider">
                        <th className="px-4 py-3">Date</th>
                        <th className="px-4 py-3">Journal</th>
                        <th className="px-4 py-3">Compte</th>
                        <th className="px-4 py-3">Libelle</th>
                        <th className="px-4 py-3 text-right">Debit</th>
                        <th className="px-4 py-3 text-right">Credit</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-borderColor">
                      {[
                        { date: '01/03/2026', journal: 'ACH', compte: '607100', libelle: 'Achat marchandises - Fournisseur Alpha', debit: '2 500,00', credit: '' },
                        { date: '01/03/2026', journal: 'ACH', compte: '445660', libelle: 'TVA deductible 20%', debit: '500,00', credit: '' },
                        { date: '01/03/2026', journal: 'ACH', compte: '401000', libelle: 'Fournisseur Alpha', debit: '', credit: '3 000,00' },
                        { date: '05/03/2026', journal: 'VTE', compte: '411000', libelle: 'Client Beta SAS', debit: '6 000,00', credit: '' },
                        { date: '05/03/2026', journal: 'VTE', compte: '445710', libelle: 'TVA collectee 20%', debit: '', credit: '1 000,00' },
                        { date: '05/03/2026', journal: 'VTE', compte: '707100', libelle: 'Vente marchandises - Client Beta', debit: '', credit: '5 000,00' },
                      ].map((row, i) => (
                        <tr key={i} className="hover:bg-bgPage/50">
                          <td className="px-4 py-3 font-mono text-xs">{row.date}</td>
                          <td className="px-4 py-3"><span className="bg-primary/10 text-primary text-xs font-bold px-2 py-0.5 rounded">{row.journal}</span></td>
                          <td className="px-4 py-3 font-mono text-xs">{row.compte}</td>
                          <td className="px-4 py-3">{row.libelle}</td>
                          <td className="px-4 py-3 text-right font-mono">{row.debit && <span className="text-blue-600">{row.debit}</span>}</td>
                          <td className="px-4 py-3 text-right font-mono">{row.credit && <span className="text-emerald-600">{row.credit}</span>}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 1 && (
              <div className="p-6">
                <div className="flex items-center gap-2 mb-4 text-sm text-textMuted">
                  <FontAwesomeIcon icon={faRobot} className="text-emerald-600" />
                  <span className="font-semibold text-emerald-600">BANKA</span> rapprochement en cours &mdash; 3 passes
                </div>
                <div className="space-y-3">
                  {[
                    { bank: 'VIR SEPA Client Beta', montant: '+6 000,00', compte: '411000 - Client Beta SAS', statut: 'Rapproche', color: 'text-successGreen bg-green-50' },
                    { bank: 'PRLV Fournisseur Alpha', montant: '-3 000,00', compte: '401000 - Fournisseur Alpha', statut: 'Rapproche', color: 'text-successGreen bg-green-50' },
                    { bank: 'CB AMAZON WEB SERVICES', montant: '-149,00', compte: '613500 - Hebergement', statut: 'Suggestion', color: 'text-warningAmber bg-amber-50' },
                    { bank: 'VIR URSSAF', montant: '-4 230,00', compte: '431000 - URSSAF', statut: 'Rapproche', color: 'text-successGreen bg-green-50' },
                  ].map((row, i) => (
                    <div key={i} className="flex items-center gap-4 p-4 rounded-xl border border-borderColor">
                      <div className="flex-1">
                        <p className="font-semibold text-sm">{row.bank}</p>
                        <p className="text-xs text-textMuted">{row.compte}</p>
                      </div>
                      <span className={`font-mono font-bold text-sm ${row.montant.startsWith('+') ? 'text-emerald-600' : 'text-red-500'}`}>{row.montant} &euro;</span>
                      <span className={`text-xs font-bold px-3 py-1 rounded-full ${row.color}`}>{row.statut}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 2 && (
              <div className="p-6">
                <div className="flex items-center gap-2 mb-4 text-sm text-textMuted">
                  <FontAwesomeIcon icon={faRobot} className="text-amber-600" />
                  <span className="font-semibold text-amber-600">FISCA</span> declaration CA3 preparee automatiquement
                </div>
                <div className="bg-bgPage rounded-xl p-6 border border-borderColor">
                  <h4 className="font-bold text-lg mb-4">Declaration CA3 &mdash; Mars 2026</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                    {[
                      { label: 'CA HT (ventes France)', value: '45 230,00 EUR' },
                      { label: 'TVA collectee (20%)', value: '9 046,00 EUR' },
                      { label: 'TVA deductible (achats)', value: '3 812,00 EUR' },
                      { label: 'TVA deductible (immos)', value: '420,00 EUR' },
                      { label: 'Credit de TVA precedent', value: '0,00 EUR' },
                      { label: 'TVA nette a payer', value: '4 814,00 EUR' },
                    ].map((row) => (
                      <div key={row.label} className="flex justify-between p-3 bg-white rounded-lg border border-borderColor">
                        <span className="text-textSecondary">{row.label}</span>
                        <span className="font-bold font-mono">{row.value}</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 flex items-center gap-2 text-sm text-successGreen">
                    <FontAwesomeIcon icon={faCircleCheck} />
                    <span className="font-semibold">Verification terminee &mdash; 0 anomalie detectee</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ================================================================ */}
      {/* ROI CALCULATOR                                                   */}
      {/* ================================================================ */}
      <section className="py-20 sm:py-28" style={{ backgroundColor: '#F3F4F6' }}>
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <p className="text-sm font-bold uppercase tracking-widest mb-3" style={{ color: '#4F46E5' }}>Retour sur investissement</p>
            <h2 className="text-3xl sm:text-4xl font-extrabold" style={{ color: '#111827' }}>Calculez vos economies</h2>
            <p className="mt-3 text-base" style={{ color: '#6B7280' }}>Deplacez les curseurs pour estimer vos gains avec DouCompta</p>
          </div>

          <div className="rounded-2xl p-8 sm:p-10" style={{ backgroundColor: '#FFFFFF', border: '2px solid #E5E7EB', boxShadow: '0 10px 40px rgba(0,0,0,0.08)' }}>
            {/* Inputs */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
              <div>
                <label className="block text-sm font-bold mb-4" style={{ color: '#111827' }}>
                  <FontAwesomeIcon icon={faBuilding} className="mr-2" style={{ color: '#4F46E5' }} />
                  Nombre de dossiers comptables
                </label>
                <div className="flex items-center gap-3">
                  <button onClick={() => setDossiers(Math.max(1, dossiers - 1))} className="w-10 h-10 rounded-lg text-lg font-bold flex items-center justify-center" style={{ backgroundColor: '#EEF2FF', color: '#4F46E5', border: '1px solid #C7D2FE' }}>-</button>
                  <input
                    type="number"
                    min={1}
                    max={200}
                    value={dossiers}
                    onChange={(e) => setDossiers(Math.max(1, Math.min(200, Number(e.target.value) || 1)))}
                    className="flex-1 h-12 text-center text-2xl font-bold rounded-lg outline-none"
                    style={{ border: '2px solid #4F46E5', color: '#4F46E5' }}
                  />
                  <button onClick={() => setDossiers(Math.min(200, dossiers + 1))} className="w-10 h-10 rounded-lg text-lg font-bold flex items-center justify-center" style={{ backgroundColor: '#EEF2FF', color: '#4F46E5', border: '1px solid #C7D2FE' }}>+</button>
                </div>
                <div className="flex justify-center gap-2 mt-3">
                  {[1, 5, 10, 25, 50, 100].map(v => (
                    <button key={v} onClick={() => setDossiers(v)}
                      className="px-3 py-1 rounded-full text-xs font-semibold transition-all"
                      style={{
                        backgroundColor: dossiers === v ? '#4F46E5' : '#F3F4F6',
                        color: dossiers === v ? '#FFFFFF' : '#6B7280',
                        border: dossiers === v ? '1px solid #4F46E5' : '1px solid #D1D5DB',
                      }}
                    >{v}</button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-bold mb-4" style={{ color: '#111827' }}>
                  <FontAwesomeIcon icon={faClock} className="mr-2" style={{ color: '#4F46E5' }} />
                  Heures comptables par mois
                </label>
                <div className="flex items-center gap-3">
                  <button onClick={() => setHeures(Math.max(5, heures - 5))} className="w-10 h-10 rounded-lg text-lg font-bold flex items-center justify-center" style={{ backgroundColor: '#EEF2FF', color: '#4F46E5', border: '1px solid #C7D2FE' }}>-</button>
                  <input
                    type="number"
                    min={5}
                    max={500}
                    value={heures}
                    onChange={(e) => setHeures(Math.max(5, Math.min(500, Number(e.target.value) || 5)))}
                    className="flex-1 h-12 text-center text-2xl font-bold rounded-lg outline-none"
                    style={{ border: '2px solid #4F46E5', color: '#4F46E5' }}
                  />
                  <button onClick={() => setHeures(Math.min(500, heures + 5))} className="w-10 h-10 rounded-lg text-lg font-bold flex items-center justify-center" style={{ backgroundColor: '#EEF2FF', color: '#4F46E5', border: '1px solid #C7D2FE' }}>+</button>
                </div>
                <div className="flex justify-center gap-2 mt-3">
                  {[20, 40, 80, 120, 200].map(v => (
                    <button key={v} onClick={() => setHeures(v)}
                      className="px-3 py-1 rounded-full text-xs font-semibold transition-all"
                      style={{
                        backgroundColor: heures === v ? '#4F46E5' : '#F3F4F6',
                        color: heures === v ? '#FFFFFF' : '#6B7280',
                        border: heures === v ? '1px solid #4F46E5' : '1px solid #D1D5DB',
                      }}
                    >{v}h</button>
                  ))}
                </div>
              </div>
            </div>

            {/* Divider */}
            <div className="flex items-center gap-4 mb-10">
              <div className="flex-1 h-px" style={{ backgroundColor: '#E5E7EB' }} />
              <span className="text-xs font-bold uppercase tracking-widest" style={{ color: '#9CA3AF' }}>Vos economies estimees</span>
              <div className="flex-1 h-px" style={{ backgroundColor: '#E5E7EB' }} />
            </div>

            {/* Results */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div className="rounded-xl p-6 text-center" style={{ backgroundColor: '#EEF2FF', border: '2px solid #C7D2FE' }}>
                <div className="w-14 h-14 rounded-full mx-auto mb-4 flex items-center justify-center" style={{ backgroundColor: '#4F46E5' }}>
                  <FontAwesomeIcon icon={faClock} className="text-white text-xl" />
                </div>
                <p className="text-5xl font-extrabold" style={{ color: '#4F46E5' }}>{tempsGagne}</p>
                <p className="text-lg font-bold mt-1" style={{ color: '#4F46E5' }}>heures / mois</p>
                <p className="text-sm mt-2" style={{ color: '#6B7280' }}>de temps gagne</p>
              </div>
              <div className="rounded-xl p-6 text-center" style={{ backgroundColor: '#ECFDF5', border: '2px solid #A7F3D0' }}>
                <div className="w-14 h-14 rounded-full mx-auto mb-4 flex items-center justify-center" style={{ backgroundColor: '#10B981' }}>
                  <FontAwesomeIcon icon={faCoins} className="text-white text-xl" />
                </div>
                <p className="text-5xl font-extrabold" style={{ color: '#10B981' }}>{economie.toLocaleString('fr-FR')}</p>
                <p className="text-lg font-bold mt-1" style={{ color: '#10B981' }}>EUR / an</p>
                <p className="text-sm mt-2" style={{ color: '#6B7280' }}>d&apos;economie annuelle</p>
              </div>
              <div className="rounded-xl p-6 text-center" style={{ backgroundColor: '#FFF7ED', border: '2px solid #FED7AA' }}>
                <div className="w-14 h-14 rounded-full mx-auto mb-4 flex items-center justify-center" style={{ backgroundColor: '#F59E0B' }}>
                  <FontAwesomeIcon icon={faRocket} className="text-white text-xl" />
                </div>
                <p className="text-5xl font-extrabold" style={{ color: '#F59E0B' }}>{roi}</p>
                <p className="text-lg font-bold mt-1" style={{ color: '#F59E0B' }}>mois</p>
                <p className="text-sm mt-2" style={{ color: '#6B7280' }}>retour sur investissement</p>
              </div>
            </div>

            {/* Explanation */}
            <div className="mt-8 p-4 rounded-lg text-sm" style={{ backgroundColor: '#F9FAFB', border: '1px solid #E5E7EB', color: '#6B7280' }}>
              <strong style={{ color: '#111827' }}>Comment ca marche :</strong> DouCompta automatise ~70% de vos taches comptables.
              Avec {dossiers} dossier{dossiers > 1 ? 's' : ''} et {heures}h/mois, vous gagnez {tempsGagne}h de travail.
              A 65 EUR/h (taux moyen expert-comptable), cela represente {economie.toLocaleString('fr-FR')} EUR d&apos;economie annuelle.
            </div>
          </div>
        </div>
      </section>

      {/* ================================================================ */}
      {/* COMPLIANCE & SECURITY                                            */}
      {/* ================================================================ */}
      <section className="py-20 sm:py-28 bg-gradient-to-br from-indigo-950 via-indigo-900 to-purple-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white">Conforme. Securise. Souverain.</h2>
            <p className="mt-4 text-indigo-200 max-w-xl mx-auto">
              Vos donnees comptables sont protegees au plus haut niveau de securite.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: faScaleBalanced, title: 'DGFiP', desc: 'FEC conforme Article A47 A-1, piste d\'audit fiable, zero anomalie.' },
              { icon: faShieldHalved, title: 'RGPD', desc: 'Donnees protegees, droit a l\'oubli, consentement explicite, DPO dedie.' },
              { icon: faGlobe, title: 'Hebergement France', desc: 'Infrastructure OVHcloud, datacenters en France, souverainete garantie.' },
              { icon: faLock, title: 'Chiffrement', desc: 'TLS 1.3 en transit, AES-256 au repos, secrets en coffre-fort HSM.' },
            ].map((c) => (
              <div key={c.title} className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 text-center">
                <div className="w-14 h-14 rounded-xl bg-white/10 text-white flex items-center justify-center mx-auto mb-4">
                  <FontAwesomeIcon icon={c.icon} className="text-xl" />
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{c.title}</h3>
                <p className="text-sm text-indigo-200 leading-relaxed">{c.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================================================================ */}
      {/* PRICING                                                          */}
      {/* ================================================================ */}
      <section id="pricing" className="py-20 sm:py-28 bg-bgPage">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="text-sm font-bold text-primary uppercase tracking-widest mb-3">Tarifs transparents</p>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-textPrimary">Choisissez votre formule</h2>
            <p className="mt-4 text-textSecondary max-w-xl mx-auto">
              Sans engagement. Essai gratuit de 14 jours sur toutes les formules.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
            {/* Starter */}
            <div className="bg-white rounded-2xl border border-borderColor p-8 flex flex-col">
              <h3 className="text-lg font-bold mb-1">Starter</h3>
              <p className="text-textMuted text-sm mb-6">Pour les independants</p>
              <div className="mb-6">
                <span className="text-4xl font-extrabold">29&euro;</span>
                <span className="text-textSecondary">/mois</span>
              </div>
              <ul className="space-y-3 text-sm mb-8 flex-1">
                {['1 dossier comptable', 'Comptabilite de base', 'Export FEC', '2 agents IA', 'Support email'].map((f) => (
                  <li key={f} className="flex items-start gap-2">
                    <FontAwesomeIcon icon={faCheck} className="text-successGreen mt-0.5 text-xs" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <Link href="/login" className="block text-center bg-white border-2 border-primary text-primary font-semibold py-3 rounded-xl hover:bg-primary hover:text-white transition-colors">
                Commencer
              </Link>
            </div>

            {/* Pro */}
            <div className="relative bg-white rounded-2xl border-2 border-primary p-8 flex flex-col shadow-xl shadow-primary/10">
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-primary text-white text-xs font-bold px-4 py-1 rounded-full uppercase tracking-wider">
                Populaire
              </div>
              <h3 className="text-lg font-bold mb-1">Pro</h3>
              <p className="text-textMuted text-sm mb-6">Pour les cabinets</p>
              <div className="mb-6">
                <span className="text-4xl font-extrabold">79&euro;</span>
                <span className="text-textSecondary">/mois</span>
              </div>
              <ul className="space-y-3 text-sm mb-8 flex-1">
                {['10 dossiers comptables', 'Tous les agents IA', 'Rapprochement bancaire', 'Declarations fiscales', 'Analyse financiere', 'Support prioritaire'].map((f) => (
                  <li key={f} className="flex items-start gap-2">
                    <FontAwesomeIcon icon={faCheck} className="text-successGreen mt-0.5 text-xs" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <Link href="/login" className="block text-center bg-primary text-white font-semibold py-3 rounded-xl hover:bg-primaryHover transition-colors">
                Commencer
              </Link>
            </div>

            {/* Expert */}
            <div className="bg-white rounded-2xl border border-borderColor p-8 flex flex-col">
              <h3 className="text-lg font-bold mb-1">Expert</h3>
              <p className="text-textMuted text-sm mb-6">Pour les grands cabinets</p>
              <div className="mb-6">
                <span className="text-4xl font-extrabold">149&euro;</span>
                <span className="text-textSecondary">/mois</span>
              </div>
              <ul className="space-y-3 text-sm mb-8 flex-1">
                {['50 dossiers comptables', 'Tout du plan Pro', 'Support prioritaire', 'Acces API complet', 'Formations incluses', 'Manager dedie'].map((f) => (
                  <li key={f} className="flex items-start gap-2">
                    <FontAwesomeIcon icon={faCheck} className="text-successGreen mt-0.5 text-xs" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <Link href="/login" className="block text-center bg-white border-2 border-primary text-primary font-semibold py-3 rounded-xl hover:bg-primary hover:text-white transition-colors">
                Commencer
              </Link>
            </div>

            {/* Enterprise */}
            <div className="bg-white rounded-2xl border border-borderColor p-8 flex flex-col">
              <h3 className="text-lg font-bold mb-1">Enterprise</h3>
              <p className="text-textMuted text-sm mb-6">Pour les grands groupes</p>
              <div className="mb-6">
                <span className="text-4xl font-extrabold">Sur devis</span>
              </div>
              <ul className="space-y-3 text-sm mb-8 flex-1">
                {['Dossiers illimites', 'Deploiement on-premise', 'SLA garanti 99.9%', 'Support dedie 24/7', 'Formation sur site', 'Personnalisation'].map((f) => (
                  <li key={f} className="flex items-start gap-2">
                    <FontAwesomeIcon icon={faCheck} className="text-successGreen mt-0.5 text-xs" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <Link href="/contact" className="block text-center bg-white border-2 border-primary text-primary font-semibold py-3 rounded-xl hover:bg-primary hover:text-white transition-colors">
                Nous contacter
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ================================================================ */}
      {/* TESTIMONIALS                                                     */}
      {/* ================================================================ */}
      <section id="testimonials" className="py-20 sm:py-28 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="text-sm font-bold text-primary uppercase tracking-widest mb-3">Temoignages</p>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-textPrimary">Ce que disent nos clients</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {[
              {
                name: 'Marie Dupont',
                role: 'Expert-comptable, Cabinet Dupont & Associes',
                quote: 'Nous avons divise par 3 le temps de saisie. Les ecritures auto sont d\'une precision remarquable. La conformite DGFiP est irreprochable.',
              },
              {
                name: 'Jean-Philippe Martin',
                role: 'DAF, Groupe Lumiere SAS',
                quote: 'Les previsions de tresorerie ont transforme notre pilotage financier. Notre reporting est passe de 5 jours a 2 heures.',
              },
              {
                name: 'Sophie Lefebvre',
                role: 'Gerante, Boulangerie Lefebvre SARL',
                quote: 'Enfin un outil comptable que je comprends. L\'IA fait tout, je me concentre sur mon metier. Le rapport qualite-prix est imbattable.',
              },
            ].map((t) => (
              <div key={t.name} className="bg-bgPage rounded-2xl p-8 border border-borderColor">
                <div className="flex gap-1 text-yellow-400 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <FontAwesomeIcon key={i} icon={faStar} className="text-sm" />
                  ))}
                </div>
                <p className="text-textSecondary leading-relaxed mb-6 italic">&ldquo;{t.quote}&rdquo;</p>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-sm">
                    {t.name.split(' ').map((n) => n[0]).join('')}
                  </div>
                  <div>
                    <p className="font-semibold text-sm">{t.name}</p>
                    <p className="text-xs text-textMuted">{t.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================================================================ */}
      {/* FAQ                                                              */}
      {/* ================================================================ */}
      <section id="faq" className="py-20 sm:py-28 bg-bgPage">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <p className="text-sm font-bold text-primary uppercase tracking-widest mb-3">Questions frequentes</p>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-textPrimary">FAQ</h2>
          </div>

          <div className="space-y-3">
            {[
              { q: 'DouCompta est-il conforme aux exigences de la DGFiP ?', a: 'Oui, DouCompta genere des FEC 100% conformes a l\'Article A47 A-1 du Livre des Procedures Fiscales. Chaque ecriture respecte le PCG 2025 et la piste d\'audit fiable est garantie.' },
              { q: 'Ou sont hebergees mes donnees ?', a: 'Toutes les donnees sont hebergees en France chez OVHcloud, dans des datacenters certifies ISO 27001. Le chiffrement TLS 1.3 en transit et AES-256 au repos garantit la securite maximale.' },
              { q: 'Comment migrer depuis mon logiciel actuel ?', a: 'DouCompta importe vos FEC existants, fichiers CAMT.053, CSV bancaires et Factur-X. Notre equipe vous accompagne gratuitement dans la migration.' },
              { q: 'Quel support est disponible ?', a: 'Le plan Starter inclut le support email. Les plans Pro et Expert beneficient du support prioritaire avec temps de reponse garanti. Enterprise dispose d\'un support dedie 24/7.' },
              { q: 'Comment fonctionne la facturation ?', a: 'La facturation est mensuelle, sans engagement. Vous pouvez changer de formule ou annuler a tout moment. Essai gratuit de 14 jours sur toutes les formules.' },
              { q: 'Proposez-vous une API ?', a: 'Oui, notre API RESTful complete est disponible des le plan Expert. Elle permet l\'integration avec SAP, Oracle, Google Workspace, Microsoft 365 et tout systeme tiers.' },
            ].map((item, i) => (
              <div key={i} className="bg-white rounded-xl border border-borderColor overflow-hidden">
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full flex items-center justify-between p-5 text-left"
                >
                  <span className="font-semibold text-sm pr-4">{item.q}</span>
                  <span className={`text-primary transition-transform flex-shrink-0 ${openFaq === i ? 'rotate-180' : ''}`}>
                    <FontAwesomeIcon icon={faArrowDown} className="text-xs" />
                  </span>
                </button>
                {openFaq === i && (
                  <div className="px-5 pb-5 text-sm text-textSecondary leading-relaxed border-t border-borderColor pt-4">
                    {item.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================================================================ */}
      {/* CTA FINAL                                                        */}
      {/* ================================================================ */}
      <section id="contact" className="py-20 sm:py-28 bg-gradient-to-br from-primary via-indigo-600 to-purple-700">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
            Pret a automatiser votre comptabilite ?
          </h2>
          <p className="text-indigo-100 text-lg mb-10 max-w-xl mx-auto">
            Rejoignez les cabinets et entreprises qui font confiance a DouCompta pour automatiser leur comptabilite.
          </p>
          <form
            onSubmit={(e) => e.preventDefault()}
            className="flex flex-col sm:flex-row items-center gap-3 max-w-lg mx-auto mb-6"
          >
            <div className="relative flex-1 w-full">
              <FontAwesomeIcon icon={faEnvelope} className="absolute left-4 top-1/2 -translate-y-1/2 text-textMuted" />
              <input
                type="email"
                placeholder="votre@email.fr"
                className="w-full pl-11 pr-4 py-4 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-white/50"
              />
            </div>
            <button
              type="submit"
              className="w-full sm:w-auto bg-white text-primary font-bold px-8 py-4 rounded-xl hover:shadow-lg hover:scale-105 transition-all whitespace-nowrap"
            >
              Demander une demo
            </button>
          </form>
          <p className="text-indigo-200 text-sm">
            <FontAwesomeIcon icon={faPhone} className="mr-2" />
            Ou appelez-nous : +33 1 42 00 00 00
          </p>
        </div>
      </section>

      {/* ================================================================ */}
      {/* FOOTER                                                           */}
      {/* ================================================================ */}
      <footer className="bg-gray-900 text-gray-400 pt-16 pb-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-10 mb-14">
            {/* Brand */}
            <div className="lg:col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                  <FontAwesomeIcon icon={faCalculator} className="text-white text-sm" />
                </div>
                <span className="text-xl font-bold text-white">DouCompta</span>
              </div>
              <p className="text-sm leading-relaxed max-w-xs">
                La plateforme de comptabilite souveraine propulsee par l&apos;IA. Conforme aux normes francaises, hebergee en France.
              </p>
              <div className="flex gap-3 mt-6">
                {['LinkedIn', 'Twitter', 'GitHub'].map((s) => (
                  <span key={s} className="w-9 h-9 rounded-lg bg-gray-800 hover:bg-primary flex items-center justify-center text-xs font-bold text-gray-500 hover:text-white transition-colors cursor-pointer">
                    {s[0]}
                  </span>
                ))}
              </div>
            </div>

            {/* Produit */}
            <div>
              <h4 className="text-white font-semibold mb-4 text-sm uppercase tracking-wider">Produit</h4>
              <ul className="space-y-2 text-sm">
                {[
                  { label: 'Fonctionnalites', href: '#features' },
                  { label: 'Tarifs', href: '#pricing' },
                  { label: 'Securite', href: '/legal/confidentialite' },
                  { label: 'API', href: '#faq' },
                  { label: 'Changelog', href: '#' },
                ].map((l) => (
                  <li key={l.label}>
                    <Link href={l.href} className="hover:text-white transition-colors">{l.label}</Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Ressources */}
            <div>
              <h4 className="text-white font-semibold mb-4 text-sm uppercase tracking-wider">Ressources</h4>
              <ul className="space-y-2 text-sm">
                {[
                  { label: 'Documentation', href: '/legal/cgu' },
                  { label: 'Blog', href: '#' },
                  { label: 'Tutoriels', href: '#' },
                  { label: 'Support', href: '/contact' },
                  { label: 'FAQ', href: '#faq' },
                ].map((l) => (
                  <li key={l.label}>
                    <Link href={l.href} className="hover:text-white transition-colors">{l.label}</Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Contact */}
            <div>
              <h4 className="text-white font-semibold mb-4 text-sm uppercase tracking-wider">Contact</h4>
              <ul className="space-y-3 text-sm">
                <li className="flex items-start gap-2">
                  <FontAwesomeIcon icon={faLocationDot} className="text-primary mt-0.5" />
                  <span>12 Rue de la Paix, 75002 Paris</span>
                </li>
                <li className="flex items-start gap-2">
                  <FontAwesomeIcon icon={faPhone} className="text-primary mt-0.5" />
                  <span>+33 1 42 00 00 00</span>
                </li>
                <li className="flex items-start gap-2">
                  <FontAwesomeIcon icon={faEnvelope} className="text-primary mt-0.5" />
                  <span>contact@doucompta.fr</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Legal links */}
          <div className="border-t border-gray-800 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
            <div className="flex flex-wrap items-center gap-4">
              <Link href="/legal/mentions-legales" className="hover:text-white transition-colors">Mentions legales</Link>
              <Link href="/legal/cgu" className="hover:text-white transition-colors">CGU</Link>
              <Link href="/legal/confidentialite" className="hover:text-white transition-colors">Confidentialite</Link>
              <Link href="/legal/cookies" className="hover:text-white transition-colors">Cookies</Link>
            </div>
            <div className="text-center sm:text-right">
              <p>&copy; 2026 DouCompta SAS &middot; SIREN 123 456 789 &middot; Heberge en France</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

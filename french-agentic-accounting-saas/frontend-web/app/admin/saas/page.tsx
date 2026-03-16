'use client'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faServer, faUsers, faCreditCard, faChartLine } from '@fortawesome/free-solid-svg-icons'

export default function SaaSAdminPage() {
  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-textPrimary">Administration SaaS</h1>
        <p className="text-sm text-textSecondary mt-1">Gestion de la plateforme</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { icon: faUsers, label: 'Tenants', value: '-', desc: 'Organisations actives' },
          { icon: faCreditCard, label: 'Abonnements', value: '-', desc: 'Abonnements actifs' },
          { icon: faServer, label: 'Services', value: '12', desc: 'Microservices deployes' },
          { icon: faChartLine, label: 'Utilisation', value: '-', desc: 'Requetes/jour' },
        ].map((card, i) => (
          <div key={i} className="bg-white rounded-xl border border-borderColor p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-indigo-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={card.icon} className="text-primary" />
              </div>
              <span className="text-sm font-medium text-textSecondary">{card.label}</span>
            </div>
            <div className="text-2xl font-bold text-textPrimary">{card.value}</div>
            <div className="text-xs text-textMuted mt-1">{card.desc}</div>
          </div>
        ))}
      </div>
      <div className="mt-6 bg-yellow-50 rounded-xl border border-yellow-200 p-6 text-center">
        <p className="text-sm text-yellow-800">Module SaaS Admin en cours de developpement. Provisioning multi-tenant, facturation et monitoring a venir.</p>
      </div>
    </div>
  )
}

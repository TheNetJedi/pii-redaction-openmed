import { createFileRoute, Link } from '@tanstack/react-router'
import { ArrowRight, ShieldCheck, Zap, Database } from 'lucide-react'

export const Route = createFileRoute('/')({
  component: Dashboard,
})

function Dashboard() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Hero / Quick Action */}
      <div className="grid md:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div className="flex items-center gap-4 mb-6">
            <img
              src="/favicon.png"
              alt="RedactX"
              className="w-16 h-16 rounded-xl shadow-lg shadow-accent/20"
            />
            <div>
              <h1 className="text-4xl font-bold text-white tracking-tight">
                Redact<span className="text-accent">X</span>
              </h1>
              <p className="text-text-muted text-sm">Production-grade PII Redaction</p>
            </div>
          </div>

          <p className="text-lg text-text-secondary leading-relaxed">
            Medical-grade entity detection and de-identification for clinical documents.
            Powered by OpenMed LLMs.
          </p>

          <div className="flex gap-4">
            <Link
              to="/redact"
              className="btn btn-primary h-12 px-6 text-base"
            >
              Start Redaction <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
            <Link
              to="/bulk"
              className="btn btn-secondary h-12 px-6 text-base"
            >
              Batch Process
            </Link>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-4">
            <StatBox label="Model Engine" value="ClinicalE5" />
            <StatBox label="Architecture" value="Stateless" />
            <StatBox label="Compliance" value="HIPAA Ready" />
            <StatBox label="Inference" value="Local / Private" />
          </div>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 gap-4">
          <FeatureCard
            icon={ShieldCheck}
            title="HIPAA Compliant"
            desc="Safe Harbor expert determination. All processing happens locally in container."
          />
          <FeatureCard
            icon={Zap}
            title="High Performance"
            desc="Optimized for low-latency clinical inference."
          />
          <FeatureCard
            icon={Database}
            title="Zero Retention"
            desc="Stateless architecture. No data persisted on disk after processing."
          />
        </div>
      </div>
    </div>
  )
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-clinical-border bg-clinical-surface/50 p-3 rounded-md">
      <div className="text-text-muted text-xs uppercase font-mono mb-1">{label}</div>
      <div className="text-white font-medium">{value}</div>
    </div>
  )
}

function FeatureCard({ icon: Icon, title, desc }: { icon: any; title: string; desc: string }) {
  return (
    <div className="flex gap-4 p-4 border border-clinical-border bg-clinical-surface rounded-md hover:border-accent/30 transition-colors">
      <div className="bg-clinical-bg p-3 h-fit border border-clinical-border rounded-md">
        <Icon className="w-5 h-5 text-accent" />
      </div>
      <div>
        <h3 className="text-white font-medium mb-1">{title}</h3>
        <p className="text-sm text-text-secondary leading-relaxed">{desc}</p>
      </div>
    </div>
  )
}

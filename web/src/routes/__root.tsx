import { Link, Outlet, createRootRoute } from '@tanstack/react-router'
import { FileText, Layers, Settings, Activity } from 'lucide-react'
import '../styles.css'

export const Route = createRootRoute({
  component: RootComponent,
})

function RootComponent() {
  return (
    <>
      <div className="min-h-screen flex flex-col font-sans">
        <header className="border-b border-clinical-border bg-clinical-surface/50 backdrop-blur-md sticky top-0 z-50">
          <div className="max-w-[1400px] mx-auto px-6 h-16 flex items-center justify-between">
            {/* Logo Area */}
            <Link to="/" className="flex items-center gap-3 hover:opacity-90 transition-opacity">
              <img
                src="/favicon.png"
                alt="RedactX"
                className="w-9 h-9 rounded-md"
              />
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold tracking-tight text-white">
                  Redact<span className="text-accent">X</span>
                </span>
                <span className="px-2 py-0.5 rounded-full bg-clinical-border text-[10px] uppercase font-mono text-text-secondary tracking-wider">
                  v1.0
                </span>
              </div>
            </Link>

            {/* Navigation */}
            <nav className="flex items-center gap-1">
              <NavLink to="/" icon={Activity} label="Overview" />
              <NavLink to="/redact" icon={FileText} label="Redact" />
              <NavLink to="/bulk" icon={Layers} label="Batch" />
              <div className="w-px h-6 bg-clinical-border mx-2" />
              <NavLink to="/settings" icon={Settings} label="Config" />
            </nav>
          </div>
        </header>

        <main className="flex-1 w-full bg-clinical-bg relative">
          {/* Subtle Grid Background */}
          <div className="absolute inset-0 bg-grid opacity-[0.03] pointer-events-none" />

          <div className="relative z-10 max-w-[1400px] mx-auto p-6 md:p-8">
            <Outlet />
          </div>
        </main>

        <footer className="border-t border-clinical-border py-6 mt-auto bg-clinical-surface">
          <div className="max-w-[1400px] mx-auto px-6 flex justify-between items-center text-sm text-text-secondary">
            <div className="flex items-center gap-3">
              <img src="/favicon.png" alt="" className="w-5 h-5 opacity-50" />
              <span className="font-mono text-xs">
                STATUS: <span className="text-emerald-500">OPERATIONAL</span>
              </span>
            </div>
            <div className="flex gap-6 text-xs">
              <span>Powered by OpenMed</span>
              <span>HIPAA Compliant</span>
              <span>No Data Retention</span>
            </div>
          </div>
        </footer>
      </div>
    </>
  )
}

function NavLink({ to, icon: Icon, label }: { to: string; icon: any; label: string }) {
  return (
    <Link
      to={to}
      className="[&.active]:bg-clinical-border [&.active]:text-white text-text-secondary hover:text-white hover:bg-clinical-border/50 px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2"
    >
      <Icon className="w-4 h-4" />
      {label}
    </Link>
  )
}

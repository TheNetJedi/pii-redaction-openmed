import { createFileRoute } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { Cpu, Database, Server, Check, Loader2 } from 'lucide-react'

export const Route = createFileRoute('/settings')({
    component: SettingsPage,
})

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function SettingsPage() {
    const [config, setConfig] = useState<any>(null)
    const [models, setModels] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [switchingId, setSwitchingId] = useState<string | null>(null)

    useEffect(() => {
        loadData()
    }, [])

    async function loadData() {
        try {
            const [configRes, modelsRes] = await Promise.all([
                fetch(`${API_URL}/api/v1/config/defaults`),
                fetch(`${API_URL}/api/v1/config/models`)
            ])
            if (configRes.ok && modelsRes.ok) {
                const configData = await configRes.json()
                const modelsData = await modelsRes.json()
                setConfig(configData)
                setModels(modelsData)
            }
        } catch (e) {
            console.error("Failed to load settings", e)
        } finally {
            setLoading(false)
        }
    }

    const handleActivate = async (modelId: string) => {
        setSwitchingId(modelId)
        try {
            const res = await fetch(`${API_URL}/api/v1/config/model`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_id: modelId })
            })

            if (res.ok) {
                // Refresh config to reflect change
                const configRes = await fetch(`${API_URL}/api/v1/config/defaults`)
                const data = await configRes.json()
                setConfig(data)
            }
        } catch (e) {
            console.error("Failed to switch model", e)
        } finally {
            setSwitchingId(null)
        }
    }

    if (loading) return <div className="p-8 text-text-muted flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Loading configuration...</div>

    const activeModel = models.find(m => m.id === config?.model) || { name: config?.model, size: '?' }

    return (
        <div className="layout-container max-w-4xl py-6 space-y-8">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-medium text-white">System Configuration</h2>
                {switchingId && <span className="text-xs text-accent animate-pulse">Switching Model Engine...</span>}
            </div>

            <div className="space-y-6">
                {/* Active Model */}
                <Section title="Model Engine" icon={Cpu}>
                    <div className="bg-clinical-surface border border-clinical-border rounded-md p-4">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h3 className="text-white font-medium">{activeModel.name}</h3>
                                <div className="text-xs text-text-muted mt-1 font-mono break-all">{config?.model}</div>
                                {activeModel.description && (
                                    <p className="text-sm text-text-secondary mt-2">{activeModel.description}</p>
                                )}
                            </div>
                            <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-1 rounded-sm text-xs font-bold uppercase tracking-wider flex items-center gap-1 shrink-0">
                                <Check className="w-3 h-3" /> Active
                            </span>
                        </div>

                        <div className="flex gap-4 mb-4 text-sm border-b border-clinical-border pb-4">
                            <div className="flex flex-col">
                                <span className="text-text-muted text-xs uppercase">Size</span>
                                <span className="text-white">{activeModel.size}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-text-muted text-xs uppercase">Device</span>
                                <span className="text-white uppercase">{config?.device}</span>
                            </div>
                        </div>

                        <div>
                            <p className="text-xs text-text-secondary uppercase mb-2 font-medium">Available Models</p>
                            <div className="space-y-2">
                                {models.filter(m => m.id !== config?.model).map((m: any) => (
                                    <div key={m.id} className="flex items-center justify-between text-sm p-3 border border-clinical-border/50 rounded-sm hover:bg-clinical-bg/50 transition-colors">
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <span className="text-text-secondary font-medium">{m.name}</span>
                                                <span className="text-text-muted font-mono text-xs border border-clinical-border px-1 rounded-sm">{m.size}</span>
                                            </div>
                                            <div className="text-xs text-text-muted mt-1">{m.description}</div>
                                        </div>
                                        <button
                                            onClick={() => handleActivate(m.id)}
                                            disabled={!!switchingId}
                                            className="btn btn-secondary text-xs h-8 px-3 ml-4 shrink-0 transition-opacity disabled:opacity-50"
                                        >
                                            {switchingId === m.id ? (
                                                <Loader2 className="w-3 h-3 animate-spin" />
                                            ) : "Activate"}
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </Section>

                {/* System Settings */}
                <Section title="Runtime Environment" icon={Server}>
                    <div className="grid grid-cols-2 gap-4">
                        <ConfigItem label="Max Upload Size" value={`${config?.max_file_size_mb} MB`} />
                        <ConfigItem label="Batch Limit" value={`${config?.max_batch_size} items`} />
                        <ConfigItem label="Smart Merging" value={config?.use_smart_merging ? 'Enabled' : 'Disabled'} />
                        <ConfigItem label="Inference Backend" value={config?.device === 'cuda' ? 'NVIDIA CUDA' : 'CPU Optimized'} />
                    </div>
                </Section>

                {/* Storage Policy */}
                <Section title="Storage & Retention" icon={Database}>
                    <div className="p-4 bg-yellow-500/5 border border-yellow-500/10 rounded-md">
                        <p className="text-sm text-yellow-500 mb-2 font-medium">Zero-Retention Policy Active</p>
                        <p className="text-sm text-text-secondary">
                            The system is currently running in stateless mode. All uploaded documents are processed in-memory
                            or in temporary ephemeral storage and are securely wiped immediately after the request completes.
                        </p>
                    </div>
                </Section>
            </div>
        </div>
    )
}

function Section({ title, icon: Icon, children }: { title: string; icon: any; children: any }) {
    return (
        <div className="space-y-3">
            <div className="flex items-center gap-2 text-text-secondary">
                <Icon className="w-4 h-4" />
                <span className="text-sm font-medium uppercase tracking-wider">{title}</span>
            </div>
            {children}
        </div>
    )
}

function ConfigItem({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex justify-between p-3 border-b border-clinical-border last:border-0 border-clinical-bg">
            <span className="text-sm text-text-secondary">{label}</span>
            <span className="text-sm text-white font-mono">{value}</span>
        </div>
    )
}

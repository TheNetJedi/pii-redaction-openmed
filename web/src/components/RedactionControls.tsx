import { Eraser, Hash, Type, X } from 'lucide-react'
import clsx from 'clsx'

interface RedactionConfig {
    method: string
    confidence: number
}

interface Props {
    config: RedactionConfig
    onChange: (config: RedactionConfig) => void
    disabled?: boolean
}

export function RedactionControls({ config, onChange, disabled }: Props) {
    const methods = [
        { id: 'mask', label: 'Mask', icon: Eraser },
        { id: 'remove', label: 'Remove', icon: X },
        { id: 'replace', label: 'Replace', icon: Type },
        { id: 'hash', label: 'Hash', icon: Hash },
    ]

    return (
        <div className={clsx("space-y-6", disabled && "opacity-50 pointer-events-none")}>
            <div>
                <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2 block">Method</label>
                <div className="grid grid-cols-2 gap-2">
                    {methods.map(m => (
                        <MethodButton
                            key={m.id}
                            active={config.method === m.id}
                            onClick={() => onChange({ ...config, method: m.id })}
                            icon={m.icon}
                            label={m.label}
                        />
                    ))}
                </div>
            </div>

            <div>
                <div className="flex justify-between mb-2">
                    <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Confidence Threshold</label>
                    <span className="text-xs font-mono text-accent">{config.confidence}</span>
                </div>
                <input
                    type="range" min="0" max="1" step="0.05"
                    value={config.confidence}
                    onChange={e => onChange({ ...config, confidence: parseFloat(e.target.value) })}
                    className="w-full accent-accent cursor-pointer"
                />
            </div>
        </div>
    )
}

function MethodButton({ active, onClick, icon: Icon, label }: any) {
    return (
        <button
            onClick={onClick}
            className={clsx(
                "flex flex-col items-center justify-center p-3 rounded-lg border transition-all gap-2",
                active
                    ? "bg-accent text-white border-accent shadow-lg shadow-accent/20"
                    : "bg-clinical-bg border-clinical-border text-text-secondary hover:border-text-muted hover:bg-clinical-surface"
            )}
        >
            <Icon className="w-5 h-5" />
            <span className="text-[10px] font-medium uppercase">{label}</span>
        </button>
    )
}

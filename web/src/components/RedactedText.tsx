import { clsx } from 'clsx'

export function RedactedText({ text, className }: { text: string; className?: string }) {
    if (!text) return null
    return (
        <div className={clsx("whitespace-pre-wrap", className)}>
            {text.split(/(\[.*?\])/g).map((part, i) => {
                if (part.startsWith('[') && part.endsWith(']')) {
                    return (
                        <span
                            key={i}
                            className="bg-stone-800 text-stone-400 px-1 rounded mx-0.5 border border-stone-700 font-mono text-xs select-all"
                            title="Redacted Entity"
                        >
                            {part}
                        </span>
                    )
                }
                return <span key={i}>{part}</span>
            })}
        </div>
    )
}

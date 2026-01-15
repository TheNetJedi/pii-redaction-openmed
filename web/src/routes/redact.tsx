import { createFileRoute } from '@tanstack/react-router'
import { useState, useRef, useMemo } from 'react'
import {
    Upload, FileText, Check, Download, X,
    Copy, Loader2, Scan,
    Eye, EyeOff
} from 'lucide-react'
import clsx from 'clsx'
import { RedactionControls } from '../components/RedactionControls'
import { EntityList } from '../components/EntityList'
import { RedactedText } from '../components/RedactedText'

export const Route = createFileRoute('/redact')({
    component: RedactorRoute,
})

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function RedactorRoute() {
    return <RedactWorkspace />
}

function RedactWorkspace() {
    const [input, setInput] = useState('')
    const [file, setFile] = useState<File | null>(null)
    const [result, setResult] = useState<any>(null)
    const [analysis, setAnalysis] = useState<{ by_type: Record<string, number>, total: number } | null>(null)
    const [loading, setLoading] = useState(false)

    // View state
    const [viewMode, setViewMode] = useState<'original' | 'redacted'>('original')

    // Config state
    const [config, setConfig] = useState({
        method: 'mask',
        confidence: 0.6
    })

    // Entity Selection State
    const [selectedEntities, setSelectedEntities] = useState<string[]>([])

    // Drag & Drop refs
    const dragCounter = useRef(0)
    const [isDragging, setIsDragging] = useState(false)
    const fileInputRef = useRef<HTMLInputElement>(null)

    // Handlers
    const handleFileSelect = (uploadedFile: File) => {
        setFile(uploadedFile)
        resetState()
    }

    const resetState = () => {
        setResult(null)
        setAnalysis(null)
        setViewMode('original')
        setSelectedEntities([])
    }

    const handleReset = () => {
        setInput('')
        setFile(null)
        resetState()
        if (fileInputRef.current) fileInputRef.current.value = ''
    }

    const handleScan = async () => {
        setLoading(true)
        setAnalysis(null)
        setResult(null)

        try {
            if (file) {
                const formData = new FormData()
                formData.append('file', file)

                const res = await fetch(`${API_URL}/api/v1/documents/analyze`, {
                    method: 'POST', body: formData
                })

                if (!res.ok) throw new Error('Analysis failed')

                const data = await res.json()
                setAnalysis({ by_type: data.by_type, total: data.total_entities })
                setSelectedEntities(data.all_types)

            } else if (input.trim()) {
                const res = await fetch(`${API_URL}/api/v1/extract`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: input,
                        config: { confidence_threshold: config.confidence }
                    })
                })

                if (!res.ok) throw new Error('Extraction failed')

                const entities = await res.json()
                const stats: Record<string, number> = {}
                entities.forEach((e: any) => {
                    stats[e.label] = (stats[e.label] || 0) + 1
                })

                setAnalysis({ by_type: stats, total: entities.length })
                setSelectedEntities(Object.keys(stats).sort())
            }
        } catch (e) {
            console.error(e)
            // Ideally show toast error
        } finally {
            setLoading(false)
        }
    }

    const handleRedact = async () => {
        setLoading(true)
        try {
            const entityTypesPayload = analysis ? selectedEntities : null

            if (file) {
                const formData = new FormData()
                formData.append('file', file)
                formData.append('method', config.method)
                formData.append('confidence_threshold', config.confidence.toString())
                if (entityTypesPayload) {
                    formData.append('entity_types', entityTypesPayload.join(','))
                }

                const res = await fetch(`${API_URL}/api/v1/documents/redact`, {
                    method: 'POST', body: formData
                })

                if (!res.ok) throw new Error('Failed')

                const blob = await res.blob()
                const url = URL.createObjectURL(blob)
                const count = res.headers.get('X-Entity-Count')

                setResult({
                    type: 'file',
                    fileType: file.name.toLowerCase().endsWith('.pdf') ? 'pdf' : 'other',
                    count: count || 0,
                    url,
                    filename: `redacted_${file.name}`
                })
                setViewMode('redacted')
            } else if (input.trim()) {
                const res = await fetch(`${API_URL}/api/v1/redact/text`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: input,
                        config: {
                            method: config.method,
                            confidence_threshold: config.confidence,
                            entity_types: entityTypesPayload
                        }
                    })
                })

                if (!res.ok) throw new Error('Redaction failed')

                const data = await res.json()
                setResult(data)
                setViewMode('redacted')
            }
        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }

    const toggleEntityType = (type: string) => {
        setSelectedEntities(prev =>
            prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
        )
    }

    // Drag handlers
    const handleDragEnter = (e: React.DragEvent) => {
        e.preventDefault(); e.stopPropagation(); dragCounter.current += 1
        if (e.dataTransfer.items?.length > 0) setIsDragging(true)
    }
    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault(); e.stopPropagation(); dragCounter.current -= 1
        if (dragCounter.current === 0) setIsDragging(false)
    }
    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault(); e.stopPropagation(); setIsDragging(false); dragCounter.current = 0
        if (e.dataTransfer.files?.length > 0) handleFileSelect(e.dataTransfer.files[0])
    }

    const hasResult = !!result

    // Stable URLs for PDF preview to prevent reload
    const originalFileUrl = useMemo(() => file ? URL.createObjectURL(file) : null, [file])

    return (
        <div
            className="flex flex-col md:flex-row h-[calc(100vh-100px)] gap-6"
            onDragEnter={handleDragEnter} onDragOver={(e) => e.preventDefault()} onDragLeave={handleDragLeave} onDrop={handleDrop}
        >
            {isDragging && !file && (
                <div className="absolute inset-0 z-50 bg-accent/20 backdrop-blur-sm border-4 border-accent border-dashed m-4 rounded-xl flex items-center justify-center pointer-events-none">
                    <div className="bg-clinical-bg p-8 rounded-full border border-accent shadow-2xl animate-bounce">
                        <Upload className="w-12 h-12 text-accent" />
                    </div>
                </div>
            )}

            {/* Left Panel: Workspace */}
            <div className="flex-1 flex flex-col min-w-0 bg-clinical-surface/50 border border-clinical-border rounded-xl shadow-sm overflow-hidden backdrop-blur-sm relative group">

                {/* View Toggles (Floating) */}
                {hasResult && (
                    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-40 bg-clinical-bg/90 backdrop-blur border border-clinical-border rounded-full p-1 flex shadow-xl">
                        <button onClick={() => setViewMode('original')} className={clsx("px-4 py-1.5 text-xs font-medium rounded-full transition-all flex items-center gap-2", viewMode === 'original' ? "bg-clinical-surface text-white shadow-sm" : "text-text-muted hover:text-white")}>
                            <EyeOff className="w-3.5 h-3.5" /> Original
                        </button>
                        <button onClick={() => setViewMode('redacted')} className={clsx("px-4 py-1.5 text-xs font-medium rounded-full transition-all flex items-center gap-2 text-emerald-400", viewMode === 'redacted' ? "bg-clinical-surface shadow-sm font-bold" : "hover:bg-clinical-surface/50")}>
                            <Eye className="w-3.5 h-3.5" /> Redacted
                        </button>
                    </div>
                )}

                {/* Close/Reset Button */}
                {(file || input || result) && (
                    <button onClick={handleReset} className="absolute top-4 right-4 z-40 p-2 bg-clinical-bg/80 backdrop-blur border border-clinical-border rounded-lg text-text-muted hover:text-white hover:bg-clinical-surface cursor-pointer shadow-sm transition-all">
                        <X className="w-5 h-5" />
                    </button>
                )}

                {/* Content Area */}
                <div className="flex-1 relative bg-clinical-bg/30 overflow-hidden flex flex-col">
                    {!file ? (
                        // Initial "Dashboard" State
                        !input && !result ? (
                            <div className="flex-1 flex flex-col items-center justify-center p-8 animate-in fade-in zoom-in duration-300">
                                <div
                                    className={clsx(
                                        "w-full max-w-lg bg-clinical-surface/30 border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center text-center transition-all group cursor-pointer",
                                        isDragging ? "border-accent bg-accent/5 scale-105" : "border-clinical-border hover:border-text-secondary hover:bg-clinical-surface/50"
                                    )}
                                    onClick={() => fileInputRef.current?.click()}
                                >
                                    <div className="p-4 rounded-full bg-clinical-bg border border-clinical-border mb-4 group-hover:scale-110 transition-transform shadow-sm">
                                        <Upload className="w-8 h-8 text-text-muted group-hover:text-white transition-colors" />
                                    </div>
                                    <h3 className="text-xl font-medium text-white mb-2">Upload Document</h3>
                                    <p className="text-sm text-text-muted mb-6 max-w-xs leading-relaxed">
                                        Drag & drop PDF, DOCX, or TXT files here to detect and redact sensitive data.
                                    </p>
                                    <div className="btn btn-secondary text-xs px-6">Select File</div>
                                    <input ref={fileInputRef} type="file" className="hidden" accept=".pdf,.docx,.txt" onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])} />
                                </div>

                                <div className="mt-8 flex items-center gap-4 w-full max-w-sm opacity-50">
                                    <div className="h-px bg-clinical-border flex-1" />
                                    <span className="text-[10px] text-text-muted uppercase font-medium tracking-widest">Or Type Manually</span>
                                    <div className="h-px bg-clinical-border flex-1" />
                                </div>

                                <div className="mt-6 w-full max-w-lg relative group">
                                    <textarea
                                        value={input}
                                        onChange={e => { setInput(e.target.value); if (analysis) setAnalysis(null); }}
                                        placeholder="Paste clinical notes or text here..."
                                        className="w-full h-32 bg-clinical-surface/30 border border-clinical-border rounded-xl p-4 font-mono text-sm resize-none focus:outline-none focus:border-accent/50 focus:bg-clinical-surface transition-all placeholder-text-muted/40"
                                    />
                                    {input.trim() && (
                                        <div className="absolute bottom-3 right-3 flex items-center gap-2">
                                            <span className="text-[10px] text-text-muted">Press Scan to continue</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ) : (
                            // Text Input/Result Mode (Full Screen)
                            <div className="flex-1 relative flex flex-col">
                                {viewMode === 'original' && (
                                    <textarea
                                        value={input}
                                        onChange={e => { setInput(e.target.value); if (analysis) setAnalysis(null); }}
                                        className="flex-1 w-full bg-transparent p-8 font-mono text-sm resize-none focus:outline-none placeholder-text-muted/30 leading-relaxed text-text-primary"
                                        spellCheck={false}
                                        placeholder="Type here..."
                                    />
                                )}
                                {hasResult && viewMode === 'redacted' && (
                                    <div className="flex-1 w-full p-8 font-mono text-sm leading-relaxed overflow-auto bg-clinical-bg">
                                        <RedactedText text={result.redacted_text} />
                                    </div>
                                )}
                            </div>
                        )
                    ) : (
                        // File Loaded View (Full Size)
                        <div className="absolute inset-0 flex flex-col">
                            {/* Original Preview */}
                            <div className={clsx("absolute inset-0 flex flex-col bg-white", viewMode === 'original' ? "z-10 visible" : "z-0 invisible")}>
                                {file.name.toLowerCase().endsWith('.pdf') && originalFileUrl ? (
                                    <iframe src={originalFileUrl} className="flex-1 w-full border-0" title="Original" />
                                ) : (
                                    <div className="flex-1 flex flex-col items-center justify-center bg-clinical-bg">
                                        <FileText className="w-16 h-16 text-text-secondary mb-4" />
                                        <p className="text-lg text-white font-medium">{file.name}</p>
                                        <p className="text-sm text-text-muted">Preview not available for this format</p>
                                    </div>
                                )}
                            </div>

                            {/* Redacted Preview */}
                            <div className={clsx("absolute inset-0 flex flex-col bg-white", viewMode === 'redacted' ? "z-20 visible" : "z-0 invisible")}>
                                {result?.url && file.name.toLowerCase().endsWith('.pdf') ? (
                                    <iframe src={result.url} className="flex-1 w-full border-0" title="Redacted" />
                                ) : (
                                    <div className="flex-1 flex flex-col items-center justify-center bg-clinical-bg">
                                        <Check className="w-16 h-16 text-emerald-500 mb-4" />
                                        <p className="text-lg text-white font-medium">Redaction Complete</p>
                                        {result?.filename && <p className="text-sm text-text-muted mt-2">{result.filename}</p>}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Right Panel: Controls */}
            <div className="w-full md:w-80 flex flex-col gap-4 shrink-0">
                <div className="bg-clinical-surface border border-clinical-border rounded-xl p-5 shadow-sm space-y-6">

                    {/* Phase 1: Configuration */}
                    {!result && (
                        <RedactionControls config={config} onChange={setConfig} />
                    )}

                    {/* Phase 2: Analysis & Review */}
                    {analysis ? (
                        <>
                            <EntityList stats={analysis.by_type} selected={selectedEntities} onToggle={toggleEntityType} />

                            {!result && (
                                <button
                                    onClick={handleRedact}
                                    disabled={loading || selectedEntities.length === 0}
                                    className={clsx("w-full btn btn-primary h-10 shadow-lg shadow-accent/20", loading && "opacity-80")}
                                >
                                    {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Confirm Redaction"}
                                </button>
                            )}
                        </>
                    ) : (
                        // Phase 0: Initial Scan Button
                        !result && (
                            <button
                                onClick={handleScan}
                                disabled={loading || (!input && !file)}
                                className={clsx("w-full btn btn-primary h-12 text-base font-semibold shadow-xl shadow-accent/10 transition-all", loading && "opacity-80 cursor-wait", (!input && !file) && "opacity-50 cursor-not-allowed")}
                            >
                                {loading ? <div className="flex items-center justify-center gap-2"><Loader2 className="animate-spin w-5 h-5" /> Scanning...</div> : <div className="flex items-center justify-center gap-2"><Scan className="w-4 h-4" /> Scan for PII</div>}
                            </button>
                        )
                    )}

                    {/* Phase 3: Result Actions */}
                    {result && (
                        <div className="animate-in fade-in space-y-4 pt-4 border-t border-clinical-border">
                            <div className="flex items-center gap-2 text-emerald-400 justify-center">
                                <Check className="w-5 h-5" />
                                <span className="font-medium">Redaction Applied</span>
                            </div>

                            {result.url && (result.type === 'file' || result.fileType === 'pdf') ? (
                                <a href={result.url} download={result.filename} className="btn bg-emerald-500 hover:bg-emerald-600 text-white w-full h-10 shadow-lg shadow-emerald-500/20 border-0 flex items-center justify-center gap-2">
                                    <Download className="w-4 h-4" /> Download Result
                                </a>
                            ) : null}

                            {result.redacted_text && (
                                <button onClick={() => navigator.clipboard.writeText(result.redacted_text)} className="btn btn-secondary w-full h-10 flex items-center justify-center gap-2">
                                    <Copy className="w-4 h-4" /> Copy Text
                                </button>
                            )}

                            <button onClick={handleReset} className="btn btn-ghost w-full">Start Over</button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

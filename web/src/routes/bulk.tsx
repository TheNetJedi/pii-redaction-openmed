import { createFileRoute } from '@tanstack/react-router'
import { useState, useRef } from 'react'
import {
    Upload, FileText, Check, Download, X,
    Loader2, Scan, Trash2, AlertCircle, Eraser
} from 'lucide-react'
import clsx from 'clsx'
import { RedactionControls } from '../components/RedactionControls'
import { EntityList } from '../components/EntityList'

export const Route = createFileRoute('/bulk')({
    component: BulkPage,
})

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

type BatchItem = {
    id: string
    file: File
    status: 'pending' | 'analyzing' | 'analyzed' | 'processing' | 'completed' | 'error'
    stats?: Record<string, number>
    totalEntities?: number
    resultUrl?: string
    error?: string
}

function BulkPage() {
    const [queue, setQueue] = useState<BatchItem[]>([])
    const [loading, setLoading] = useState(false)
    const [processingStep, setProcessingStep] = useState<'idle' | 'scanning' | 'redacting'>('idle')

    // Config
    const [config, setConfig] = useState({
        method: 'mask',
        confidence: 0.6
    })

    const [selectedEntities, setSelectedEntities] = useState<string[]>([])
    const [aggregateStats, setAggregateStats] = useState<Record<string, number>>({})

    const fileInputRef = useRef<HTMLInputElement>(null)
    const [isDragging, setIsDragging] = useState(false)
    const dragCounter = useRef(0)

    // Handlers
    const handleFilesAdd = (files: FileList | null) => {
        if (!files) return
        const newItems: BatchItem[] = Array.from(files).map(f => ({
            id: Math.random().toString(36).substring(7),
            file: f,
            status: 'pending'
        }))
        setQueue(prev => [...prev, ...newItems])
    }

    const removeItem = (id: string) => {
        setQueue(prev => prev.filter(i => i.id !== id))
    }

    const resetState = () => {
        setQueue([])
        setAggregateStats({})
        setSelectedEntities([])
        setProcessingStep('idle')
    }

    // Logic
    const scanQueue = async () => {
        setLoading(true)
        setProcessingStep('scanning')

        let newAggregate = { ...aggregateStats }
        let allTypes = new Set(selectedEntities)

        // Process only pending items
        const newQueue = [...queue]
        for (let i = 0; i < newQueue.length; i++) {
            const item = newQueue[i]
            if (item.status === 'analyzed' || item.status === 'completed') continue

            // Update item status to analyzing
            newQueue[i] = { ...item, status: 'analyzing' }
            setQueue([...newQueue])

            try {
                const formData = new FormData()
                formData.append('file', item.file)

                const res = await fetch(`${API_URL}/api/v1/documents/analyze`, { method: 'POST', body: formData })
                if (!res.ok) throw new Error('Failed')

                const data = await res.json()

                // Update stats
                newQueue[i] = {
                    ...item,
                    status: 'analyzed',
                    stats: data.by_type,
                    totalEntities: data.total_entities
                }

                // Aggregate
                Object.entries(data.by_type as Record<string, number>).forEach(([type, count]) => {
                    newAggregate[type] = (newAggregate[type] || 0) + count
                    allTypes.add(type)
                })

            } catch (e) {
                newQueue[i] = { ...item, status: 'error', error: 'Scan failed' }
            }
            // Update queue incrementally
            setQueue([...newQueue])
        }

        setAggregateStats(newAggregate)
        setSelectedEntities(Array.from(allTypes).sort())
        setLoading(false)
        setProcessingStep('idle')
    }

    const processRedaction = async () => {
        setLoading(true)
        setProcessingStep('redacting')

        const entityTypesPayload = Object.keys(aggregateStats).length > 0 ? selectedEntities : null

        const newQueue = [...queue]
        for (let i = 0; i < newQueue.length; i++) {
            const item = newQueue[i]
            // Skip already redacted or errored
            if (item.status === 'completed' || item.status === 'error') continue

            newQueue[i] = { ...item, status: 'processing' }
            setQueue([...newQueue])

            try {
                const formData = new FormData()
                formData.append('file', item.file)
                formData.append('method', config.method)
                formData.append('confidence_threshold', config.confidence.toString())
                if (entityTypesPayload) {
                    formData.append('entity_types', entityTypesPayload.join(','))
                }

                const res = await fetch(`${API_URL}/api/v1/documents/redact`, { method: 'POST', body: formData })

                if (res.ok) {
                    const blob = await res.blob()
                    const url = URL.createObjectURL(blob)
                    newQueue[i] = { ...item, status: 'completed', resultUrl: url }
                } else {
                    throw new Error('Failed')
                }
            } catch (e) {
                newQueue[i] = { ...item, status: 'error', error: 'Redaction failed' }
            }
            setQueue([...newQueue])
        }

        setLoading(false)
        setProcessingStep('idle')
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
        if (e.dataTransfer.files?.length > 0) handleFilesAdd(e.dataTransfer.files)
    }

    // Computed
    const canScan = queue.some(i => i.status === 'pending')
    const canRedact = queue.some(i => i.status === 'analyzed' || i.status === 'pending')
    const hasAnalysis = Object.keys(aggregateStats).length > 0

    return (
        <div
            className="flex flex-col md:flex-row h-[calc(100vh-100px)] gap-6"
            onDragEnter={handleDragEnter} onDragOver={(e) => e.preventDefault()} onDragLeave={handleDragLeave} onDrop={handleDrop}
        >
            {isDragging && queue.length > 0 && (
                <div className="absolute inset-0 z-50 bg-accent/20 backdrop-blur-sm border-4 border-accent border-dashed m-4 rounded-xl flex items-center justify-center pointer-events-none">
                    <div className="bg-clinical-bg p-8 rounded-full border border-accent shadow-2xl animate-bounce">
                        <Upload className="w-12 h-12 text-accent" />
                    </div>
                </div>
            )}

            {/* Left Panel: Queue */}
            <div className="flex-1 flex flex-col min-w-0 bg-clinical-surface/50 border border-clinical-border rounded-xl shadow-sm overflow-hidden backdrop-blur-sm relative flex-col">
                {/* Header */}
                <div className="h-14 border-b border-clinical-border flex items-center justify-between px-4 bg-clinical-surface">
                    <span className="font-medium text-white flex items-center gap-2">
                        Batch Queue <span className="px-2 py-0.5 rounded-full bg-clinical-bg text-xs text-text-muted">{queue.length}</span>
                    </span>
                    {queue.length > 0 && (
                        <button onClick={resetState} className="text-xs text-text-muted hover:text-red-400 flex items-center gap-1">
                            <Trash2 className="w-3.5 h-3.5" /> Clear All
                        </button>
                    )}
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto bg-clinical-bg/30 p-4">
                    {queue.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center">
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
                                <h3 className="text-xl font-medium text-white mb-2">Upload Multiple Files</h3>
                                <p className="text-sm text-text-muted mb-6 max-w-xs leading-relaxed">
                                    Queue multiple documents for batch PII scanning and redaction.
                                </p>
                                <div className="btn btn-secondary text-xs px-6">Select Files</div>
                                <input ref={fileInputRef} type="file" multiple className="hidden" accept=".pdf,.docx,.txt" onChange={(e) => handleFilesAdd(e.target.files)} />
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {queue.map(item => (
                                <div key={item.id} className="bg-clinical-bg border border-clinical-border rounded-lg p-3 flex items-center justify-between group hover:border-accent/30 transition-colors">
                                    <div className="flex items-center gap-3 min-w-0">
                                        <div className="p-2 bg-clinical-surface rounded border border-clinical-border">
                                            <FileText className="w-5 h-5 text-gray-400" />
                                        </div>
                                        <div className="min-w-0">
                                            <div className="text-sm font-medium text-white truncate max-w-[200px] sm:max-w-md">{item.file.name}</div>
                                            <div className="text-[10px] text-text-muted flex items-center gap-2">
                                                {(item.file.size / 1024).toFixed(1)} KB
                                                {item.totalEntities !== undefined && (
                                                    <span className="text-accent">• {item.totalEntities} PII Found</span>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-4">
                                        {/* Status Indicators */}
                                        {item.status === 'analyzing' && <div className="flex items-center gap-2 text-xs text-accent"><Loader2 className="w-3.5 h-3.5 animate-spin" /> Scanning...</div>}
                                        {item.status === 'processing' && <div className="flex items-center gap-2 text-xs text-accent"><Loader2 className="w-3.5 h-3.5 animate-spin" /> Redacting...</div>}
                                        {item.status === 'completed' && <div className="flex items-center gap-2 text-xs text-emerald-400"><Check className="w-3.5 h-3.5" /> Done</div>}
                                        {item.status === 'error' && <div className="flex items-center gap-2 text-xs text-red-400"><AlertCircle className="w-3.5 h-3.5" /> Failed</div>}

                                        {/* Actions */}
                                        {item.status === 'completed' && item.resultUrl && (
                                            <a href={item.resultUrl} download={`redacted_${item.file.name}`} className="btn btn-xs btn-ghost text-emerald-400 hover:bg-emerald-400/10">
                                                <Download className="w-4 h-4" />
                                            </a>
                                        )}

                                        <button onClick={() => removeItem(item.id)} className="text-text-muted hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <X className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            ))}
                            {/* Drag Tip */}
                            <div
                                className="border-2 border-dashed border-clinical-border/50 rounded-lg p-6 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-clinical-surface/30 hover:border-clinical-border transition-colors -my-1"
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <span className="text-xs text-text-muted">+ Add more files</span>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Right Panel: Controls */}
            <div className="w-full md:w-80 flex flex-col gap-4 shrink-0">
                <div className="bg-clinical-surface border border-clinical-border rounded-xl p-5 shadow-sm space-y-6">

                    {/* Method Config */}
                    <RedactionControls config={config} onChange={setConfig} />

                    {/* Actions */}
                    <div className="space-y-3 pt-2 border-t border-clinical-border">
                        <button
                            onClick={scanQueue}
                            disabled={loading || !canScan}
                            className={clsx(
                                "w-full btn h-10 border border-accent/20 text-accent hover:bg-accent/5",
                                loading && "opacity-50",
                                !canScan && "opacity-50 cursor-not-allowed"
                            )}
                        >
                            {loading && processingStep === 'scanning' ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Scan className="w-4 h-4 mr-2" />}
                            Scan Pending ({queue.filter(i => i.status === 'pending').length})
                        </button>

                        <button
                            onClick={processRedaction}
                            disabled={loading || !canRedact}
                            className={clsx(
                                "w-full btn btn-primary h-10 shadow-lg shadow-accent/20",
                                loading && "opacity-50",
                                !canRedact && "opacity-50 cursor-not-allowed"
                            )}
                        >
                            {loading && processingStep === 'redacting' ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Eraser className="w-4 h-4 mr-2" />}
                            Process Batch
                        </button>
                    </div>

                    {/* Aggregate Stats */}
                    {hasAnalysis && (
                        <EntityList
                            stats={aggregateStats}
                            selected={selectedEntities}
                            onToggle={toggleEntityType}
                        />
                    )}
                </div>
            </div>
        </div>
    )
}

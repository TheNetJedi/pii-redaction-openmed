import {
    CheckSquare, Square,
    User, Mail, Phone, CreditCard, Calendar, MapPin, Building2,
    Globe, Lock, Tag, Stethoscope
} from 'lucide-react'
import clsx from 'clsx'

const ICON_MAP: Record<string, typeof Tag> = {
    // Person
    first_name: User,
    last_name: User,
    middle_name: User,
    full_name: User,
    name: User,
    gender: User,

    // Contact
    email: Mail,
    phone_number: Phone,
    fax_number: Phone,

    // Financial/ID
    credit_debit_card: CreditCard,
    bank_account: CreditCard,
    ssn: Lock,
    passport: Lock,
    driver_license: Lock,
    tax_id: Lock,
    medical_record_number: Stethoscope,

    // Location
    address: MapPin,
    street_address: MapPin,
    city: MapPin,
    state: MapPin,
    zipcode: MapPin,
    country: MapPin,

    // Time
    date: Calendar,
    date_of_birth: Calendar,
    time: Calendar,
    age: Calendar,

    // Network
    url: Globe,
    ip_address: Globe,
    mac_address: Globe,
    email_address: Mail,

    // Misc
    organization: Building2,
    hospital: Building2,
}

interface Props {
    stats: Record<string, number> // Type -> Count
    selected: string[]
    onToggle: (type: string) => void
    total?: number
    className?: string
}

export function EntityList({ stats, selected, onToggle, total, className }: Props) {
    const totalCount = total ?? Object.values(stats).reduce((a, b) => a + b, 0)

    return (
        <div className={clsx("animate-in fade-in slide-in-from-right-4 space-y-4", className)}>
            <div className="flex items-center justify-between border-b border-clinical-border pb-2">
                <span className="text-sm font-medium text-white">Detected PII</span>
                <span className="text-xs text-text-muted">{totalCount} Found</span>
            </div>
            <div className="max-h-[300px] overflow-y-auto space-y-1 pr-1 custom-scrollbar">
                {Object.entries(stats).map(([type, count]) => {
                    const TypeIcon = ICON_MAP[type.toLowerCase()] || Tag

                    return (
                        <button
                            key={type}
                            onClick={() => onToggle(type)}
                            className="w-full flex items-center justify-between p-2 rounded hover:bg-clinical-bg/50 group text-left transition-colors"
                        >
                            <div className="flex items-center gap-3">
                                {selected.includes(type)
                                    ? <CheckSquare className="w-4 h-4 text-accent shrink-0" />
                                    : <Square className="w-4 h-4 text-text-muted group-hover:text-text-secondary shrink-0" />}

                                <div className="flex items-center gap-2 min-w-0">
                                    <TypeIcon className="w-3.5 h-3.5 text-text-muted/70" />
                                    <span className={clsx(
                                        "text-xs font-mono transition-colors truncate",
                                        selected.includes(type) ? "text-white" : "text-text-muted"
                                    )}>
                                        {type}
                                    </span>
                                </div>
                            </div>
                            <span className="text-[10px] bg-clinical-bg px-1.5 py-0.5 rounded-full border border-clinical-border/50 text-text-secondary min-w-[20px] text-center">
                                {count}
                            </span>
                        </button>
                    )
                })}
            </div>
        </div>
    )
}

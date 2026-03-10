"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { encounterApi, patientsApi, getErrorMessage } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/ui/Toast';
import Link from 'next/link';
import {
    ChevronLeft, Brain, Zap, CheckCircle, AlertTriangle, Clock,
    Pill, Stethoscope, CreditCard, Calendar, Shield,
    Loader2, RefreshCw, ChevronDown, ChevronUp, AlertCircle,
    CheckSquare, FileText, Activity, Link2, BookOpen, Microscope,
    Repeat, BrainCircuit, Lock, ExternalLink
} from 'lucide-react';

/* ─────────────────── Types ─────────────────── */
interface Medication { id: number; name: string; dosage?: string; frequency?: string; route?: string; duration?: string; start_date_text?: string; requires_confirmation: boolean; fields_required: string[]; confidence: string; }
interface Diagnosis { id: number; condition_name: string; icd10_code?: string; confidence_score: number; reasoning?: string; is_primary: boolean; }
interface Procedure { id: number; name: string; code?: string; notes?: string; confidence: string; }
interface BillingItem { id: number; cpt_code?: string; description: string; estimated_cost?: number; complexity: string; confidence: number; requires_review: boolean; review_reason?: string; }
interface TimelineEvent { id: number; event_type: string; event_description: string; event_date_text?: string; severity: string; }
interface Followup { id: number; recommendation: string; follow_up_type?: string; urgency: string; suggested_days?: number; }
interface QualityReport {
    confidence_score: number;
    compliance_score: number;
    risk_level: string;
    evidence_mode_enabled: boolean;
    rationale_json: any;
    drug_safety_flags: any;
    structured_risk_metrics: any;
    guideline_flags: any;
    differential_output: any;
    lab_interpretation: any;
    handoff_sbar: any;
    clinical_safety_flags: any;
    hallucination_flags: string[];
    missing_critical_fields: string[];
}
interface Encounter {
    encounter_id: number; patient_id: number; status: string; is_confirmed: boolean;
    encounter_date: string; chief_complaint: string;
    soap: Record<string, string>; medications: Medication[]; diagnoses: Diagnosis[];
    procedures: Procedure[];
    billing: BillingItem[]; timeline_events: TimelineEvent[]; followups: Followup[];
    risk_score: string; risk_flags: string[]; legal_flags: string[];
    admission_required: boolean; icu_required: boolean; follow_up_days?: number;
    case_status: string; billing_complexity: string; ai_watermark: string; created_at: string;
}

/* ─────────────────── Helpers ─────────────────── */
const RISK_COLORS: Record<string, string> = {
    High: 'text-red-600 bg-red-50 border-red-200',
    Medium: 'text-amber-600 bg-amber-50 border-amber-200',
    Low: 'text-emerald-600 bg-emerald-50 border-emerald-200',
};
const URGENCY_COLORS: Record<string, string> = {
    stat: 'bg-red-100 text-red-700',
    urgent: 'bg-amber-100 text-amber-700',
    routine: 'bg-slate-100 text-slate-600',
};
const SEVERITY_COLORS: Record<string, string> = {
    high: 'border-l-red-500',
    medium: 'border-l-amber-500',
    low: 'border-l-blue-400',
    info: 'border-l-slate-300',
};

function ConfidenceBar({ score }: { score: number }) {
    const pct = Math.round(score * 100);
    const color = pct >= 75 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-400' : 'bg-red-400';
    return (
        <div className="flex items-center gap-2 mt-1">
            <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
            </div>
            <span className="text-[10px] font-bold text-slate-400 w-8">{pct}%</span>
        </div>
    );
}

function Section({ title, icon, children, badge }: { title: string; icon: React.ReactNode; children: React.ReactNode; badge?: number }) {
    const [open, setOpen] = useState(true);
    return (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <button onClick={() => setOpen(o => !o)} className="w-full flex items-center justify-between px-6 py-4 hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-3">
                    <div className="text-teal-600">{icon}</div>
                    <span className="font-black text-slate-900 text-sm tracking-tight">{title}</span>
                    {badge !== undefined && badge > 0 && (
                        <span className="px-2 py-0.5 bg-teal-100 text-teal-700 rounded-full text-[10px] font-black">{badge}</span>
                    )}
                </div>
                {open ? <ChevronUp size={16} className="text-slate-400" /> : <ChevronDown size={16} className="text-slate-400" />}
            </button>
            {open && <div className="px-6 pb-6 pt-2 border-t border-slate-50">{children}</div>}
        </div>
    );
}

/* ─────────────────── Main Page ─────────────────── */
export default function EncounterGeneratorPage() {
    const { id } = useParams();
    const router = useRouter();
    const { user } = useAuth();
    const { showToast } = useToast();

    const [patient, setPatient] = useState<any>(null);
    const [rawNote, setRawNote] = useState('');
    const [encounterDate, setEncounterDate] = useState(new Date().toISOString().split('T')[0]);
    const [encounter, setEncounter] = useState<Encounter | null>(null);
    const [qualityReport, setQualityReport] = useState<QualityReport | null>(null);
    const [evidenceModeEnabled, setEvidenceModeEnabled] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [confirming, setConfirming] = useState(false);
    const [progress, setProgress] = useState<string[]>([]);
    const [wsStatus, setWsStatus] = useState<'idle' | 'connecting' | 'connected' | 'done'>('idle');
    const wsRef = useRef<WebSocket | null>(null);

    /* load patient */
    useEffect(() => {
        if (id) patientsApi.getById(id as string).then(r => setPatient(r.data)).catch(() => { });
    }, [id]);

    /* ── WebSocket setup ── */
    const connectWs = (encounterId: number) => {
        setWsStatus('connecting');
        const url = encounterApi.wsUrl(encounterId);
        const ws = new WebSocket(url);
        wsRef.current = ws;
        ws.onopen = () => { setWsStatus('connected'); addProgress('🔌 Real-time connection established'); };
        ws.onmessage = (evt) => {
            try {
                const msg = JSON.parse(evt.data);
                if (msg.event === 'encounter_ready') { addProgress('✅ Encounter data ready'); setWsStatus('done'); }
                if (msg.event === 'encounter_confirmed') { addProgress('✅ Encounter confirmed & saved'); }
            } catch { }
        };
        ws.onerror = () => { setWsStatus('done'); };
        ws.onclose = () => { setWsStatus(s => s === 'connected' ? 'done' : s); };
    };

    const addProgress = (msg: string) => setProgress(p => [...p, msg]);

    /* ── Generate encounter ── */
    const handleGenerate = async () => {
        if (!rawNote.trim() || rawNote.trim().length < 10) {
            showToast('Please enter at least 10 characters for the note.', 'error');
            return;
        }
        setGenerating(true);
        setProgress([]);
        setEncounter(null);
        addProgress('🚀 Initiating Clinical Intelligence Pipeline...');
        addProgress('⚡ Running 6 parallel AI pipelines simultaneously...');

        const pipeline_msgs = [
            '📋 SOAP structuring pipeline...',
            '💊 Medication extraction & structuring...',
            '🔬 ICD-10 diagnosis coding...',
            '💳 Billing intelligence inference...',
            '🧠 Case intelligence analysis...',
            '⚖️ Medico-legal audit...',
        ];
        let idx = 0;
        const interval = setInterval(() => {
            if (idx < pipeline_msgs.length) addProgress(pipeline_msgs[idx++]);
            else clearInterval(interval);
        }, 600);

        try {
            const res = await encounterApi.generate({
                patient_id: Number(id),
                raw_note: rawNote,
                encounter_date: new Date(encounterDate).toISOString(),
                evidence_mode_enabled: evidenceModeEnabled,
            });
            clearInterval(interval);
            const enc: Encounter = res.data;
            setEncounter(enc);

            // Fetch Quality Report v2
            try {
                const qRes = await encounterApi.getQualityReport(enc.encounter_id);
                setQualityReport(qRes.data);
                addProgress('🛡️ Clinical Governance & Safety Audit complete');
            } catch (qErr) {
                console.error("Failed to load quality report", qErr);
            }

            addProgress(`✅ Encounter #${enc.encounter_id} generated in < 4 seconds`);
            addProgress('⚠️  Review all AI outputs before confirming.');
            connectWs(enc.encounter_id);
            showToast('AI Encounter generated! Review below.', 'success');
        } catch (err: any) {
            clearInterval(interval);
            const msg = getErrorMessage(err);
            addProgress(`❌ Error: ${msg}`);
            showToast(`Generation failed: ${msg}`, 'error');
        } finally {
            setGenerating(false);
        }
    };

    /* ── Confirm encounter ── */
    const handleConfirm = async () => {
        if (!encounter) return;
        setConfirming(true);
        try {
            const res = await encounterApi.confirm(encounter.encounter_id);
            addProgress('✅ Encounter confirmed & data promoted to clinical records');
            addProgress('📝 Clinical note saved');
            addProgress('💊 Medications activated');
            addProgress('🔬 Diagnoses added to medical history');
            addProgress('📋 Procedures recorded');
            setEncounter(e => e ? { ...e, is_confirmed: true, status: 'confirmed' } : e);
            showToast('Encounter confirmed. All data saved to patient record.', 'success');
        } catch (err: any) {
            showToast(getErrorMessage(err) || 'Confirmation failed', 'error');
        } finally {
            setConfirming(false);
        }
    };

    /* ─── Render ─── */
    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-teal-50/30">
            {/* Header */}
            <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-xl border-b border-slate-100 px-8 py-4 flex items-center justify-between shadow-sm">
                <div className="flex items-center gap-4">
                    <Link href={`/patients/${id}`} className="text-slate-400 hover:text-teal-600 transition-colors">
                        <ChevronLeft size={22} />
                    </Link>
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg shadow-teal-500/20">
                            <Brain size={20} className="text-white" />
                        </div>
                        <div>
                            <h1 className="text-lg font-black text-slate-900 leading-tight">Clinical Intelligence Engine</h1>
                            <p className="text-xs text-slate-400 font-medium">{patient?.name || 'Patient'} • AI-Driven Encounter Generation</p>
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    {wsStatus === 'connected' && (
                        <span className="flex items-center gap-1.5 text-xs text-emerald-600 font-bold">
                            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />Live
                        </span>
                    )}
                    {encounter && !encounter.is_confirmed && (
                        <button
                            onClick={handleConfirm}
                            disabled={confirming}
                            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-teal-600 to-cyan-600 text-white font-black text-sm rounded-xl shadow-lg shadow-teal-600/25 hover:shadow-xl hover:-translate-y-0.5 transition-all disabled:opacity-60"
                        >
                            {confirming ? <Loader2 size={16} className="animate-spin" /> : <CheckSquare size={16} />}
                            Confirm & Save to Records
                        </button>
                    )}
                    {encounter?.is_confirmed && (
                        <>
                            <Link
                                href={`/encounter/${encounter.encounter_id}/prescription`}
                                className="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white font-black text-sm rounded-xl shadow-md hover:bg-teal-700 transition-all"
                            >
                                <Pill size={16} /> Generate Prescription
                            </Link>
                            <span className="flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-700 font-black text-sm rounded-xl border border-emerald-200">
                                <CheckCircle size={16} /> Confirmed
                            </span>
                        </>
                    )}
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-8 py-8 grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-8">
                {/* Left panel — input */}
                <div className="space-y-6">
                    {/* Note input */}
                    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
                        <label className="text-xs font-black text-slate-400 uppercase tracking-[0.2em] block mb-3">Raw Clinical Note</label>
                        <textarea
                            value={rawNote}
                            onChange={e => setRawNote(e.target.value)}
                            rows={14}
                            placeholder="Paste or type the raw clinical note here...&#10;&#10;Example:&#10;Patient is a 58yo M presenting with 3-day history of productive cough, fever 38.5°C, and left lower lobe dullness. Started amoxicillin 500mg TID. CXR ordered. Follow-up in 7 days..."
                            className="w-full text-sm text-slate-800 placeholder-slate-300 border-0 resize-none focus:outline-none leading-relaxed font-mono"
                        />
                        <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-50">
                            <span className="text-xs text-slate-400">{rawNote.length} chars</span>
                            <div className="flex items-center gap-2">
                                <label className="text-xs text-slate-400">Date</label>
                                <input type="date" value={encounterDate} onChange={e => setEncounterDate(e.target.value)}
                                    className="text-xs border border-slate-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-teal-500" />
                            </div>
                        </div>
                    </div>

                    {/* v2 Evidence Mode Toggle */}
                    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${evidenceModeEnabled ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-400'}`}>
                                <Shield size={18} />
                            </div>
                            <div>
                                <p className="text-sm font-black text-slate-900 leading-none mb-1">Evidence Mode (v2)</p>
                                <p className="text-[10px] text-slate-400 font-medium tracking-tight">Governance + Deterministic Safety</p>
                            </div>
                        </div>
                        <button
                            onClick={() => setEvidenceModeEnabled(!evidenceModeEnabled)}
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${evidenceModeEnabled ? 'bg-indigo-600' : 'bg-slate-200'}`}
                        >
                            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${evidenceModeEnabled ? 'translate-x-6' : 'translate-x-1'}`} />
                        </button>
                    </div>

                    {/* Generate button */}
                    <button
                        onClick={handleGenerate}
                        disabled={generating || !rawNote.trim()}
                        className="w-full flex items-center justify-center gap-3 py-4 bg-gradient-to-r from-teal-600 via-cyan-600 to-blue-600 text-white font-black text-sm rounded-2xl shadow-xl shadow-teal-600/20 hover:shadow-2xl hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:translate-y-0"
                    >
                        {generating ? <><Loader2 size={18} className="animate-spin" />Generating Intelligence...</> : <><Zap size={18} />Generate Full Encounter</>}
                    </button>

                    {/* Pipeline progress */}
                    {progress.length > 0 && (
                        <div className="bg-slate-900 rounded-2xl p-5 space-y-1.5">
                            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-3">Pipeline Log</p>
                            {progress.map((msg, i) => (
                                <div key={i} className={`text-xs font-mono flex items-start gap-2 ${msg.startsWith('❌') ? 'text-red-400' : msg.startsWith('✅') ? 'text-emerald-400' : msg.startsWith('⚠️') ? 'text-amber-400' : 'text-slate-300'}`}>
                                    {msg}
                                </div>
                            ))}
                            {generating && <div className="flex gap-1 pt-1"><span className="w-1.5 h-1.5 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} /><span className="w-1.5 h-1.5 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '120ms' }} /><span className="w-1.5 h-1.5 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '240ms' }} /></div>}
                        </div>
                    )}
                </div>

                {/* Right panel — encounter results */}
                {encounter ? (
                    <div className="space-y-5">
                        {/* AI Watermark */}
                        <div className="bg-amber-50 border border-amber-200 rounded-2xl px-5 py-3 flex items-center gap-3">
                            <AlertTriangle size={18} className="text-amber-500 shrink-0" />
                            <p className="text-xs text-amber-700 font-bold">{encounter.ai_watermark}</p>
                        </div>

                        {/* Summary cards */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            {[
                                { label: 'Risk', value: encounter.risk_score, icon: <Activity size={14} />, color: RISK_COLORS[encounter.risk_score] || RISK_COLORS.Low },
                                { label: 'Case', value: encounter.case_status, icon: <FileText size={14} />, color: 'text-slate-600 bg-slate-50 border-slate-200' },
                                { label: 'Admission', value: encounter.admission_required ? 'Required' : 'Not Required', icon: <Stethoscope size={14} />, color: encounter.admission_required ? 'text-red-600 bg-red-50 border-red-200' : 'text-emerald-600 bg-emerald-50 border-emerald-200' },
                                { label: 'ICU', value: encounter.icu_required ? 'Required' : 'Not Required', icon: <AlertCircle size={14} />, color: encounter.icu_required ? 'text-red-700 bg-red-100 border-red-300' : 'text-slate-500 bg-white border-slate-200' },
                            ].map(c => (
                                <div key={c.label} className={`border rounded-xl p-3 ${c.color}`}>
                                    <div className="flex items-center gap-1.5 mb-1">{c.icon}<span className="text-[10px] font-black uppercase tracking-widest">{c.label}</span></div>
                                    <div className="text-sm font-black capitalize">{c.value}</div>
                                </div>
                            ))}
                        </div>

                        {/* Chief complaint */}
                        {encounter.chief_complaint && (
                            <div className="bg-teal-50 border border-teal-100 rounded-2xl px-5 py-4">
                                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-teal-500 mb-1">Chief Complaint</p>
                                <p className="text-slate-900 font-bold text-sm">{encounter.chief_complaint}</p>
                            </div>
                        )}

                        {/* SOAP Note */}
                        {Object.keys(encounter.soap).length > 0 && (
                            <Section title="SOAP Note" icon={<FileText size={16} />}>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-3">
                                    {Object.entries(encounter.soap).map(([k, v]) => (
                                        <div key={k} className="bg-slate-50 rounded-xl p-4">
                                            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">{k}</p>
                                            <p className="text-sm text-slate-700 leading-relaxed">{v}</p>
                                        </div>
                                    ))}
                                </div>
                            </Section>
                        )}

                        {/* Medications */}
                        <Section title="AI Extracted Medications" icon={<Pill size={16} />} badge={encounter.medications.length}>
                            {encounter.medications.length === 0 ? <p className="text-slate-400 italic text-sm mt-3">No medications extracted.</p> : (
                                <div className="space-y-3 mt-3">
                                    {encounter.medications.map(med => (
                                        <div key={med.id} className={`p-4 rounded-xl border ${med.requires_confirmation ? 'border-amber-200 bg-amber-50/50' : 'border-slate-100 bg-white'}`}>
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <div className="font-black text-slate-900">{med.name}</div>
                                                    <div className="text-xs text-slate-500 mt-0.5">{[med.dosage, med.frequency, med.route, med.duration].filter(Boolean).join(' • ')}</div>
                                                    {med.start_date_text && <div className="text-xs text-slate-400 mt-0.5">Start: {med.start_date_text}</div>}
                                                    {med.requires_confirmation && (
                                                        <div className="flex items-center gap-1.5 mt-2 text-amber-600 text-xs font-bold">
                                                            <AlertTriangle size={12} /> Doctor confirmation required: {med.fields_required.join(', ')}
                                                        </div>
                                                    )}
                                                </div>
                                                <span className={`text-[10px] font-black uppercase px-2 py-1 rounded-lg ${med.confidence === 'high' ? 'bg-emerald-100 text-emerald-700' : med.confidence === 'medium' ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'}`}>{med.confidence}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </Section>

                        {/* Diagnoses */}
                        <Section title="ICD-10 Diagnosis Coding" icon={<Stethoscope size={16} />} badge={encounter.diagnoses.length}>
                            {encounter.diagnoses.length === 0 ? <p className="text-slate-400 italic text-sm mt-3">No diagnoses inferred.</p> : (
                                <div className="space-y-3 mt-3">
                                    {encounter.diagnoses.map(d => (
                                        <div key={d.id} className={`p-4 rounded-xl border ${d.is_primary ? 'border-teal-200 bg-teal-50/40' : 'border-slate-100 bg-white'}`}>
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="font-black text-slate-900">{d.condition_name}</span>
                                                        {d.is_primary && <span className="text-[10px] bg-teal-600 text-white px-1.5 py-0.5 rounded font-black">PRIMARY</span>}
                                                    </div>
                                                    {d.icd10_code && <div className="text-xs font-mono text-blue-600 mt-0.5">{d.icd10_code}</div>}
                                                    {d.reasoning && <div className="text-xs text-slate-500 mt-1 italic">{d.reasoning}</div>}
                                                </div>
                                            </div>
                                            <ConfidenceBar score={d.confidence_score} />
                                        </div>
                                    ))}
                                </div>
                            )}
                        </Section>

                        {/* Procedures */}
                        <Section title="AI Extracted Procedures" icon={<Activity size={16} />} badge={encounter.procedures?.length}>
                            {!encounter.procedures || encounter.procedures.length === 0 ? <p className="text-slate-400 italic text-sm mt-3">No procedures extracted.</p> : (
                                <div className="space-y-3 mt-3">
                                    {encounter.procedures.map(proc => (
                                        <div key={proc.id} className="p-4 rounded-xl border border-slate-100 bg-white">
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <div className="font-black text-slate-900">{proc.name}</div>
                                                    {proc.code && <div className="text-xs font-mono text-blue-600 mt-0.5">{proc.code}</div>}
                                                    {proc.notes && <div className="text-xs text-slate-500 mt-1">{proc.notes}</div>}
                                                </div>
                                                <span className={`text-[10px] font-black uppercase px-2 py-1 rounded-lg ${proc.confidence === 'high' ? 'bg-emerald-100 text-emerald-700' : proc.confidence === 'medium' ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'}`}>{proc.confidence}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </Section>

                        {/* Billing */}
                        <Section title="AI Billing Intelligence" icon={<CreditCard size={16} />} badge={encounter.billing.length}>
                            <div className="flex items-center gap-2 mt-3 mb-4">
                                <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Overall complexity:</span>
                                <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${encounter.billing_complexity === 'high' ? 'bg-red-100 text-red-700' : encounter.billing_complexity === 'medium' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'}`}>{encounter.billing_complexity}</span>
                            </div>
                            {encounter.billing.length === 0 ? <p className="text-slate-400 italic text-sm">No billing items inferred.</p> : (
                                <div className="space-y-3">
                                    {encounter.billing.map(b => (
                                        <div key={b.id} className={`p-4 rounded-xl border ${b.requires_review ? 'border-amber-200 bg-amber-50/40' : 'border-slate-100 bg-white'}`}>
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    {b.cpt_code && <span className="text-xs font-mono font-black text-blue-600 mr-2">{b.cpt_code}</span>}
                                                    <span className="font-bold text-slate-900 text-sm">{b.description}</span>
                                                    {b.estimated_cost && <div className="text-xs text-slate-400 mt-0.5">${b.estimated_cost.toFixed(2)} estimated</div>}
                                                    {b.requires_review && <div className="text-xs text-amber-600 font-bold mt-1 flex items-center gap-1"><AlertTriangle size={11} /> Manual review required{b.review_reason ? `: ${b.review_reason}` : ''}</div>}
                                                </div>
                                            </div>
                                            <ConfidenceBar score={b.confidence} />
                                        </div>
                                    ))}
                                </div>
                            )}
                        </Section>

                        {/* Risk & Legal */}
                        {(encounter.risk_flags.length > 0 || encounter.legal_flags.length > 0) && (
                            <Section title="Risk & Medico-Legal Flags" icon={<Shield size={16} />}>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-3">
                                    {encounter.risk_flags.length > 0 && (
                                        <div>
                                            <p className="text-[10px] font-black uppercase tracking-widest text-red-500 mb-2">Risk Flags</p>
                                            <ul className="space-y-1.5">
                                                {encounter.risk_flags.map((f, i) => <li key={i} className="text-xs text-red-700 flex items-start gap-1.5"><AlertTriangle size={11} className="mt-0.5 shrink-0 text-red-400" />{f}</li>)}
                                            </ul>
                                        </div>
                                    )}
                                    {encounter.legal_flags.length > 0 && (
                                        <div>
                                            <p className="text-[10px] font-black uppercase tracking-widest text-purple-500 mb-2">Legal Flags</p>
                                            <ul className="space-y-1.5">
                                                {encounter.legal_flags.map((f, i) => <li key={i} className="text-xs text-purple-700 flex items-start gap-1.5"><Shield size={11} className="mt-0.5 shrink-0 text-purple-400" />{f}</li>)}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            </Section>
                        )}

                        {/* Timeline Events */}
                        {encounter.timeline_events.length > 0 && (
                            <Section title="AI Timeline Events" icon={<Calendar size={16} />} badge={encounter.timeline_events.length}>
                                <div className="space-y-2 mt-3">
                                    {encounter.timeline_events.map(evt => (
                                        <div key={evt.id} className={`pl-4 py-3 pr-4 border-l-4 ${SEVERITY_COLORS[evt.severity] || 'border-l-slate-300'} bg-slate-50 rounded-r-xl`}>
                                            <div className="flex items-center justify-between">
                                                <span className="text-xs font-black text-slate-700">{evt.event_description}</span>
                                                <span className="text-[10px] text-slate-400 ml-2 shrink-0">{evt.event_date_text}</span>
                                            </div>
                                            <span className="text-[10px] uppercase tracking-wide text-slate-400">{evt.event_type.replace('_', ' ')}</span>
                                        </div>
                                    ))}
                                </div>
                            </Section>
                        )}

                        {/* Follow-ups */}
                        {encounter.followups.length > 0 && (
                            <Section title="Follow-Up Recommendations" icon={<Clock size={16} />} badge={encounter.followups.length}>
                                <div className="space-y-3 mt-3">
                                    {encounter.followups.map(fu => (
                                        <div key={fu.id} className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl border border-slate-100">
                                            <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-lg shrink-0 mt-0.5 ${URGENCY_COLORS[fu.urgency] || 'bg-slate-100 text-slate-600'}`}>{fu.urgency}</span>
                                            <div>
                                                <p className="text-sm font-bold text-slate-900">{fu.recommendation}</p>
                                                <p className="text-xs text-slate-400 mt-0.5">{fu.follow_up_type} {fu.suggested_days ? `• In ${fu.suggested_days} days` : ''}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </Section>
                        )}

                        {/* --- Clinical Sense v2: Expansion Tabs --- */}
                        {qualityReport && (
                            <div className="space-y-5 pt-4 border-t-2 border-slate-100">
                                <div className="flex items-center gap-2 px-2">
                                    <Zap size={16} className="text-indigo-600" />
                                    <h3 className="text-xs font-black text-indigo-900 uppercase tracking-widest">Clinical expansion (v2)</h3>
                                </div>

                                {/* 1. Safety Section */}
                                <Section title="🛡 Safety & Drug Interactions" icon={<Shield size={16} />}>
                                    <div className="space-y-4 mt-2">
                                        {/* Critical/Moderate Interactions */}
                                        {qualityReport.drug_safety_flags?.critical_interactions?.length > 0 && (
                                            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                                                <p className="text-[10px] font-black text-red-600 uppercase tracking-widest mb-3">CRITICAL INTERACTIONS</p>
                                                <div className="space-y-3">
                                                    {qualityReport.drug_safety_flags.critical_interactions.map((ci: any, i: number) => (
                                                        <div key={i} className="flex items-start gap-2">
                                                            <AlertCircle size={14} className="text-red-500 mt-0.5 shrink-0" />
                                                            <div>
                                                                <p className="text-xs font-black text-slate-900">{ci.drugs.join(' + ').toUpperCase()}</p>
                                                                <p className="text-xs text-red-700 mt-0.5 leading-relaxed">{ci.message}</p>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                        {/* Contraindications */}
                                        {qualityReport.drug_safety_flags?.contraindications?.length > 0 && (
                                            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                                                <p className="text-[10px] font-black text-amber-600 uppercase tracking-widest mb-3">CONTRAINDICATIONS</p>
                                                <div className="space-y-3">
                                                    {qualityReport.drug_safety_flags.contraindications.map((c: any, i: number) => (
                                                        <div key={i} className="flex items-start gap-2">
                                                            <Shield size={14} className="text-amber-500 mt-0.5 shrink-0" />
                                                            <div>
                                                                <p className="text-xs font-black text-slate-900">{c.drug.toUpperCase()}</p>
                                                                <p className="text-xs text-amber-800 mt-0.5 leading-relaxed">{c.reason}</p>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                        {/* Clinical Rules Flags */}
                                        {qualityReport.clinical_safety_flags?.critical_flags?.length > 0 && (
                                            <div className="bg-slate-900 rounded-xl p-4">
                                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">SAFETY RULE VIOLATIONS</p>
                                                <div className="space-y-2">
                                                    {qualityReport.clinical_safety_flags.critical_flags.map((f: string, i: number) => (
                                                        <div key={i} className="text-xs text-red-400 flex items-start gap-2">
                                                            <Lock size={12} className="mt-0.5 shrink-0" />
                                                            {f}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                        {(!qualityReport.drug_safety_flags?.critical_interactions?.length && !qualityReport.drug_safety_flags?.contraindications?.length && !qualityReport.clinical_safety_flags?.critical_flags?.length) && (
                                            <div className="text-center py-6 text-slate-400 italic text-xs">No critical safety flags detected.</div>
                                        )}
                                    </div>
                                </Section>

                                {/* 2. Risk Metrics */}
                                <Section title="📊 Structured Risk Scores" icon={<Activity size={16} />}>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
                                        <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">BMI</p>
                                            <p className="text-lg font-black text-slate-900">{qualityReport.structured_risk_metrics?.bmi || 'N/A'}</p>
                                        </div>
                                        <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">POLYPHARMACY RISK</p>
                                            <p className={`text-sm font-black ${qualityReport.structured_risk_metrics?.polypharmacy_risk ? 'text-red-600' : 'text-emerald-600'}`}>
                                                {qualityReport.structured_risk_metrics?.polypharmacy_risk ? 'HIGH RISK' : 'LOW RISK'}
                                            </p>
                                        </div>
                                        <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">READMISSION RISK</p>
                                            <div className="w-full bg-slate-200 h-1.5 rounded-full mt-2 overflow-hidden">
                                                <div className={`h-full rounded-full ${qualityReport.structured_risk_metrics?.readmission_risk_score > 60 ? 'bg-red-500' : 'bg-teal-500'}`} style={{ width: `${qualityReport.structured_risk_metrics?.readmission_risk_score || 0}%` }} />
                                            </div>
                                            <p className="text-[10px] font-bold text-slate-400 mt-1">{qualityReport.structured_risk_metrics?.readmission_risk_score || 0}% Probability</p>
                                        </div>
                                        <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">FALL RISK</p>
                                            <div className="w-full bg-slate-200 h-1.5 rounded-full mt-2 overflow-hidden">
                                                <div className={`h-full rounded-full ${qualityReport.structured_risk_metrics?.fall_risk_score > 50 ? 'bg-amber-500' : 'bg-teal-500'}`} style={{ width: `${qualityReport.structured_risk_metrics?.fall_risk_score || 0}%` }} />
                                            </div>
                                            <p className="text-[10px] font-bold text-slate-400 mt-1">{qualityReport.structured_risk_metrics?.fall_risk_score || 0}/100 Score</p>
                                        </div>
                                    </div>
                                </Section>

                                {/* 3. Evidence & Rationales */}
                                <Section title="📚 Evidence & Rationales" icon={<BookOpen size={16} />}>
                                    <div className="space-y-4 mt-2">
                                        {qualityReport.rationale_json?.diagnosis_rationale?.map((dr: any, i: number) => (
                                            <div key={i} className="bg-indigo-50 border border-indigo-100 rounded-xl p-4">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="text-[10px] bg-indigo-600 text-white px-1.5 py-0.5 rounded font-black">DIAGNOSIS</span>
                                                    <span className="text-xs font-black text-slate-900">{dr.condition}</span>
                                                </div>
                                                <p className="text-xs text-slate-700 leading-relaxed italic border-l-2 border-indigo-300 pl-3 mb-2">{dr.evidence}</p>
                                                <div className="flex items-start gap-2 bg-white/60 p-2 rounded-lg text-[10px] text-indigo-600 font-medium">
                                                    <Link2 size={12} className="shrink-0 mt-0.5" />
                                                    <span>Snippet: "{dr.source_snippet}"</span>
                                                </div>
                                            </div>
                                        ))}
                                        {qualityReport.guideline_flags?.guideline_gaps?.length > 0 && (
                                            <div className="bg-slate-50 rounded-xl p-4">
                                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">GUIDELINE COMPLIANCE GAPS</p>
                                                <div className="space-y-2">
                                                    {qualityReport.guideline_flags.guideline_gaps.map((gap: string, i: number) => (
                                                        <div key={i} className="text-xs text-slate-600 flex items-start gap-2">
                                                            <ExternalLink size={12} className="text-slate-400 mt-0.5 shrink-0" />
                                                            {gap}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </Section>

                                {/* 4. Lab Interpretations */}
                                <Section title="🔬 Lab Interpretation" icon={<Microscope size={16} />}>
                                    <div className="space-y-3 mt-2">
                                        {qualityReport.lab_interpretation?.abnormal_labs?.map((lab: any, i: number) => (
                                            <div key={i} className="flex items-center justify-between p-3 bg-white border border-slate-100 rounded-xl shadow-sm">
                                                <div>
                                                    <p className="text-xs font-black text-slate-900">{lab.lab}</p>
                                                    <p className="text-[10px] text-slate-400">{lab.threshold} {lab.unit} (Normal range upper)</p>
                                                </div>
                                                <div className="text-right">
                                                    <span className={`text-xs font-black ${lab.status === 'High' ? 'text-red-600' : 'text-blue-600'}`}>{lab.value}{lab.unit}</span>
                                                    <p className={`text-[10px] font-black ${lab.status === 'High' ? 'text-red-400' : 'text-blue-400'}`}>{lab.status.toUpperCase()}</p>
                                                </div>
                                            </div>
                                        ))}
                                        {qualityReport.lab_interpretation?.interpretations?.map((txt: string, i: number) => (
                                            <p key={i} className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-lg border-l-2 border-slate-300">{txt}</p>
                                        ))}
                                        {(!qualityReport.lab_interpretation?.abnormal_labs?.length) && (
                                            <div className="text-center py-6 text-slate-400 italic text-xs">No active abnormal labs detected in note.</div>
                                        )}
                                    </div>
                                </Section>

                                {/* 5. Handoff (SBAR) */}
                                <Section title="🔁 SBAR Handoff" icon={<Repeat size={16} />}>
                                    <div className="space-y-4 mt-2">
                                        {['situation', 'background', 'assessment', 'recommendation'].map(key => (
                                            <div key={key} className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{key}</p>
                                                <p className="text-xs text-slate-700 leading-relaxed font-mono">{qualityReport.handoff_sbar?.[key] || '...'}</p>
                                            </div>
                                        ))}
                                    </div>
                                </Section>

                                {/* 6. Differentials */}
                                <Section title="🧠 Differential Diagnosis" icon={<BrainCircuit size={16} />}>
                                    <div className="space-y-3 mt-2">
                                        <div className="bg-blue-50 border border-blue-100 rounded-xl p-3 flex items-start gap-2 mb-2">
                                            <AlertCircle size={14} className="text-blue-500 mt-0.5 shrink-0" />
                                            <p className="text-[10px] text-blue-700 font-bold leading-tight">ASSISTIVE ONLY — Consider these alternatives based on symptoms mentioned in the note.</p>
                                        </div>
                                        {qualityReport.differential_output?.possible_differentials?.map((diff: any, i: number) => (
                                            <div key={i} className="p-4 bg-white border border-slate-100 rounded-xl shadow-sm">
                                                <div className="flex items-start justify-between mb-1">
                                                    <p className="text-sm font-black text-slate-900">{diff.condition}</p>
                                                    <span className="text-[10px] font-black text-slate-400">{Math.round(diff.confidence * 100)}% Match</span>
                                                </div>
                                                <p className="text-xs text-slate-500 leading-relaxed">{diff.reason}</p>
                                            </div>
                                        ))}
                                    </div>
                                </Section>
                            </div>
                        )}

                        {/* Confirm CTA at bottom */}
                        {!encounter.is_confirmed && (
                            <div className="bg-gradient-to-r from-teal-600 to-cyan-700 rounded-2xl p-6 text-white">
                                <h3 className="font-black text-lg mb-1">Ready to finalise?</h3>
                                <p className="text-teal-100 text-sm mb-4">Confirming will promote all AI outputs into the permanent clinical record. This includes saving the structured SOAP note, activating medications, recording procedures, and updating medical history.</p>
                                <button onClick={handleConfirm} disabled={confirming} className="flex items-center gap-2 px-6 py-3 bg-white text-teal-700 font-black rounded-xl hover:bg-teal-50 transition-colors disabled:opacity-60">
                                    {confirming ? <Loader2 size={16} className="animate-spin" /> : <CheckSquare size={16} />}
                                    Confirm & Save to Clinical Records
                                </button>
                            </div>
                        )}
                    </div>
                ) : (
                    !generating && (
                        <div className="flex flex-col items-center justify-center h-full py-32 text-center">
                            <div className="w-24 h-24 bg-gradient-to-br from-teal-100 to-cyan-100 rounded-3xl flex items-center justify-center mb-6">
                                <Brain size={40} className="text-teal-500" />
                            </div>
                            <h2 className="text-2xl font-black text-slate-900 mb-3">Clinical Intelligence Engine</h2>
                            <p className="text-slate-400 text-sm max-w-sm leading-relaxed">
                                Paste a raw clinical note on the left. The AI will run 6 parallel pipelines and return a fully structured encounter in under 4 seconds.
                            </p>
                            <div className="grid grid-cols-3 gap-3 mt-8 text-left max-w-md">
                                {['SOAP Structuring', 'Medication Extraction', 'ICD-10 Coding', 'Billing Intelligence', 'Risk Analysis', 'Medico-Legal Audit'].map(f => (
                                    <div key={f} className="bg-white border border-slate-100 rounded-xl p-3 text-xs font-bold text-slate-600 shadow-sm">{f}</div>
                                ))}
                            </div>
                        </div>
                    )
                )}
            </main>
        </div>
    );
}

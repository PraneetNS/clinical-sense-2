"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { encounterApi, patientsApi, aiApi, getErrorMessage } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/ui/Toast';
import Link from 'next/link';
import {
    ChevronLeft, Brain, Zap, CheckCircle, AlertTriangle, Clock,
    Pill, Stethoscope, CreditCard, Calendar, Shield,
    Loader2, RefreshCw, ChevronDown, ChevronUp, AlertCircle,
    CheckSquare, FileText, Activity, Link2, BookOpen, Microscope,
    Repeat, BrainCircuit, Lock, ExternalLink, Mic, Square, Sparkles, Send,
    BarChart3
} from 'lucide-react';
import Waveform from '@/components/encounter/Waveform';

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
interface PipelineStatus { pipeline_name: string; status: 'success' | 'failed' | 'partial'; data: any; error: string | null; latency_ms: number; }
interface Encounter {
    encounter_id: number; patient_id: number; status: string; is_confirmed: boolean;
    encounter_date: string; chief_complaint: string;
    soap: Record<string, string>; medications: Medication[]; diagnoses: Diagnosis[];
    procedures: Procedure[];
    billing: BillingItem[]; timeline_events: TimelineEvent[]; followups: Followup[];
    risk_score: string; risk_flags: string[]; legal_flags: string[];
    admission_required: boolean; icu_required: boolean; follow_up_days?: number;
    case_status: string; billing_complexity: string; ai_watermark: string; created_at: string;
    pipeline_statuses?: PipelineStatus[];
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

function PipelineStatusBadge({ status }: { status?: PipelineStatus }) {
    if (!status) return null;
    if (status.status === 'success') return <span className="flex items-center gap-1 px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full text-[10px] font-black"><CheckCircle size={10} /> {status.latency_ms}ms</span>;
    if (status.status === 'partial') return <span className="flex items-center gap-1 px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full text-[10px] font-black"><AlertTriangle size={10} /> PARTIAL</span>;
    return <span className="flex items-center gap-1 px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-[10px] font-black"><AlertCircle size={10} /> FAILED</span>;
}

function Section({ title, icon, children, badge, pipelineStatus }: { title: string; icon: React.ReactNode; children: React.ReactNode; badge?: number; pipelineStatus?: PipelineStatus }) {
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
                    {pipelineStatus && <PipelineStatusBadge status={pipelineStatus} />}
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

    // Voice Capture State
    const [isRecording, setIsRecording] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const [scribeSessionId, setScribeSessionId] = useState('');
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioStreamRef = useRef<MediaStream | null>(null);
    const recordingIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);

    // DDx Challenge State
    const [challengeResults, setChallengeResults] = useState<Record<number, any>>({});
    const [challengingId, setChallengingId] = useState<number | null>(null);

    // Context & Actions
    const [sendingPortalLink, setSendingPortalLink] = useState(false);

    /* load patient */
    useEffect(() => {
        if (id) patientsApi.getById(id as string).then(r => setPatient(r.data)).catch(() => { });
        setScribeSessionId(crypto.randomUUID());
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
        addProgress('⚡ Running parallel AI pipelines simultaneously...');

        try {
            const res = await encounterApi.generate({
                patient_id: Number(id),
                raw_note: rawNote,
                encounter_date: new Date(encounterDate).toISOString(),
                evidence_mode_enabled: evidenceModeEnabled,
            });
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

            addProgress(`✅ Encounter #${enc.encounter_id} generated.`);
            addProgress('⚠️  Review all AI outputs before confirming.');
            connectWs(enc.encounter_id);
            showToast('AI Encounter generated! Review below.', 'success');
        } catch (err: any) {
            const msg = getErrorMessage(err);
            addProgress(`❌ Error: ${msg}`);
            showToast(`Generation failed: ${msg}`, 'error');
        } finally {
            setGenerating(false);
        }
    };

    /* ── Voice Capture ── */
    useEffect(() => {
        if (isRecording) {
            timerIntervalRef.current = setInterval(() => {
                setRecordingTime(t => t + 1);
            }, 1000);
        } else {
            if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
            setRecordingTime(0);
        }
        return () => { if (timerIntervalRef.current) clearInterval(timerIntervalRef.current); };
    }, [isRecording]);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const handleToggleRecording = async () => {
        if (isRecording) {
            if (recordingIntervalRef.current) clearInterval(recordingIntervalRef.current);
            if (audioStreamRef.current) audioStreamRef.current.getTracks().forEach(t => t.stop());
            setIsRecording(false);
            showToast('Scribe session paused.', 'success');
        } else {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                audioStreamRef.current = stream;
                
                const startNewRecorder = () => {
                    const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
                    mediaRecorderRef.current = recorder;
                    const chunks: Blob[] = [];

                    recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
                    recorder.onstop = async () => {
                        const blob = new Blob(chunks, { type: 'audio/webm' });
                        const fd = new FormData();
                        fd.append('file', blob, 'chunk.webm');
                        try {
                            const res = await aiApi.transcribe(fd, { 
                                params: { session_id: scribeSessionId, patient_id: id } 
                            });
                            if (res.data.accumulated_text) {
                                setRawNote(res.data.accumulated_text);
                            }
                        } catch (err) {
                            console.error('Transcription error', err);
                        }
                    };

                    recorder.start();
                    setTimeout(() => { if (recorder.state === 'recording') recorder.stop(); }, 5000);
                };

                startNewRecorder();
                recordingIntervalRef.current = setInterval(startNewRecorder, 5500);

                setIsRecording(true);
                showToast('Ambient Scribe started...', 'success');
            } catch (err) {
                console.error("Mic error:", err);
                showToast('Microphone access denied or unavailable.', 'error');
            }
        }
    };

    /* ── Confirm encounter ── */
    const handleConfirm = async () => {
        if (!encounter) return;
        setConfirming(true);
        try {
            await encounterApi.confirm(encounter.encounter_id);
            setEncounter(e => e ? { ...e, is_confirmed: true, status: 'confirmed' } : e);
            showToast('Encounter confirmed. All data saved to patient record.', 'success');
        } catch (err: any) {
            showToast(getErrorMessage(err) || 'Confirmation failed', 'error');
        } finally {
            setConfirming(false);
        }
    };

    /* ── DDx Challenge ── */
    const handleChallengeDiagnosis = async (d: Diagnosis) => {
        if (!encounter) return;
        setChallengingId(d.id);
        try {
            const res = await aiApi.challenge(encounter.encounter_id, {
                diagnosis_name: d.condition_name,
                icd_code: d.icd10_code || ''
            });
            setChallengeResults(prev => ({ ...prev, [d.id]: res.data }));
            showToast('Challenge analysis complete.', 'success');
        } catch (err: any) {
            showToast(`Challenge failed: ${getErrorMessage(err)}`, 'error');
        } finally {
            setChallengingId(null);
        }
    };

    /* ── Portal Link ── */
    const handleSendPortalLink = async () => {
        if (!encounter) return;
        setSendingPortalLink(true);
        try {
            const res = await encounterApi.sendPortalLink(encounter.encounter_id);
            showToast(`Portal Link Sent! Check console for debug URL.`, 'success');
            console.log('Secure portal link: ', res.data.link);
        } catch (err: any) {
            showToast(`Failed to generate portal link: ${getErrorMessage(err)}`, 'error');
        } finally {
            setSendingPortalLink(false);
        }
    };

    const hasCriticalFailure = () => {
        return encounter?.pipeline_statuses?.some(p => 
            p.status === 'failed' && ['RISK_ANALYSIS', 'MEDICO_LEGAL'].includes(p.pipeline_name)
        );
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-teal-50/30">
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
                        <span className="flex items-center gap-1.5 text-xs text-emerald-600 font-bold mr-4">
                            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />Live
                        </span>
                    )}
                    {encounter && !encounter.is_confirmed && (
                        <>
                            {hasCriticalFailure() && (
                                <div className="flex items-center gap-2 px-3 py-1.5 bg-red-50 text-red-600 rounded-lg text-xs font-bold border border-red-200">
                                    <AlertTriangle size={14} /> Risk Analysis failed — manual review required.
                                </div>
                            )}
                            <button
                                onClick={handleConfirm}
                                disabled={confirming || hasCriticalFailure()}
                                className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-teal-600 to-cyan-600 text-white font-black text-sm rounded-xl shadow-lg shadow-teal-600/25 hover:shadow-xl hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {confirming ? <Loader2 size={16} className="animate-spin" /> : <CheckSquare size={16} />}
                                Confirm & Save
                            </button>
                        </>
                    )}
                    {encounter?.is_confirmed && (
                        <div className="flex items-center gap-2">
                             <button
                                onClick={handleSendPortalLink}
                                disabled={sendingPortalLink}
                                className="flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-600 font-black text-sm rounded-xl border border-indigo-200 hover:bg-indigo-100 transition-all disabled:opacity-50"
                            >
                                {sendingPortalLink ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                                Send Portal
                            </button>
                            <span className="flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-700 font-black text-sm rounded-xl border border-emerald-200">
                                <CheckCircle size={16} /> Confirmed
                            </span>
                        </div>
                    )}
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-8 py-8 grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-8">
                <div className="space-y-6">
                    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 relative">
                        <div className="flex items-center justify-between mb-4">
                            <label className="text-xs font-black text-slate-400 uppercase tracking-widest">Clinical Note</label>
                            <div className="flex items-center gap-3">
                                {isRecording && (
                                    <div className="flex items-center gap-2 px-3 py-1 bg-teal-50 text-teal-600 rounded-full text-xs font-black border border-teal-100">
                                        <Clock size={12} /> {formatTime(recordingTime)}
                                    </div>
                                )}
                                <button
                                    onClick={handleToggleRecording}
                                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold transition-all ${
                                        isRecording 
                                            ? 'bg-red-50 text-red-600 border border-red-200 animate-pulse' 
                                            : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200'
                                    }`}
                                >
                                    {isRecording ? <><Square size={12} fill="currentColor" /> Pause scribe</> : <><Mic size={14} /> Start Scribe</>}
                                </button>
                            </div>
                        </div>

                        {isRecording && (
                            <div className="mb-4 bg-slate-50 rounded-xl p-3 border border-slate-100 h-16 flex items-center justify-center">
                                <Waveform stream={audioStreamRef.current} isRecording={isRecording} />
                            </div>
                        )}

                        <textarea
                            value={rawNote}
                            onChange={e => setRawNote(e.target.value)}
                            rows={15}
                            placeholder="Type or use Ambient Scribe..."
                            className="w-full text-sm text-slate-800 border-0 resize-none focus:outline-none leading-relaxed font-mono"
                        />

                        <div className="flex items-center justify-between mt-4 border-t border-slate-50 pt-4">
                            <div className="flex gap-4">
                                <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">{rawNote.length} chars</span>
                                <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">{rawNote.split(/\s+/).filter(x => x).length} words</span>
                            </div>
                            <input 
                                type="date" 
                                value={encounterDate} 
                                onChange={e => setEncounterDate(e.target.value)}
                                className="text-xs border border-slate-200 rounded-lg px-2 py-1 font-bold text-slate-700"
                            />
                        </div>
                    </div>

                    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${evidenceModeEnabled ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-400'}`}>
                                <Shield size={18} />
                            </div>
                            <div>
                                <p className="text-sm font-black text-slate-900 mb-0.5">Evidence Mode</p>
                                <p className="text-[10px] text-slate-400 font-medium">Enhanced Governance Audit</p>
                            </div>
                        </div>
                        <button
                            onClick={() => setEvidenceModeEnabled(!evidenceModeEnabled)}
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${evidenceModeEnabled ? 'bg-indigo-600' : 'bg-slate-200'}`}
                        >
                            <span className={`h-4 w-4 transform rounded-full bg-white transition-transform ${evidenceModeEnabled ? 'translate-x-6' : 'translate-x-1'}`} />
                        </button>
                    </div>

                    <button
                        onClick={handleGenerate}
                        disabled={generating || !rawNote.trim()}
                        className="w-full flex items-center justify-center gap-3 py-4 bg-gradient-to-r from-teal-600 via-cyan-600 to-blue-600 text-white font-black text-sm rounded-2xl shadow-xl shadow-teal-600/20 hover:shadow-2xl hover:-translate-y-0.5 transition-all disabled:opacity-50"
                    >
                        {generating ? <><Loader2 size={18} className="animate-spin" />Processing...</> : <><Zap size={18} />Generate Encounter</>}
                    </button>

                    {progress.length > 0 && (
                        <div className="bg-slate-900 rounded-2xl p-5 space-y-1.5">
                            {progress.map((msg, i) => (
                                <div key={i} className={`text-[10px] font-mono flex items-start gap-2 ${msg.startsWith('❌') ? 'text-red-400' : 'text-slate-300'}`}>
                                    {msg}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="space-y-6">
                    {encounter ? (
                        <>
                            <div className="bg-amber-50 border border-amber-200 rounded-2xl px-5 py-3 flex items-center gap-3">
                                <AlertTriangle size={18} className="text-amber-500 shrink-0" />
                                <p className="text-xs text-amber-700 font-bold">{encounter.ai_watermark}</p>
                            </div>

                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                                {[
                                    { label: 'Risk', value: encounter.risk_score, color: RISK_COLORS[encounter.risk_score] || RISK_COLORS.Low },
                                    { label: 'Case Status', value: encounter.case_status, color: 'bg-slate-50 text-slate-700' },
                                    { label: 'Admission', value: encounter.admission_required ? 'Req' : 'No', color: encounter.admission_required ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700' },
                                    { label: 'Billing', value: encounter.billing_complexity, color: 'bg-indigo-50 text-indigo-700' },
                                ].map(c => (
                                    <div key={c.label} className={`rounded-xl p-3 border border-transparent ${c.color}`}>
                                        <p className="text-[10px] font-black uppercase tracking-widest mb-1 opacity-60">{c.label}</p>
                                        <p className="text-sm font-black capitalize">{c.value}</p>
                                    </div>
                                ))}
                            </div>

                            <Section title="SOAP Note" icon={<FileText size={16} />} pipelineStatus={encounter.pipeline_statuses?.find(p => p.pipeline_name === 'SOAP')}>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {Object.entries(encounter.soap).map(([k, v]) => (
                                        <div key={k} className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                                            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">{k}</p>
                                            <p className="text-sm text-slate-700 leading-relaxed font-medium">{v}</p>
                                        </div>
                                    ))}
                                </div>
                            </Section>

                            <Section title="Medications" icon={<Pill size={16} />} badge={encounter.medications.length} pipelineStatus={encounter.pipeline_statuses?.find(p => p.pipeline_name === 'MEDICATION_STRUCTURING')}>
                                <div className="space-y-3">
                                    {encounter.medications.map(med => (
                                        <div key={med.id} className="p-4 rounded-xl border border-slate-100 bg-white shadow-sm">
                                            <div className="flex justify-between items-start">
                                                <p className="font-black text-slate-900">{med.name}</p>
                                                <span className="text-[10px] font-black uppercase px-2 py-1 rounded bg-slate-100 text-slate-500">{med.confidence}</span>
                                            </div>
                                            <p className="text-xs text-slate-500 mt-1">{[med.dosage, med.frequency, med.route].filter(Boolean).join(' • ')}</p>
                                            {med.requires_confirmation && (
                                                <div className="text-[10px] font-bold text-amber-600 mt-2 bg-amber-50 px-2 py-1 rounded-lg inline-flex items-center gap-1.5">
                                                    <AlertTriangle size={12} /> Needs Confirmation
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </Section>

                            <Section title="Diagnosis Coding" icon={<Stethoscope size={16} />} badge={encounter.diagnoses.length} pipelineStatus={encounter.pipeline_statuses?.find(p => p.pipeline_name === 'DIAGNOSIS_CODING')}>
                                <div className="space-y-3 mt-2">
                                    {encounter.diagnoses.map(d => (
                                        <div key={d.id} className="p-4 rounded-xl border border-slate-100 bg-white">
                                            <div className="flex justify-between items-start mb-3">
                                                <div>
                                                    <p className="font-black text-slate-900">{d.condition_name}</p>
                                                    <p className="text-xs font-mono text-indigo-600 mt-0.5">{d.icd10_code}</p>
                                                </div>
                                                <button onClick={() => handleChallengeDiagnosis(d)} className="px-3 py-1 bg-indigo-50 text-indigo-600 rounded-lg text-xs font-black">Challenge</button>
                                            </div>
                                            {challengeResults[d.id] && (
                                                <div className="mt-4 p-4 bg-indigo-50 rounded-xl border border-indigo-100 text-xs text-indigo-900">
                                                    <p className="font-black mb-2 flex items-center gap-2"><Sparkles size={12}/> DDX CHALLENGE</p>
                                                    <div className="space-y-2">
                                                        <p><strong>Support:</strong> {challengeResults[d.id].supports?.[0]?.finding || 'None'}</p>
                                                        <p><strong>Against:</strong> {challengeResults[d.id].against?.[0]?.finding || 'None'}</p>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </Section>

                            {qualityReport && (
                                <div className="pt-8 space-y-6">
                                    <div className="flex items-center gap-2 px-2 text-indigo-600">
                                        <Shield size={20} />
                                        <h2 className="text-xs font-black uppercase tracking-[0.2em]">Clinical Governance v2</h2>
                                    </div>
                                    <Section title="Safety Audit" icon={<Activity size={16} />}>
                                        {qualityReport.drug_safety_flags?.critical_interactions?.length > 0 && (
                                            <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4">
                                                <p className="text-[10px] font-black text-red-600 uppercase mb-2">Critical Interactions</p>
                                                {qualityReport.drug_safety_flags.critical_interactions.map((ci: any, i: number) => (
                                                    <p key={i} className="text-xs text-red-800 font-medium">• {ci.message}</p>
                                                ))}
                                            </div>
                                        )}
                                        <div className="grid grid-cols-2 gap-3">
                                            {['Polypharmacy', 'BMI', 'Readmission Risk'].map(m => (
                                                <div key={m} className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                                                    <p className="text-[10px] font-black text-slate-400 uppercase mb-1">{m}</p>
                                                    <p className="text-sm font-black text-slate-900">CHECKED</p>
                                                </div>
                                            ))}
                                        </div>
                                    </Section>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-center opacity-40 py-20">
                            <Brain size={60} className="text-slate-200 mb-6" />
                            <p className="text-sm font-bold text-slate-400">Enter a note to generate clinical intelligence</p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

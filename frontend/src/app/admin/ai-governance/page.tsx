"use client";

import React, { useState, useEffect } from 'react';
import { adminApi, getErrorMessage } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/ui/Toast';
import {
    Brain, Shield, BarChart3, AlertTriangle,
    TrendingUp, Clock, Zap, Target, Loader2,
    Users, Activity, Globe, Info
} from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function AdminGovernancePage() {
    const { user, loading: authLoading } = useAuth();
    const { showToast } = useToast();
    const router = useRouter();

    const [analytics, setAnalytics] = useState<any>(null);
    const [biasReport, setBiasReport] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!authLoading && (!user || user.role !== 'SUPER_ADMIN')) {
            showToast('Access denied. Super Admin role required.', 'error');
            router.push('/');
            return;
        }

        const fetchData = async () => {
            try {
                const [anaRes, biasRes] = await Promise.all([
                    adminApi.getAnalytics(),
                    adminApi.getBiasReport()
                ]);
                setAnalytics(anaRes.data);
                setBiasReport(biasRes.data);
            } catch (err) {
                showToast(getErrorMessage(err), 'error');
            } finally {
                setLoading(false);
            }
        };

        if (user?.role === 'SUPER_ADMIN') {
            fetchData();
        }
    }, [user, authLoading]);

    if (loading || authLoading) {
        return (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center">
                <Loader2 className="animate-spin text-teal-600" size={40} />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <header className="max-w-7xl mx-auto mb-10 flex items-center justify-between">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-indigo-600 rounded-lg text-white">
                            <Shield size={20} />
                        </div>
                        <h1 className="text-3xl font-black text-slate-900 tracking-tight">AI Governance & Analytics</h1>
                    </div>
                    <p className="text-slate-500 font-medium">Monitoring model performance, drift, and clinical safety distribution.</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="bg-emerald-100 text-emerald-700 px-3 py-1.5 rounded-full text-xs font-black flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> Live Monitoring Active
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto space-y-10">
                {/* 1. Core KPIs */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {[
                        { label: 'Avg Latency', value: `${analytics?.metrics?.avg_latency_ms || 0}ms`, icon: <Clock />, color: 'text-indigo-600 bg-indigo-50 border-indigo-100' },
                        { label: 'Acceptance Rate', value: `${Math.round((analytics?.metrics?.acceptance_rate || 0) * 100)}%`, icon: <CheckCircle className="text-emerald-500" />, color: 'text-emerald-700 bg-emerald-50 border-emerald-100' },
                        { label: 'Avg Confidence', value: `${Math.round((analytics?.metrics?.avg_confidence_score || 0) * 100)}%`, icon: <Target />, color: 'text-blue-600 bg-blue-50 border-blue-100' },
                        { label: 'Compliance Score', value: `${Math.round((analytics?.metrics?.avg_compliance_score || 0) * 100)}%`, icon: <BarChart3 />, color: 'text-purple-600 bg-purple-50 border-purple-100' },
                    ].map((kpi, i) => (
                        <div key={i} className={`p-6 rounded-3xl border ${kpi.color} shadow-sm`}>
                            <div className="flex items-center justify-between mb-4">
                                <span className="p-2 bg-white rounded-xl shadow-sm">{kpi.icon}</span>
                                <TrendingUp size={16} className="text-slate-400 opacity-50" />
                            </div>
                            <p className="text-xs font-black uppercase tracking-widest opacity-60 mb-1">{kpi.label}</p>
                            <p className="text-2xl font-black">{kpi.value}</p>
                        </div>
                    ))}
                </div>

                {/* 2. Bias Monitoring & Drift */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Model Performance Distribution */}
                    <div className="bg-white rounded-3xl border border-slate-100 shadow-sm p-8">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-black text-slate-900 flex items-center gap-2">
                                <Activity className="text-orange-500" size={18} /> Model Performance Drift
                            </h3>
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">By Version</span>
                        </div>
                        <div className="space-y-6">
                            {biasReport?.model_performance?.map((m: any, i: number) => (
                                <div key={i} className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs font-black text-slate-700">{m.model}</span>
                                        <span className="text-xs font-bold text-slate-500">{m.total_count} encounters</span>
                                    </div>
                                    <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full rounded-full ${m.avg_confidence > 0.8 ? 'bg-emerald-500' : 'bg-orange-500'}`}
                                            style={{ width: `${m.avg_confidence * 100}%` }}
                                        />
                                    </div>
                                    <div className="flex items-center justify-between text-[10px]">
                                        <span className="text-slate-400 font-medium">Confidence Score</span>
                                        <span className="font-black text-slate-900">{Math.round(m.avg_confidence * 100)}%</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Risk Level Bias */}
                    <div className="bg-white rounded-3xl border border-slate-100 shadow-sm p-8">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-black text-slate-900 flex items-center gap-2">
                                <AlertTriangle className="text-red-500" size={18} /> Risk Confidence Bias
                            </h3>
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">By Triage Level</span>
                        </div>
                        <div className="space-y-6">
                            {biasReport?.risk_distribution?.map((r: any, i: number) => (
                                <div key={i} className="flex items-center gap-4">
                                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-black text-sm border ${r.risk_level === 'HIGH' ? 'bg-red-50 text-red-600 border-red-100' :
                                            r.risk_level === 'MEDIUM' ? 'bg-orange-50 text-orange-600 border-orange-100' : 'bg-teal-50 text-teal-600 border-teal-100'
                                        }`}>
                                        {r.risk_level[0]}
                                    </div>
                                    <div className="flex-1 space-y-1.5">
                                        <div className="flex items-center justify-between font-black text-xs text-slate-900">
                                            <span>{r.risk_level} TRIAGE</span>
                                            <span>{Math.round(r.avg_confidence * 100)}% Conf</span>
                                        </div>
                                        <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full rounded-full ${r.risk_level === 'HIGH' ? 'bg-red-500' : 'bg-teal-500'}`}
                                                style={{ width: `${r.avg_confidence * 100}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="mt-8 bg-slate-50 rounded-2xl p-4 flex items-start gap-3">
                            <Info size={16} className="text-slate-400 shrink-0 mt-0.5" />
                            <p className="text-[11px] text-slate-500 leading-relaxed">
                                Significant variation in confidence between LOW and HIGH risk encounters may indicate training bias or model hallucination in complex clinical scenarios.
                            </p>
                        </div>
                    </div>
                </div>

                {/* 3. Operational Safety Flags */}
                <div className="bg-slate-900 rounded-[2.5rem] p-10 text-white shadow-2xl">
                    <div className="flex items-center gap-4 mb-8">
                        <div className="p-3 bg-indigo-500 rounded-2xl">
                            <Shield size={24} />
                        </div>
                        <div>
                            <h2 className="text-2xl font-black tracking-tight">Governance Enforcement</h2>
                            <p className="text-indigo-300 text-sm font-medium">Automatic clinical rule enforcement for all clinical outputs.</p>
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div className="bg-white/5 rounded-3xl p-6 border border-white/10">
                            <h4 className="text-xs font-black uppercase tracking-widest text-indigo-400 mb-4">DRUG SAFETY ENGINE</h4>
                            <p className="text-2xl font-black mb-1">Deterministic</p>
                            <p className="text-xs text-slate-400">Zero AI involvement for critical interaction mapping.</p>
                        </div>
                        <div className="bg-white/5 rounded-3xl p-6 border border-white/10">
                            <h4 className="text-xs font-black uppercase tracking-widest text-emerald-400 mb-4">PHI PROTECTION</h4>
                            <p className="text-2xl font-black mb-1">Active Masking</p>
                            <p className="text-xs text-slate-400">No PHI transmitted to external Groq/LLM endpoints.</p>
                        </div>
                        <div className="bg-white/5 rounded-3xl p-6 border border-white/10">
                            <h4 className="text-xs font-black uppercase tracking-widest text-orange-400 mb-4">HUMAN-IN-LOOP</h4>
                            <p className="text-2xl font-black mb-1">Mandatory</p>
                            <p className="text-xs text-slate-400">All AI outputs require Clinician signature before record entry.</p>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

// Simple internal components not in standard library
function CheckCircle({ className }: { className?: string }) {
    return <Zap className={className} />;
}

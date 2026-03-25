"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { workflowApi } from '@/lib/api';
import { FileText, Plus, User, LogOut, ChevronLeft, ShieldAlert, Activity, CheckCircle, TrendingUp, AlertTriangle } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function ShiftBriefingPage() {
    const [briefing, setBriefing] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const { logout, isLoading, fbUser } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!isLoading && fbUser) {
            fetchBriefing();
        }
    }, [isLoading, fbUser]);

    const fetchBriefing = async () => {
        try {
            setLoading(true);
            const res = await workflowApi.getShiftBriefing();
            setBriefing(res.data);
        } catch (err) {
            console.error("Failed to load shift briefing", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex h-screen bg-slate-50">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-900 text-white flex flex-col pt-8">
                <div className="px-6 mb-10">
                    <div className="bg-teal-600 w-10 h-10 rounded-lg flex items-center justify-center font-bold text-xl mb-4">C</div>
                    <h1 className="text-xl font-bold">Clinical Assistant</h1>
                </div>

                <nav className="flex-1 px-4 space-y-2">
                    <Link href="/dashboard" className="flex items-center gap-3 px-4 py-3 text-slate-400 hover:bg-slate-800 hover:text-white rounded-lg transition-colors">
                        <FileText size={20} /> My Notes
                    </Link>
                    <Link href="/patients" className="flex items-center gap-3 px-4 py-3 text-slate-400 hover:bg-slate-800 hover:text-white rounded-lg transition-colors">
                        <User size={20} /> Patients
                    </Link>
                    <Link href="/shift-briefing" className="flex items-center gap-3 px-4 py-3 bg-slate-800 rounded-lg text-white font-medium">
                        <Activity size={20} /> Shift Briefing
                    </Link>
                    <Link href="/notes/new" className="flex items-center gap-3 px-4 py-3 text-slate-400 hover:bg-slate-800 hover:text-white rounded-lg transition-colors">
                        <Plus size={20} /> Create New
                    </Link>
                </nav>

                <div className="p-4 border-t border-slate-800">
                    <button onClick={logout} className="flex items-center gap-3 px-4 py-3 text-slate-400 hover:text-white w-full transition-colors">
                        <LogOut size={20} /> Logout
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto p-10 relative">
                <header className="mb-8">
                    <Link href="/dashboard" className="inline-flex items-center gap-2 text-slate-400 hover:text-teal-600 transition-colors mb-4 text-sm font-bold">
                        <ChevronLeft size={16} /> Back to Dashboard
                    </Link>
                    <h2 className="text-3xl font-black text-slate-900 flex items-center gap-3">
                        <SparklesIcon /> Shift-End Intelligence Briefing
                    </h2>
                    <p className="text-slate-500 mt-2 font-medium">Automated handover summary and critical action tracking.</p>
                </header>

                {loading ? (
                    <div className="grid place-items-center h-64">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                    </div>
                ) : briefing ? (
                    <div className="max-w-4xl space-y-8 pb-20">
                        {/* High-Level Stats */}
                        <div className="grid grid-cols-3 gap-6">
                            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4">
                                <div className="p-4 bg-teal-50 text-teal-600 rounded-xl"><User size={24} /></div>
                                <div>
                                    <p className="text-sm font-bold text-slate-400 uppercase tracking-widest">Encounters</p>
                                    <p className="text-3xl font-black text-slate-900">{briefing.stats?.total_encounters || 0}</p>
                                </div>
                            </div>
                            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4">
                                <div className="p-4 bg-red-50 text-red-600 rounded-xl"><ShieldAlert size={24} /></div>
                                <div>
                                    <p className="text-sm font-bold text-slate-400 uppercase tracking-widest">High Risk</p>
                                    <p className="text-3xl font-black text-slate-900">{briefing.stats?.high_risk || 0}</p>
                                </div>
                            </div>
                            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4">
                                <div className="p-4 bg-amber-50 text-amber-600 rounded-xl"><AlertTriangle size={24} /></div>
                                <div>
                                    <p className="text-sm font-bold text-slate-400 uppercase tracking-widest">Pending Charts</p>
                                    <p className="text-3xl font-black text-slate-900">{briefing.stats?.pending_charts || 0}</p>
                                </div>
                            </div>
                        </div>

                        {/* Executive Summary */}
                        <section className="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-3xl p-8 text-white shadow-xl relative overflow-hidden">
                            <div className="absolute right-0 top-0 w-64 h-64 bg-indigo-500/20 blur-[80px] rounded-full translate-x-1/2 -translate-y-1/2" />
                            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-indigo-300 mb-4 flex items-center gap-2"><TrendingUp size={16} /> Executive Summary</h3>
                            <p className="text-lg leading-relaxed text-slate-100 font-medium">{briefing.briefing?.executive_summary}</p>
                        </section>

                        <div className="grid md:grid-cols-2 gap-8">
                            {/* Critical Actions */}
                            <section className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm">
                                <h3 className="text-xs font-black uppercase tracking-[0.2em] text-amber-500 mb-6 flex items-center gap-2"><AlertTriangle size={16} /> Critical Follow-ups</h3>
                                {briefing.briefing?.critical_actions?.length > 0 ? (
                                    <ul className="space-y-4">
                                        {briefing.briefing.critical_actions.map((action: string, idx: number) => (
                                            <li key={idx} className="flex gap-3 text-slate-700 items-start">
                                                <div className="mt-1 w-2 h-2 rounded-full bg-amber-400 shrink-0" />
                                                <span className="font-medium leading-relaxed">{action}</span>
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <div className="flex items-center gap-3 text-emerald-600 bg-emerald-50 p-4 rounded-xl">
                                        <CheckCircle size={20} /> <span className="font-bold">No pending critical actions.</span>
                                    </div>
                                )}
                            </section>

                            {/* High Risk Cases */}
                            <section className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm">
                                <h3 className="text-xs font-black uppercase tracking-[0.2em] text-red-500 mb-6 flex items-center gap-2"><ShieldAlert size={16} /> High-Risk Encounters</h3>
                                {briefing.briefing?.high_risk_cases_summarized?.length > 0 ? (
                                    <ul className="space-y-4">
                                        {briefing.briefing.high_risk_cases_summarized.map((caseInfo: string, idx: number) => (
                                            <li key={idx} className="flex gap-3 text-slate-700 items-start p-4 bg-red-50/50 border border-red-100 rounded-xl">
                                                <ShieldAlert size={16} className="text-red-500 mt-0.5 shrink-0" />
                                                <span className="font-medium leading-relaxed">{caseInfo}</span>
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <div className="flex items-center gap-3 text-emerald-600 bg-emerald-50 p-4 rounded-xl">
                                        <CheckCircle size={20} /> <span className="font-bold">No high-risk cases identified.</span>
                                    </div>
                                )}
                            </section>
                        </div>
                    </div>
                ) : (
                    <div className="bg-red-50 text-red-600 p-6 rounded-2xl flex gap-4 items-center">
                        <AlertTriangle />
                        <div>
                            <p className="font-bold">Briefing Unavailable</p>
                            <p className="text-sm">Could not generate the shift briefing at this time.</p>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

function SparklesIcon() {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-600">
            <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" />
        </svg>
    )
}

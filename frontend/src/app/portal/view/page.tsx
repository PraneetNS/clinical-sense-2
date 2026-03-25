"use client";

import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { portalApi, getErrorMessage } from '@/lib/api';
import { 
    Clock, Calendar, Stethoscope, Pill, AlertCircle, 
    ChevronRight, CheckCircle2, ShieldCheck, HeartPulse
} from 'lucide-react';

export default function PatientPortalView() {
    const searchParams = useSearchParams();
    const token = searchParams.get('token');
    
    const [loading, setLoading] = useState(true);
    const [summary, setSummary] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (token) {
            portalApi.getSummary(token)
                .then(res => {
                    if (res.data.expired) {
                        setError(res.data.error || "This link has expired.");
                    } else {
                        setSummary(res.data);
                    }
                })
                .catch(err => {
                    setError(getErrorMessage(err));
                })
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
            setError("No access token provided.");
        }
    }, [token]);

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center">
                <div className="animate-pulse flex flex-col items-center">
                    <div className="w-12 h-12 bg-indigo-500 rounded-2xl mb-4" />
                    <div className="h-4 w-32 bg-slate-200 rounded" />
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 text-center">
                <div className="max-w-md w-full bg-white rounded-3xl shadow-xl p-10 border border-slate-100">
                    <div className="w-16 h-16 bg-red-50 text-red-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
                        <AlertCircle size={32} />
                    </div>
                    <h1 className="text-xl font-black text-slate-900 mb-3">Unable to Load Summary</h1>
                    <p className="text-slate-400 text-sm leading-relaxed mb-8">{error}</p>
                    <p className="text-xs text-slate-400">Please contact your healthcare provider's office for a new link or assistance.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Header Branding */}
            <header className="bg-white border-b border-slate-100 px-6 py-6 text-center">
                <div className="inline-flex items-center gap-2 mb-1">
                    <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-600/20">
                        <ShieldCheck size={18} className="text-white" />
                    </div>
                    <span className="text-sm font-black text-slate-900 tracking-tight">ClinicalSense Secure Patient Portal</span>
                </div>
                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Confidential Health Summary</p>
            </header>

            <main className="max-w-2xl mx-auto px-6 py-10">
                <div className="mb-10 text-center">
                    <h1 className="text-3xl font-black text-slate-900 mb-2">Hello, {summary.patient_first_name}</h1>
                    <p className="text-slate-500 text-sm font-medium">Your visit summary from your encounter on {summary.visit_date}</p>
                </div>

                {/* Main Card */}
                <div className="bg-white rounded-3xl shadow-xl shadow-indigo-600/5 border border-slate-100 overflow-hidden mb-8">
                    {/* Hero Section */}
                    <div className="bg-gradient-to-r from-indigo-600 to-blue-600 p-8 text-white">
                        <div className="flex items-center gap-2 mb-3">
                            <HeartPulse size={20} className="text-indigo-200" />
                            <h2 className="text-xs font-black uppercase tracking-widest text-indigo-100">Visit Summary</h2>
                        </div>
                        <p className="text-white text-lg font-bold leading-relaxed">{summary.summary}</p>
                    </div>

                    <div className="p-8 space-y-10">
                        {/* Medications */}
                        {summary.medications?.length > 0 && (
                            <section>
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center">
                                        <Pill size={20} />
                                    </div>
                                    <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest">Prescribed Medications</h3>
                                </div>
                                <div className="space-y-3">
                                    {summary.medications.map((med: string, i: number) => (
                                        <div key={i} className="flex items-center gap-3 p-4 bg-slate-50 rounded-2xl border border-slate-100 transition-colors hover:bg-white hover:shadow-lg hover:shadow-slate-200/50">
                                            <div className="w-2 h-2 rounded-full bg-emerald-500" />
                                            <span className="text-sm font-bold text-slate-700">{med}</span>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        )}

                        {/* Follow-up */}
                        <section>
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-amber-50 text-amber-600 rounded-xl flex items-center justify-center">
                                    <Calendar size={20} />
                                </div>
                                <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest">Follow-Up Instructions</h3>
                            </div>
                            <div className="p-4 bg-amber-50 rounded-2xl border border-amber-100 border-l-4 border-l-amber-500">
                                <p className="text-sm text-amber-900 leading-relaxed font-bold">{summary.followup_instructions}</p>
                            </div>
                        </section>
                        
                        {/* Security Footer */}
                        <div className="pt-8 border-t border-slate-50 text-center">
                            <div className="inline-flex items-center gap-1 px-3 py-1 bg-slate-50 text-slate-400 rounded-full text-[10px] font-black uppercase tracking-widest mb-3">
                                <CheckCircle2 size={10} /> Secure End-to-End Encryption
                            </div>
                            <p className="text-[10px] text-slate-300 max-w-xs mx-auto leading-relaxed">This summary is temporary and will expire in 48 hours for your security. Please save or print this page if you need to keep it for your records.</p>
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-3">
                    <button onClick={() => window.print()} className="w-full py-4 bg-white border border-slate-200 text-slate-700 font-bold text-sm rounded-2xl shadow-sm hover:bg-slate-50 transition-colors">
                        Download / Print Summary
                    </button>
                </div>
                
                <footer className="mt-16 text-center text-slate-400 pb-10">
                    <p className="text-[10px] font-bold uppercase tracking-widest mb-1">Powered by ClinicalSense IQ</p>
                    <p className="text-[10px]">© 2026 Clinical Intelligence Platform. All rights reserved.</p>
                </footer>
            </main>
        </div>
    );
}

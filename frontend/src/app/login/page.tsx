"use client";

import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { authApi } from '@/lib/api';
import { Shield, Lock, Mail, ArrowRight } from 'lucide-react';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { login } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const response = await authApi.login({
                username: email,
                password: password,
                grant_type: 'password'
            });
            const { access_token } = response.data;

            login(access_token);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || "Invalid clinical credentials or server connection error.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[calc(100-36px)] flex items-center justify-center p-6 sm:p-12">
            <div className="bg-white rounded-[2.5rem] shadow-2xl overflow-hidden w-full max-w-5xl flex flex-col md:flex-row min-h-[600px] border border-slate-100">

                {/* Brand Side */}
                <div className="md:w-5/12 bg-slate-900 p-12 text-white flex flex-col justify-between">
                    <div>
                        <div className="flex items-center gap-3 mb-10">
                            <div className="w-12 h-12 bg-teal-500 rounded-2xl flex items-center justify-center font-bold text-2xl shadow-lg shadow-teal-500/20">
                                C
                            </div>
                            <h1 className="text-2xl font-bold tracking-tight">Clinical Assistant</h1>
                        </div>

                        <h2 className="text-4xl font-bold mb-8 leading-tight">AI Accuracy. Clinician Safety.</h2>

                        <div className="space-y-6">
                            <div className="flex gap-4 items-start">
                                <div className="bg-teal-500/10 p-2 rounded-xl">
                                    <Shield size={22} className="text-teal-400" />
                                </div>
                                <div>
                                    <h3 className="font-bold text-lg">Secure & Private</h3>
                                    <p className="text-slate-400 text-sm leading-relaxed">Encrypted storage and private AI inference for patient data safety.</p>
                                </div>
                            </div>

                            <div className="flex gap-4 items-start">
                                <div className="bg-blue-500/10 p-2 rounded-xl">
                                    <Shield size={22} className="text-blue-400" />
                                </div>
                                <div>
                                    <h3 className="font-bold text-lg">SOAP Structure</h3>
                                    <p className="text-slate-400 text-sm leading-relaxed">Automated restructuring of raw observations into professional documentation.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="text-xs text-slate-500 font-medium uppercase tracking-widest pt-10">
                        Powered by Clinical-AI Engine v1.0
                    </div>
                </div>

                {/* Form Side */}
                <div className="flex-1 p-12 md:p-20 bg-white">
                    <div className="mb-12">
                        <h2 className="text-3xl font-bold text-slate-900 mb-3">Clinician Login</h2>
                        <p className="text-slate-500">Access your secure documentation workspace.</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && (
                            <div className="p-4 bg-red-50 border border-red-100 text-red-600 rounded-2xl text-sm font-bold flex items-center gap-2">
                                <Shield size={16} /> {error}
                            </div>
                        )}

                        <div className="space-y-2">
                            <label className="text-sm font-bold text-slate-700 ml-1">Work Email</label>
                            <div className="relative">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-100 rounded-2xl focus:ring-2 focus:ring-teal-500/50 focus:bg-white outline-none transition-all"
                                    placeholder="name@hospital.org"
                                    required
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between items-center px-1">
                                <label className="text-sm font-bold text-slate-700">Security Password</label>
                                <button type="button" className="text-teal-600 text-xs font-bold hover:underline">Reset</button>
                            </div>
                            <div className="relative">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-100 rounded-2xl focus:ring-2 focus:ring-teal-500/50 focus:bg-white outline-none transition-all"
                                    placeholder="••••••••••••"
                                    required
                                />
                            </div>
                        </div>

                        <button
                            disabled={loading}
                            className="w-full py-4 bg-teal-600 text-white font-bold rounded-2xl shadow-xl shadow-teal-600/20 hover:bg-teal-700 transition-all flex items-center justify-center gap-2 active:scale-[0.98] disabled:opacity-50"
                        >
                            {loading ? "Authenticating..." : (
                                <>Enter Workspace <ArrowRight size={20} /></>
                            )}
                        </button>
                    </form>

                    <div className="mt-12 pt-8 border-t border-slate-100 flex justify-between items-center">
                        <span className="text-xs text-slate-400 font-bold uppercase tracking-tighter">Compliance Status</span>
                        <div className="flex gap-3">
                            <div className="bg-slate-50 px-3 py-1.5 rounded-lg text-[10px] font-bold text-slate-500 border border-slate-100">HIPAA</div>
                            <div className="bg-slate-50 px-3 py-1.5 rounded-lg text-[10px] font-bold text-slate-500 border border-slate-100">SOC2</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

"use client";

import React, { useState } from 'react';
import { auth } from '@/lib/firebase';
import {
    createUserWithEmailAndPassword,
    GoogleAuthProvider,
    signInWithPopup
} from 'firebase/auth';
import { Shield, Lock, Mail, ArrowRight, UserPlus } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function RegisterPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            await createUserWithEmailAndPassword(auth, email, password);
            // Full name can be updated in backend during sync in AuthContext
            router.push('/dashboard');
        } catch (err: any) {
            console.error(err);
            setError(err.message || "Registration failed. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleLogin = async () => {
        setLoading(true);
        setError(null);
        try {
            const provider = new GoogleAuthProvider();
            await signInWithPopup(auth, provider);
            router.push('/dashboard');
        } catch (err: any) {
            console.error(err);
            setError("Google login failed.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[calc(100vh-36px)] flex items-center justify-center p-6 sm:p-12">
            <div className="bg-white rounded-[2.5rem] shadow-2xl overflow-hidden w-full max-w-5xl flex flex-col md:flex-row min-h-[650px] border border-slate-100">

                {/* Brand Side */}
                <div className="md:w-5/12 bg-slate-900 p-12 text-white flex flex-col justify-between">
                    <div>
                        <div className="flex items-center gap-3 mb-10">
                            <div className="w-12 h-12 bg-teal-500 rounded-2xl flex items-center justify-center font-bold text-2xl shadow-lg shadow-teal-500/20">
                                C
                            </div>
                            <h1 className="text-2xl font-bold tracking-tight">Clinical Assistant</h1>
                        </div>

                        <h2 className="text-4xl font-bold mb-8 leading-tight">Join the Network of Modern Clinicians.</h2>

                        <div className="space-y-6">
                            <div className="flex gap-4 items-start">
                                <div className="bg-teal-500/10 p-2 rounded-xl">
                                    <Shield size={22} className="text-teal-400" />
                                </div>
                                <div>
                                    <h3 className="font-bold text-lg">Secure & Private</h3>
                                    <p className="text-slate-400 text-sm leading-relaxed">Identity managed by Firebase Auth with HIPAA compliance in mind.</p>
                                </div>
                            </div>

                            <div className="flex gap-4 items-start">
                                <div className="bg-blue-500/10 p-2 rounded-xl">
                                    <Shield size={22} className="text-blue-400" />
                                </div>
                                <div>
                                    <h3 className="font-bold text-lg">Supabase Cloud</h3>
                                    <p className="text-slate-400 text-sm leading-relaxed">Centralized clinical data with real-time durability.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="text-xs text-slate-500 font-medium uppercase tracking-widest pt-10">
                        Powered by Clinical-AI & Firebase
                    </div>
                </div>

                {/* Form Side */}
                <div className="flex-1 p-12 md:p-16 bg-white overflow-y-auto">
                    <div className="mb-8">
                        <h2 className="text-3xl font-bold text-slate-900 mb-2">Create Clinician Account</h2>
                        <p className="text-slate-500">Access your secure documentation workspace.</p>
                    </div>

                    <form onSubmit={handleRegister} className="space-y-5">
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
                            <label className="text-sm font-bold text-slate-700 ml-1">Security Password</label>
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
                            type="submit"
                            disabled={loading}
                            className="w-full py-4 bg-teal-600 text-white font-bold rounded-2xl shadow-xl shadow-teal-600/20 hover:bg-teal-700 transition-all flex items-center justify-center gap-2 active:scale-[0.98] disabled:opacity-50"
                        >
                            {loading ? "Processing..." : (
                                <>Register Now <ArrowRight size={20} /></>
                            )}
                        </button>
                    </form>

                    <div className="mt-6 flex items-center gap-4">
                        <div className="flex-1 h-[1px] bg-slate-100"></div>
                        <span className="text-xs font-bold text-slate-400 uppercase">Or use social</span>
                        <div className="flex-1 h-[1px] bg-slate-100"></div>
                    </div>

                    <button
                        type="button"
                        onClick={handleGoogleLogin}
                        disabled={loading}
                        className="w-full mt-6 py-4 bg-white border-2 border-slate-100 text-slate-700 font-bold rounded-2xl hover:bg-slate-50 transition-all flex items-center justify-center gap-3 active:scale-[0.98]"
                    >
                        <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" className="w-5 h-5" alt="Google" />
                        Sign up with Google
                    </button>

                    <div className="mt-8 text-center">
                        <Link
                            href="/login"
                            className="text-sm font-bold text-teal-600 hover:underline"
                        >
                            Already have an account? Log in
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}

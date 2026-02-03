"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { patientsApi } from '@/lib/api';
import { ChevronLeft, Save, AlertCircle } from 'lucide-react';
import PatientForm from '@/components/forms/PatientForm';

export default function NewPatientPage() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();

    const handleSubmit = async (data: any) => {
        setLoading(true);
        setError(null);

        try {
            const res = await patientsApi.create(data);
            router.push(`/patients/${res.data.id}`);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || "Failed to create patient record.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col">
            <nav className="bg-white border-b border-slate-200 px-10 py-4 flex items-center gap-6">
                <Link href="/patients" className="text-slate-500 hover:text-teal-600 transition-colors">
                    <ChevronLeft size={24} />
                </Link>
                <h1 className="text-xl font-bold text-slate-900">Patient Intake</h1>
            </nav>

            <main className="flex-1 p-10 max-w-2xl mx-auto w-full">
                {error && (
                    <div className="mb-8 bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl flex items-center gap-3">
                        <AlertCircle size={20} />
                        <p className="text-sm font-medium">{error}</p>
                    </div>
                )}

                <div className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden p-8">
                    <div className="mb-8">
                        <h2 className="text-2xl font-black text-slate-900 flex items-center gap-3">
                            <div className="w-10 h-10 bg-teal-50 text-teal-600 rounded-xl flex items-center justify-center">
                                <Save size={20} />
                            </div>
                            Administrative Identity
                        </h2>
                        <p className="text-slate-500 text-sm mt-2">Initialize a new secure medical record for the patient.</p>
                    </div>

                    <PatientForm
                        onSubmit={handleSubmit}
                        onCancel={() => router.push('/patients')}
                    />
                </div>
            </main>
        </div>
    );
}

"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { patientsApi } from '@/lib/api';
import { Plus, Search, User, ChevronLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function PatientsPage() {
    const [patients, setPatients] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();

    useEffect(() => {
        fetchPatients();
    }, []);

    const fetchPatients = async (query = '') => {
        try {
            setLoading(true);
            const response = await patientsApi.getAll(query);
            setPatients(response.data);
        } catch (err) {
            console.error(err);
            setError("Failed to load patients.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen bg-slate-50">
            <main className="flex-1 overflow-auto p-10 max-w-7xl mx-auto">
                <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div className="flex items-center gap-4">
                        <Link href="/dashboard" className="text-slate-500 hover:text-teal-600 transition-colors">
                            <ChevronLeft size={24} />
                        </Link>
                        <div>
                            <h2 className="text-3xl font-bold text-slate-900">Patients</h2>
                            <p className="text-slate-500 text-sm mt-1">Manage patient records.</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                            <input
                                type="text"
                                placeholder="Search patients..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && fetchPatients(searchTerm)}
                                className="pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 outline-none w-64 shadow-sm text-sm"
                            />
                        </div>
                        <Link href="/patients/new" className="px-6 py-3 bg-teal-600 text-white font-bold rounded-xl shadow-lg hover:bg-teal-700 transition-all flex items-center gap-2">
                            <Plus size={20} /> Add Patient
                        </Link>
                    </div>
                </header>

                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
                    </div>
                ) : error ? (
                    <div className="bg-red-50 text-red-600 p-4 rounded-xl border border-red-100">{error}</div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {patients.map((patient) => (
                            <Link href={`/patients/${patient.id}`} key={patient.id} className="block group">
                                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all group-hover:border-teal-200">
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="bg-teal-50 p-3 rounded-full">
                                            <User size={24} className="text-teal-600" />
                                        </div>
                                        <span className="text-xs font-mono bg-slate-100 px-2 py-1 rounded text-slate-500">
                                            MRN: {patient.mrn}
                                        </span>
                                    </div>
                                    <h3 className="text-lg font-bold text-slate-900 mb-1 group-hover:text-teal-600 transition-colors">
                                        {patient.name}
                                    </h3>
                                    <p className="text-sm text-slate-500">
                                        DOB: {patient.date_of_birth ? new Date(patient.date_of_birth).toLocaleDateString() : 'N/A'}
                                    </p>
                                </div>
                            </Link>
                        ))}

                        {patients.length === 0 && (
                            <div className="col-span-full text-center py-20 text-slate-400">
                                <User size={48} className="mx-auto mb-4 opacity-20" />
                                <p>No patients found. Add one to get started.</p>
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}

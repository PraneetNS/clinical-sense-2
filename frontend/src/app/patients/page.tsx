"use client";

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { patientsApi } from '@/lib/api';
import { Plus, Search, User, ChevronLeft, Trash2, Loader2, AlertTriangle } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function PatientsPage() {
    const [patients, setPatients] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [deletingId, setDeletingId] = useState<number | null>(null);
    const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
    const { isLoading, fbUser } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!isLoading && fbUser) {
            fetchPatients();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isLoading, fbUser]);

    const fetchPatients = useCallback(async (query = '') => {
        try {
            setLoading(true);
            setError(null);
            const response = await patientsApi.getAll(query || undefined);
            setPatients(response.data);
        } catch (err: any) {
            console.error(err);
            const detail = err.response?.data?.detail || err.message || "Unknown connectivity error";
            setError(`Failed to load patients: ${detail}`);
        } finally {
            setLoading(false);
        }
    }, []);

    const handleDeleteClick = (e: React.MouseEvent, patientId: number) => {
        e.preventDefault();
        e.stopPropagation();
        setConfirmDeleteId(patientId);
    };

    const handleDeleteConfirm = async (patientId: number) => {
        try {
            setDeletingId(patientId);
            setConfirmDeleteId(null);
            await patientsApi.delete(patientId);
            setPatients(prev => prev.filter(p => p.id !== patientId));
        } catch (err: any) {
            const msg = err.response?.data?.detail || "Failed to delete patient";
            setError(msg);
        } finally {
            setDeletingId(null);
        }
    };

    return (
        <div className="flex min-h-screen bg-slate-50">
            {/* Delete Confirm Dialog */}
            {confirmDeleteId !== null && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
                    <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-sm w-full mx-4 border border-slate-200">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="bg-red-100 p-3 rounded-full">
                                <AlertTriangle size={22} className="text-red-600" />
                            </div>
                            <h3 className="text-lg font-bold text-slate-900">Delete Patient</h3>
                        </div>
                        <p className="text-slate-500 text-sm mb-6 leading-relaxed">
                            Are you sure you want to delete this patient record? This action cannot be undone and all associated data will be archived.
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setConfirmDeleteId(null)}
                                className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-slate-700 font-semibold hover:bg-slate-50 transition-colors text-sm"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => handleDeleteConfirm(confirmDeleteId)}
                                className="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700 transition-colors text-sm"
                            >
                                Yes, Delete
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <main className="flex-1 overflow-auto p-10 max-w-7xl mx-auto">
                <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div className="flex items-center gap-4">
                        <Link href="/dashboard" className="text-slate-500 hover:text-teal-600 transition-colors">
                            <ChevronLeft size={24} />
                        </Link>
                        <div>
                            <h2 className="text-3xl font-bold text-slate-900">Patients</h2>
                            <p className="text-slate-500 text-sm mt-1">
                                {!loading && `${patients.length} patient${patients.length !== 1 ? 's' : ''} in your records`}
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                            <input
                                type="text"
                                placeholder="Search name or MRN..."
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
                    <div className="flex flex-col items-center justify-center h-64 gap-3">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
                        <p className="text-slate-400 text-sm animate-pulse">Loading patients...</p>
                    </div>
                ) : error ? (
                    <div className="bg-red-50 text-red-600 p-4 rounded-xl border border-red-100 flex items-center gap-2">
                        <AlertTriangle size={18} />
                        {error}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {patients.map((patient) => (
                            <div key={patient.id} className="relative group">
                                <Link href={`/patients/${patient.id}`} className="block">
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
                                        <p className="text-sm text-slate-500 mb-1">
                                            DOB: {patient.date_of_birth ? new Date(patient.date_of_birth).toLocaleDateString() : 'N/A'}
                                        </p>
                                        {patient.status && (
                                            <span className={`inline-block text-xs px-2 py-0.5 rounded-full font-semibold mt-1 ${patient.status === 'Active' ? 'bg-green-50 text-green-700' :
                                                    patient.status === 'Closed' ? 'bg-slate-100 text-slate-500' :
                                                        'bg-amber-50 text-amber-700'
                                                }`}>
                                                {patient.status}
                                            </span>
                                        )}
                                    </div>
                                </Link>

                                {/* Delete button — visible on hover */}
                                <button
                                    onClick={(e) => handleDeleteClick(e, patient.id)}
                                    title="Delete patient"
                                    className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity bg-white border border-red-200 text-red-500 hover:bg-red-50 hover:border-red-400 p-2 rounded-lg shadow-sm"
                                >
                                    {deletingId === patient.id ? (
                                        <Loader2 size={16} className="animate-spin" />
                                    ) : (
                                        <Trash2 size={16} />
                                    )}
                                </button>
                            </div>
                        ))}

                        {patients.length === 0 && (
                            <div className="col-span-full text-center py-20 text-slate-400">
                                <User size={48} className="mx-auto mb-4 opacity-20" />
                                <p className="font-semibold">No patients found.</p>
                                <p className="text-sm mt-1">Add a new patient to get started.</p>
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}

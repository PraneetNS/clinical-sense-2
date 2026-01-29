"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { notesApi, patientsApi } from '@/lib/api';
import { ChevronLeft, Sparkles, AlertCircle, Save, AlertTriangle } from 'lucide-react';
import SOAPNoteEditor from '@/components/SOAPNoteEditor';

export default function NewNotePage() {
    const [title, setTitle] = useState('');
    const [rawContent, setRawContent] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [structuredData, setStructuredData] = useState<any | null>(null);
    const [noteId, setNoteId] = useState<number | null>(null);
    const [patients, setPatients] = useState<any[]>([]);
    const [selectedPatientId, setSelectedPatientId] = useState<number | undefined>(undefined);
    const [noteType, setNoteType] = useState('SOAP');
    const router = useRouter();

    // Local Draft Recovery
    useEffect(() => {
        patientsApi.getAll().then(res => setPatients(res.data)).catch(console.error);

        const savedDraft = localStorage.getItem('note_draft');
        const savedTitle = localStorage.getItem('note_title_draft');
        if (savedDraft) setRawContent(savedDraft);
        if (savedTitle) setTitle(savedTitle);
    }, []);

    useEffect(() => {
        localStorage.setItem('note_draft', rawContent);
        localStorage.setItem('note_title_draft', title);
    }, [rawContent, title]);

    const clearDraft = () => {
        localStorage.removeItem('note_draft');
        localStorage.removeItem('note_title_draft');
    };

    const handleGenerate = async () => {
        if (!rawContent.trim() || rawContent.length < 10) {
            setError("Clinical notes must be at least 10 characters long.");
            return;
        }

        try {
            setLoading(true);
            setError(null);
            const response = await notesApi.create({
                title: title || "Untitled Note",
                raw_content: rawContent,
                note_type: noteType,
                patient_id: selectedPatientId
            });
            const newNote = response.data;
            setNoteId(newNote.id);
            setStructuredData(newNote.structured_content);
            clearDraft();
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || "Failed to generate SOAP note. Please check your API connection.");
        } finally {
            setLoading(false);
        }
    };

    const handleRegenerate = async () => {
        if (!confirm("This will replace your current structured edits with a fresh AI generation. Continue?")) return;
        setStructuredData(null);
        handleGenerate();
    };

    const handleSave = async (updatedData: any, status: string = 'finalized') => {
        if (!noteId) return;

        try {
            setLoading(true);
            await notesApi.update(noteId, {
                structured_content: updatedData,
                status: status
            });
            router.push('/dashboard');
        } catch (err) {
            setError("Failed to save changes.");
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col">
            <nav className="bg-white border-b border-slate-200 px-10 py-4 flex items-center justify-between">
                <div className="flex items-center gap-6">
                    <Link href="/dashboard" className="text-slate-500 hover:text-teal-600 transition-colors">
                        <ChevronLeft size={24} />
                    </Link>
                    <h1 className="text-xl font-bold text-slate-900">New Clinical Documentation</h1>
                </div>
                {loading && <div className="text-teal-600 text-sm font-medium animate-pulse">Processing...</div>}
            </nav>

            <main className="flex-1 p-10 max-w-6xl mx-auto w-full">
                {error && (
                    <div className="mb-8 bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl flex items-center gap-3">
                        <AlertCircle size={20} />
                        <p className="text-sm font-medium">{error}</p>
                    </div>
                )}

                {!structuredData ? (
                    <div className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
                        <div className="p-8 space-y-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
                                <div>
                                    <label className="block text-sm font-semibold text-slate-700 mb-2">Patient (Optional)</label>
                                    <select
                                        value={selectedPatientId || ''}
                                        onChange={(e) => setSelectedPatientId(e.target.value ? Number(e.target.value) : undefined)}
                                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 outline-none"
                                    >
                                        <option value="">-- Select Patient --</option>
                                        {patients.map(p => (
                                            <option key={p.id} value={p.id}>{p.name} ({p.mrn})</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold text-slate-700 mb-2">Note Type</label>
                                    <select
                                        value={noteType}
                                        onChange={(e) => setNoteType(e.target.value)}
                                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 outline-none"
                                    >
                                        <option value="SOAP">SOAP Note</option>
                                        <option value="PROGRESS">Progress Note</option>
                                        <option value="DISCHARGE">Discharge Summary</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-slate-700 mb-2">Note Title</label>
                                <input
                                    type="text"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    placeholder="e.g. Pt #9822 - Recurring Migraine"
                                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 outline-none"
                                />
                            </div>

                            <div>
                                <div className="flex justify-between items-center mb-2">
                                    <label className="text-sm font-semibold text-slate-700">Raw Clinical Notes</label>
                                    <span className={`text-xs font-medium ${rawContent.length > 45000 ? 'text-red-500' : 'text-slate-400'}`}>
                                        {rawContent.length.toLocaleString()} / 50,000
                                    </span>
                                </div>
                                <textarea
                                    value={rawContent}
                                    onChange={(e) => setRawContent(e.target.value)}
                                    placeholder="Paste observation notes here... (min 10 characters)"
                                    className={`w-full h-80 px-4 py-3 bg-slate-50 border ${rawContent.length > 50000 ? 'border-red-500 bg-red-50' : 'border-slate-200'} rounded-xl focus:ring-2 focus:ring-teal-500 outline-none resize-none transition-all`}
                                    maxLength={50001}
                                />
                                {rawContent.length > 50000 && (
                                    <p className="text-red-500 text-xs mt-1 font-bold">Note exceeds maximum length of 50,000 characters.</p>
                                )}
                            </div>

                            <div className="flex items-center justify-between pt-4">
                                <p className="text-xs text-slate-400 italic flex-1 mr-8">
                                    Clicking the button below will use AI to restructure your text into SOAP format. This data is handled securely and according to privacy protocols.
                                </p>
                                <button
                                    onClick={handleGenerate}
                                    disabled={loading || !rawContent.trim() || rawContent.length > 50000}
                                    className="px-8 py-4 gradient-teal text-white font-bold rounded-2xl shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:grayscale flex items-center gap-2"
                                >
                                    <Sparkles size={20} /> Generate SOAP Note
                                </button>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-6">
                        <SOAPNoteEditor
                            initialData={structuredData}
                            onSave={handleSave}
                            noteType={noteType}
                        />
                        <div className="flex justify-center pb-20">
                            <button
                                onClick={handleRegenerate}
                                className="flex items-center gap-2 text-slate-400 hover:text-teal-600 transition-colors text-sm font-medium"
                            >
                                <AlertTriangle size={16} /> Not satisfied? Regenerate Structured Note
                            </button>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

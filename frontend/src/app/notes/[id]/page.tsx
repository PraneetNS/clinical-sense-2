"use client";

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { notesApi } from '@/lib/api';
import { ChevronLeft, AlertCircle, History, Trash2 } from 'lucide-react';
import { useToast } from '@/components/ui/Toast';
import SOAPNoteEditor from '@/components/SOAPNoteEditor';

export default function NoteDetailPage() {
    const { id } = useParams();
    const [note, setNote] = useState<any | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();
    const { showToast } = useToast();

    useEffect(() => {
        const fetchNote = async () => {
            try {
                setLoading(true);
                const response = await notesApi.getById(id as string);
                const fetchedNote = response.data;

                // Parse structured content string if it exists
                if (fetchedNote.structured_content) {
                    fetchedNote.structured_content = typeof fetchedNote.structured_content === 'string'
                        ? JSON.parse(fetchedNote.structured_content)
                        : fetchedNote.structured_content;
                }

                setNote(fetchedNote);
            } catch (err) {
                console.error(err);
                setError("Failed to load the note details.");
            } finally {
                setLoading(false);
            }
        };

        if (id) fetchNote();
    }, [id]);


    const handleDelete = async () => {
        if (!confirm("Are you sure you want to delete this note? This cannot be undone.")) return;
        try {
            setLoading(true);
            await notesApi.delete(id as string);
            router.push('/dashboard');
        } catch (err) {
            setError("Failed to delete the note.");
            setLoading(false);
        }
    };

    const [safetyErrors, setSafetyErrors] = useState<string[]>([]);

    const handleSave = async (updatedData: any, status: string) => {
        setSafetyErrors([]);
        setError(null);
        try {
            setLoading(true);
            await notesApi.update(id as string, {
                structured_content: updatedData,
                status: status
            });
            showToast(`Note ${status === 'finalized' ? 'finalized' : 'saved'} successfully`, "success");
            router.push(`/patients/${note.patient_id}?tab=notes`);
        } catch (err: any) {
            setLoading(false);
            if (err.response && err.response.data && err.response.data.detail) {
                // If backend returns HTTPException with detail
                const detail = err.response.data.detail;
                if (detail.includes("Safety Violation")) {
                    // Extract violations
                    // detail string format: "Safety Violation: Reason 1; Reason 2"
                    const violations = detail.replace("Safety Violation: ", "").split("; ");
                    setSafetyErrors(violations);
                    return;
                }
                setError(detail);
            } else {
                setError("Failed to save changes due to a network or server error.");
            }
        }
    };

    if (loading && !note) {
        return (
            <div className="flex items-center justify-center h-screen bg-slate-50">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col">
            <nav className="bg-white border-b border-slate-200 px-10 py-4 flex items-center justify-between">
                <div className="flex items-center gap-6">
                    <Link href="/dashboard" className="text-slate-500 hover:text-teal-600 transition-colors">
                        <ChevronLeft size={24} />
                    </Link>
                    <h1 className="text-xl font-bold text-slate-900">{note?.title || "Note Detail"}</h1>
                </div>
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => router.push(`/notes/${id}/history`)}
                        className="flex items-center gap-2 text-slate-500 hover:text-slate-800 transition-colors text-sm font-medium"
                    >
                        <History size={18} /> View Audit Logs
                    </button>
                    <div className="w-px h-6 bg-slate-200"></div>
                    <button
                        onClick={handleDelete}
                        className="flex items-center gap-2 text-red-400 hover:text-red-600 transition-colors text-sm font-medium"
                    >
                        <Trash2 size={18} /> Delete Note
                    </button>
                </div>
            </nav>

            <main className="flex-1 p-10 max-w-6xl mx-auto w-full">
                {/* Safety Violations */}
                {safetyErrors.length > 0 && (
                    <div className="mb-8 bg-red-50 border border-red-200 p-6 rounded-xl animate-shake">
                        <div className="flex items-start gap-4">
                            <div className="p-2 bg-red-100 rounded-lg text-red-600">
                                <AlertCircle size={24} />
                            </div>
                            <div className="flex-1">
                                <h3 className="text-lg font-bold text-red-800 mb-2">Safety Policy Violation</h3>
                                <p className="text-sm text-red-600 mb-4">
                                    Your input contains restricted language. The system prevents saving content that includes prescriptive advice, specific dosage recommendations, or prognostic guarantees.
                                </p>
                                <ul className="list-disc pl-5 space-y-1">
                                    {safetyErrors.map((err, i) => (
                                        <li key={i} className="text-sm font-medium text-red-800">{err}</li>
                                    ))}
                                </ul>
                                <div className="mt-4 p-3 bg-white/50 rounded-lg text-xs text-red-800 font-mono">
                                    Please rephrase using observational language (&quot;Patient reports taking...&quot;, &quot;Clinician plans to prescribe...&quot;)
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {error && (
                    <div className="mb-8 bg-orange-50 border border-orange-200 text-orange-800 p-4 rounded-xl flex items-center gap-3">
                        <AlertCircle size={20} />
                        <p className="text-sm font-medium">{error}</p>
                    </div>
                )}

                {note?.structured_content ? (
                    <SOAPNoteEditor
                        initialData={note.structured_content}
                        onSave={handleSave}
                        noteType={note.note_type}
                    />
                ) : (
                    <div className="bg-white rounded-3xl p-12 text-center border border-slate-200">
                        <AlertCircle size={48} className="mx-auto text-amber-500 mb-4" />
                        <h2 className="text-xl font-bold text-slate-900 mb-2">Structure Not Found</h2>
                        <p className="text-slate-500 mb-8">This note hasn&apos;t been structured into SOAP format yet.</p>
                        <button
                            onClick={() => router.push('/notes/new')}
                            className="px-6 py-3 bg-teal-600 text-white font-bold rounded-xl"
                        >
                            Generate Structure
                        </button>
                    </div>
                )}
            </main>
        </div>
    );
}

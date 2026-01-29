"use client";

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { notesApi } from '@/lib/api';
import { ChevronLeft, Clock, ArrowLeft } from 'lucide-react';

export default function NoteHistoryPage() {
    const { id } = useParams();
    const router = useRouter();
    const [history, setHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (id) fetchHistory();
    }, [id]);

    const fetchHistory = async () => {
        try {
            setLoading(true);
            const response = await notesApi.getHistory(id as string);
            setHistory(response.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen bg-slate-50">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col">
            <nav className="bg-white border-b border-slate-200 px-10 py-4 flex items-center gap-6">
                <button
                    onClick={() => router.back()}
                    className="text-slate-500 hover:text-teal-600 transition-colors"
                >
                    <ArrowLeft size={24} />
                </button>
                <h1 className="text-xl font-bold text-slate-900">Version History</h1>
            </nav>

            <main className="flex-1 p-10 max-w-4xl mx-auto w-full">
                <div className="space-y-6">
                    {history.length === 0 ? (
                        <div className="text-center py-20 bg-white rounded-3xl border border-slate-200">
                            <Clock size={48} className="mx-auto text-slate-300 mb-4" />
                            <p className="text-slate-500 font-medium">No version history available.</p>
                            <p className="text-slate-400 text-sm">Edits will appear here.</p>
                        </div>
                    ) : (
                        history.map((version, index) => (
                            <div key={version.id} className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                                <div className="flex justify-between items-center mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="bg-teal-50 text-teal-700 font-bold px-3 py-1 rounded-lg text-sm">
                                            v{history.length - index}
                                        </div>
                                        <span className="text-slate-500 text-sm">
                                            {new Date(version.created_at).toLocaleDateString()} at {new Date(version.created_at).toLocaleTimeString()}
                                        </span>
                                    </div>
                                </div>

                                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-sm font-mono text-slate-700 overflow-x-auto">
                                    <pre>{JSON.stringify(JSON.parse(version.structured_content || '{}'), null, 2)}</pre>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </main>
        </div>
    );
}

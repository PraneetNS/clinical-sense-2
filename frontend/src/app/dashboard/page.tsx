"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { notesApi } from '@/lib/api';
import { FileText, Plus, Clock, ChevronRight, Search, LogOut, Trash2, User } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function DashboardPage() {
    const [notes, setNotes] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [searchMode, setSearchMode] = useState('keyword');
    const [error, setError] = useState<string | null>(null);
    const { logout, isLoading, fbUser } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!isLoading && fbUser) {
            fetchNotes();
        }
    }, [isLoading, fbUser]);

    const fetchNotes = async (query = '', mode = 'keyword') => {
        try {
            setLoading(true);
            const response = await notesApi.getAll(query, mode);
            setNotes(response.data);
        } catch (err: any) {
            console.error(err);
            const detail = err.response?.data?.detail || err.message || "Unknown connectivity error";
            setError(`Failed to load clinical notes: ${detail}`);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (e: React.MouseEvent, id: number) => {
        e.preventDefault();
        e.stopPropagation();
        if (!confirm("Are you sure you want to delete this note? This action can be undone by an administrator.")) return;

        try {
            await notesApi.delete(id);
            fetchNotes(searchTerm, searchMode);
        } catch (err) {
            alert("Failed to delete note.");
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
                    <Link href="/dashboard" className="flex items-center gap-3 px-4 py-3 bg-slate-800 rounded-lg text-white font-medium">
                        <FileText size={20} /> My Notes
                    </Link>
                    <Link href="/patients" className="flex items-center gap-3 px-4 py-3 text-slate-400 hover:bg-slate-800 hover:text-white rounded-lg transition-colors">
                        <User size={20} /> Patients
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
            <main className="flex-1 overflow-auto p-10">
                <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <h2 className="text-3xl font-bold text-slate-900">Clinical Documentation</h2>
                        <p className="text-slate-500 text-sm mt-1">Review and manage your structured SOAP notes.</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                            <input
                                type="text"
                                placeholder="Search by title..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && fetchNotes(searchTerm, searchMode)}
                                className="pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 outline-none w-64 shadow-sm text-sm"
                            />
                        </div>
                        <select
                            value={searchMode}
                            onChange={(e) => {
                                setSearchMode(e.target.value);
                                if (searchTerm.trim()) fetchNotes(searchTerm, e.target.value);
                            }}
                            className="py-3 px-4 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 outline-none shadow-sm text-sm"
                        >
                            <option value="keyword">Keyword</option>
                            <option value="semantic">Semantic (AI)</option>
                        </select>
                        <Link href="/notes/new" className="px-6 py-3 bg-teal-600 text-white font-bold rounded-xl shadow-lg hover:bg-teal-700 transition-all flex items-center gap-2">
                            <Plus size={20} /> New Note
                        </Link>
                    </div>
                </header>

                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
                    </div>
                ) : error ? (
                    <div className="bg-red-50 border border-red-200 text-red-700 p-6 rounded-2xl flex items-center gap-4">
                        <Clock className="text-red-400" />
                        <div>
                            <p className="font-bold">Error Loading Data</p>
                            <p className="text-sm">{error}</p>
                        </div>
                    </div>
                ) : notes.length === 0 ? (
                    <div className="text-center py-20 bg-white rounded-3xl border-2 border-dashed border-slate-200">
                        <FileText size={48} className="mx-auto text-slate-300 mb-4" />
                        <h3 className="text-lg font-bold text-slate-900">No notes found</h3>
                        <p className="text-slate-500 mb-6">Start by creating your first structured SOAP note.</p>
                        <Link href="/notes/new" className="text-teal-600 font-bold hover:underline">Create a note now &rarr;</Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 gap-4">
                        {notes.map((note) => (
                            <Link key={note.id} href={`/notes/${note.id}`} className="group bg-white p-6 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-all flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center text-slate-500 group-hover:bg-teal-50 group-hover:text-teal-600 transition-colors">
                                        <FileText size={24} />
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-slate-900">{note.title || "Untitled Note"}</h4>
                                        <p className="text-xs text-slate-400 mt-1">
                                            {new Date(note.created_at).toLocaleDateString()} at {new Date(note.created_at).toLocaleTimeString()}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="flex flex-col items-end gap-2">
                                        {note.status === 'finalized' ? (
                                            <span className="text-[10px] uppercase tracking-widest font-bold bg-blue-100 text-blue-700 px-2 py-1 rounded">Finalized</span>
                                        ) : (
                                            <span className="text-[10px] uppercase tracking-widest font-bold bg-orange-100 text-orange-700 px-2 py-1 rounded">Draft</span>
                                        )}
                                        {note.structured_content && (
                                            <span className="text-[10px] uppercase tracking-widest font-bold bg-green-100 text-green-700 px-2 py-1 rounded">Structured</span>
                                        )}
                                    </div>
                                    <button
                                        onClick={(e) => handleDelete(e, note.id)}
                                        className="p-2 text-slate-300 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                                        title="Delete Note"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                    <ChevronRight size={20} className="text-slate-300 group-hover:text-teal-600 transition-colors" />
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}

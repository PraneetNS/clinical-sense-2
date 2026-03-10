"use client";

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { prescriptionApi, encounterApi, patientsApi, getErrorMessage } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/ui/Toast';
import Link from 'next/link';
import {
    ChevronLeft, Printer, Download, Save, Plus, Trash2,
    Pill, Stethoscope, FileText, User, Calendar, Shield,
    Loader2, CheckCircle, AlertCircle, Clock
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface PrescriptionItem {
    medicine_name: string;
    dosage: string;
    frequency: string;
    duration: string;
    time_of_day: string[];
    special_instruction: string;
}

export default function PrescriptionPage() {
    const { id } = useParams(); // encounter id
    const router = useRouter();
    const { user } = useAuth();
    const { showToast } = useToast();

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [downloading, setDownloading] = useState(false);
    const [encounter, setEncounter] = useState<any>(null);
    const [patient, setPatient] = useState<any>(null);

    const [diagnosis, setDiagnosis] = useState('');
    const [notes, setNotes] = useState('');
    const [items, setItems] = useState<PrescriptionItem[]>([]);

    const [prescriptionId, setPrescriptionId] = useState<string | null>(null);

    useEffect(() => {
        if (id) {
            loadData();
        }
    }, [id]);

    const loadData = async () => {
        setLoading(true);
        try {
            // 1. Load Encounter
            const eRes = await encounterApi.get(id as string);
            const enc = eRes.data;
            setEncounter(enc);

            // 2. Load Patient
            const pRes = await patientsApi.getById(enc.patient_id);
            setPatient(pRes.data);

            // 3. Try to prefill from AI
            try {
                const prefillRes = await prescriptionApi.prefill(id as string);
                setDiagnosis(prefillRes.data.diagnosis || '');
                setItems(prefillRes.data.prescription_items || []);
            } catch (pErr) {
                console.error("Prefill failed", pErr);
                // Fallback to empty
                setItems([{
                    medicine_name: '',
                    dosage: '',
                    frequency: '',
                    duration: '',
                    time_of_day: [],
                    special_instruction: ''
                }]);
            }
        } catch (err) {
            showToast(getErrorMessage(err), 'error');
            router.push('/dashboard');
        } finally {
            setLoading(false);
        }
    };

    const addItem = () => {
        setItems([...items, {
            medicine_name: '',
            dosage: '',
            frequency: '',
            duration: '',
            time_of_day: [],
            special_instruction: ''
        }]);
    };

    const removeItem = (index: number) => {
        setItems(items.filter((_, i) => i !== index));
    };

    const updateItem = (index: number, field: keyof PrescriptionItem, value: any) => {
        const newItems = [...items];
        newItems[index] = { ...newItems[index], [field]: value };
        setItems(newItems);
    };

    const toggleTimeOfDay = (index: number, time: string) => {
        const item = items[index];
        const times = item.time_of_day.includes(time)
            ? item.time_of_day.filter(t => t !== time)
            : [...item.time_of_day, time];
        updateItem(index, 'time_of_day', times);
    };

    const handleSave = async () => {
        if (items.length === 0 || !items[0].medicine_name) {
            showToast("Please add at least one medication.", "error");
            return;
        }

        setSaving(true);
        try {
            const data = {
                patient_id: encounter.patient_id,
                encounter_id: Number(id),
                diagnosis,
                notes,
                prescription_items: items
            };
            const res = await prescriptionApi.create(data);
            setPrescriptionId(res.data.id);
            showToast("Prescription saved successfully!", "success");
        } catch (err) {
            showToast(getErrorMessage(err), 'error');
        } finally {
            setSaving(false);
        }
    };

    const handleDownloadPdf = async () => {
        if (!prescriptionId) return;
        setDownloading(true);
        try {
            const res = await prescriptionApi.downloadPdf(prescriptionId);
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `prescription_${prescriptionId.slice(0, 8)}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            showToast("Failed to download PDF", "error");
        } finally {
            setDownloading(false);
        }
    };

    const handlePrint = () => {
        window.print();
    };

    if (loading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50">
                <Loader2 size={40} className="text-teal-600 animate-spin mb-4" />
                <p className="text-slate-500 font-bold">Initializing Prescription Builder...</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 pb-20">
            {/* Header */}
            <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-xl border-b border-slate-100 px-8 py-4 flex items-center justify-between shadow-sm print:hidden">
                <div className="flex items-center gap-4">
                    <button onClick={() => router.back()} className="text-slate-400 hover:text-teal-600 transition-colors">
                        <ChevronLeft size={22} />
                    </button>
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-teal-600 rounded-xl flex items-center justify-center shadow-lg shadow-teal-600/20">
                            <Pill size={20} className="text-white" />
                        </div>
                        <div>
                            <h1 className="text-lg font-black text-slate-900 leading-tight">Prescription Generator</h1>
                            <p className="text-xs text-slate-400 font-medium">Encounter #{id} • {patient?.name}</p>
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    {prescriptionId ? (
                        <>
                            <button
                                onClick={handleDownloadPdf}
                                disabled={downloading}
                                className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 font-black text-sm rounded-xl hover:bg-slate-200 transition-all disabled:opacity-50"
                            >
                                {downloading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
                                Download PDF
                            </button>
                            <button
                                onClick={handlePrint}
                                className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white font-black text-sm rounded-xl hover:bg-black transition-all"
                            >
                                <Printer size={16} />
                                Print Slip
                            </button>
                        </>
                    ) : (
                        <button
                            onClick={handleSave}
                            disabled={saving}
                            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-teal-600 to-cyan-600 text-white font-black text-sm rounded-xl shadow-lg shadow-teal-600/25 hover:shadow-xl transition-all disabled:opacity-60"
                        >
                            {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                            Save & Generate
                        </button>
                    )}
                </div>
            </header>

            <main className="max-w-4xl mx-auto p-4 sm:p-8 space-y-8">
                {/* Print View Header (Hidden on Screen) */}
                <div className="hidden print:block text-center border-b-2 border-teal-600 pb-6 mb-8">
                    <h1 className="text-3xl font-black text-teal-600">CLINICAL SENSE</h1>
                    <p className="text-sm font-bold text-slate-500">DIGITAL HEALTH PLATFORM</p>
                    <div className="mt-4 flex justify-between text-left text-sm">
                        <div>
                            <p className="font-black">DR. {(user as any)?.full_name || 'Licensed Physician'}</p>
                            <p className="text-slate-500 italic">Medical Practitioner</p>
                        </div>
                        <div className="text-right">
                            <p className="font-bold">Date: {new Date().toLocaleDateString()}</p>
                            <p className="font-mono text-[10px] text-slate-400">ID: {prescriptionId?.slice(0, 8).toUpperCase()}</p>
                        </div>
                    </div>
                </div>

                {/* Patient Info Card */}
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 print:p-0 print:border-0 print:shadow-none">
                    <div className="flex items-center gap-2 mb-4 print:hidden">
                        <User size={16} className="text-teal-600" />
                        <h2 className="text-sm font-black text-slate-900 uppercase tracking-widest">Patient Information</h2>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 print:grid-cols-4 print:mb-8">
                        <div>
                            <p className="text-[10px] font-black text-slate-400 uppercase print:text-black">Patient Name</p>
                            <p className="text-sm font-bold text-slate-900">{patient?.name}</p>
                        </div>
                        <div>
                            <p className="text-[10px] font-black text-slate-400 uppercase print:text-black">Age / Gender</p>
                            <p className="text-sm font-bold text-slate-900">
                                {patient?.date_of_birth ? new Date().getFullYear() - new Date(patient.date_of_birth).getFullYear() : 'N/A'} / {patient?.gender || 'N/A'}
                            </p>
                        </div>
                        <div>
                            <p className="text-[10px] font-black text-slate-400 uppercase print:text-black">MRN</p>
                            <p className="text-sm font-bold text-slate-900">{patient?.mrn}</p>
                        </div>
                        <div className="print:hidden">
                            <p className="text-[10px] font-black text-slate-400 uppercase">Consultation Date</p>
                            <p className="text-sm font-bold text-slate-900">{new Date(encounter?.encounter_date).toLocaleDateString()}</p>
                        </div>
                    </div>
                </div>

                {/* Diagnosis Section */}
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 print:p-0 print:border-0 print:shadow-none">
                    <div className="flex items-center gap-2 mb-4 print:hidden">
                        <Stethoscope size={16} className="text-teal-600" />
                        <h2 className="text-sm font-black text-slate-900 uppercase tracking-widest">Diagnosis</h2>
                    </div>
                    <div className="hidden print:block mb-4">
                        <p className="text-xs font-black uppercase mb-1">Diagnosis:</p>
                        <p className="text-sm font-bold border-b border-slate-200 pb-1">{diagnosis || 'General Consultation'}</p>
                    </div>
                    <input
                        type="text"
                        value={diagnosis}
                        onChange={e => setDiagnosis(e.target.value)}
                        placeholder="Primary Diagnosis (e.g. Acute Bronchitis)"
                        className="w-full text-lg font-bold text-slate-900 placeholder-slate-200 border-0 focus:ring-0 p-0 print:hidden"
                    />
                </div>

                {/* Medication List */}
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden print:border-0 print:shadow-none">
                    <div className="px-6 py-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between print:hidden">
                        <div className="flex items-center gap-2">
                            <Pill size={16} className="text-teal-600" />
                            <h2 className="text-sm font-black text-slate-900 uppercase tracking-widest">Prescribed Medications</h2>
                        </div>
                        <button onClick={addItem} className="flex items-center gap-1.5 px-3 py-1 bg-white border border-slate-200 text-slate-600 text-xs font-black rounded-lg hover:bg-slate-50 transition-colors">
                            <Plus size={14} /> Add Medicine
                        </button>
                    </div>

                    <div className="hidden print:block mb-4">
                        <p className="text-xs font-black uppercase mb-4 tracking-widest">💊 PRESCRIPTION / Rx:</p>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-slate-50 print:bg-slate-100">
                                <tr className="text-left">
                                    <th className="px-6 py-3 font-black text-slate-400 text-[10px] uppercase print:text-black">Medicine Name</th>
                                    <th className="px-4 py-3 font-black text-slate-400 text-[10px] uppercase print:text-black">Dosage</th>
                                    <th className="px-4 py-3 font-black text-slate-400 text-[10px] uppercase print:text-black">Frequency</th>
                                    <th className="px-4 py-3 font-black text-slate-400 text-[10px] uppercase print:text-black">Duration</th>
                                    <th className="px-4 py-3 font-black text-slate-400 text-[10px] uppercase print:hidden">Time of Day</th>
                                    <th className="px-6 py-3 font-black text-slate-400 text-[10px] uppercase print:text-black">Instructions</th>
                                    <th className="px-6 py-3 print:hidden"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 print:divide-slate-200">
                                <AnimatePresence initial={false}>
                                    {items.map((item, idx) => (
                                        <motion.tr
                                            key={idx}
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, x: -20 }}
                                            className="hover:bg-slate-50/50 transition-colors"
                                        >
                                            <td className="px-6 py-4">
                                                <input
                                                    type="text"
                                                    value={item.medicine_name}
                                                    onChange={e => updateItem(idx, 'medicine_name', e.target.value)}
                                                    placeholder="Amoxicillin 500mg"
                                                    className="w-full bg-transparent border-0 p-0 focus:ring-0 font-bold text-slate-900"
                                                />
                                            </td>
                                            <td className="px-4 py-4">
                                                <input
                                                    type="text"
                                                    value={item.dosage}
                                                    onChange={e => updateItem(idx, 'dosage', e.target.value)}
                                                    placeholder="1 tab"
                                                    className="w-full bg-transparent border-0 p-0 focus:ring-0 text-slate-600"
                                                />
                                            </td>
                                            <td className="px-4 py-4">
                                                <input
                                                    type="text"
                                                    value={item.frequency}
                                                    onChange={e => updateItem(idx, 'frequency', e.target.value)}
                                                    placeholder="TDS"
                                                    className="w-full bg-transparent border-0 p-0 focus:ring-0 text-slate-600"
                                                />
                                            </td>
                                            <td className="px-4 py-4">
                                                <input
                                                    type="text"
                                                    value={item.duration}
                                                    onChange={e => updateItem(idx, 'duration', e.target.value)}
                                                    placeholder="5 days"
                                                    className="w-full bg-transparent border-0 p-0 focus:ring-0 text-slate-600"
                                                />
                                            </td>
                                            <td className="px-4 py-4 print:hidden">
                                                <div className="flex gap-1">
                                                    {['M', 'A', 'N'].map(t => (
                                                        <button
                                                            key={t}
                                                            onClick={() => toggleTimeOfDay(idx, t === 'M' ? 'Morning' : t === 'A' ? 'Afternoon' : 'Night')}
                                                            className={`w-6 h-6 flex items-center justify-center rounded text-[10px] font-black transition-colors ${item.time_of_day.includes(t === 'M' ? 'Morning' : t === 'A' ? 'Afternoon' : 'Night') ? 'bg-teal-600 text-white' : 'bg-slate-100 text-slate-400 hover:bg-slate-200'}`}
                                                        >
                                                            {t}
                                                        </button>
                                                    ))}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <input
                                                    type="text"
                                                    value={item.special_instruction}
                                                    onChange={e => updateItem(idx, 'special_instruction', e.target.value)}
                                                    placeholder="After food"
                                                    className="w-full bg-transparent border-0 p-0 focus:ring-0 text-xs text-slate-500"
                                                />
                                                {/* In print, show time of day as text if instructions are long */}
                                                <div className="hidden print:block text-[10px] text-slate-400 mt-0.5">
                                                    {item.time_of_day.join(' • ')}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-right print:hidden">
                                                <button onClick={() => removeItem(idx)} className="text-slate-300 hover:text-red-500 transition-colors">
                                                    <Trash2 size={16} />
                                                </button>
                                            </td>
                                        </motion.tr>
                                    ))}
                                </AnimatePresence>
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Additional Notes */}
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 print:p-0 print:border-0 print:shadow-none">
                    <div className="flex items-center gap-2 mb-4 print:hidden">
                        <FileText size={16} className="text-teal-600" />
                        <h2 className="text-sm font-black text-slate-900 uppercase tracking-widest">Additional Notes</h2>
                    </div>
                    <div className="hidden print:block mb-4 pt-4 border-t border-slate-100">
                        <p className="text-xs font-black uppercase mb-2">Instructions / Notes:</p>
                        <p className="text-xs text-slate-600 leading-relaxed min-h-[60px]">{notes || 'None provided.'}</p>
                    </div>
                    <textarea
                        value={notes}
                        onChange={e => setNotes(e.target.value)}
                        rows={3}
                        placeholder="Any special instructions or follow-up notes for the patient..."
                        className="w-full text-sm text-slate-700 placeholder-slate-200 border-0 focus:ring-0 p-0 resize-none print:hidden"
                    />
                </div>

                {/* Print Signature Section */}
                <div className="hidden print:flex justify-between items-end mt-20 pt-10 border-t border-slate-100">
                    <div className="text-[8px] text-slate-400 max-w-xs">
                        This is a computer-generated prescription. Verification code: {prescriptionId?.toUpperCase()}.
                        Generated via Clinical Sense Platform.
                    </div>
                    <div className="text-center">
                        <div className="w-48 h-px bg-slate-900 mb-2"></div>
                        <p className="text-xs font-black uppercase">Dr. {(user as any)?.full_name || 'Physician Signature'}</p>
                        <p className="text-[10px] text-slate-500">Authorized Medical Professional</p>
                    </div>
                </div>

                <div className="flex items-center gap-2 px-4 py-4 bg-teal-50 rounded-2xl print:hidden">
                    <Shield size={16} className="text-teal-600" />
                    <p className="text-xs text-teal-700 font-bold leading-tight">
                        Confirm all medications and dosages before saving. Digital prescriptions are stored securely and can be downloaded as signed PDFs for the patient.
                    </p>
                </div>
            </main>

            {/* Print specific CSS */}
            <style jsx global>{`
                @media print {
                    body {
                        background-color: white !important;
                        padding: 0 !important;
                    }
                    @page {
                        margin: 2cm;
                    }
                    .no-print {
                        display: none !important;
                    }
                }
            `}</style>
        </div>
    );
}

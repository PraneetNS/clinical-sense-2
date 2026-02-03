"use client";

import React, { useState, useEffect } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { patientsApi, clinicalApi } from '@/lib/api';
import Modal from '@/components/ui/Modal';
import PatientForm from '@/components/forms/PatientForm';
import MedicationForm from '@/components/forms/MedicationForm';
import ProcedureForm from '@/components/forms/ProcedureForm';
import DocumentForm from '@/components/forms/DocumentForm';
import TaskForm from '@/components/forms/TaskForm';
import BillingForm from '@/components/forms/BillingForm';
import AllergyForm from '@/components/forms/AllergyForm';
import AdmissionForm from '@/components/forms/AdmissionForm';
import HistoryForm from '@/components/forms/HistoryForm';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/ui/Toast';
import {
    ChevronLeft, User, Shield, AlertTriangle, Pill,
    ClipboardList, LayoutDashboard, FileText, CheckSquare,
    CreditCard, Stethoscope, AlertCircle, Clock, Plus, Edit2, Trash2, Calendar, Search, RefreshCw, TriangleAlert, Download,
    ClipboardCheck, History as HistoryIcon
} from 'lucide-react';

export default function PatientDetailPage() {
    const { id } = useParams();
    const router = useRouter();
    const searchParams = useSearchParams();
    const { user } = useAuth();
    const { showToast } = useToast();
    const [patient, setPatient] = useState<any>(null);
    const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'overview');
    const [loading, setLoading] = useState(true);
    const [tabLoading, setTabLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Modal State
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalType, setModalType] = useState<string | null>(null);
    const [editingItem, setEditingItem] = useState<any | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Data States
    const [notes, setNotes] = useState<any[]>([]);
    const [medications, setMedications] = useState<any[]>([]);
    const [procedures, setProcedures] = useState<any[]>([]);
    const [documents, setDocuments] = useState<any[]>([]);
    const [tasks, setTasks] = useState<any[]>([]);
    const [billing, setBilling] = useState<any[]>([]);
    const [admissions, setAdmissions] = useState<any[]>([]);
    const [medicalHistory, setMedicalHistory] = useState<any[]>([]);

    // Billing Date Filters
    const [billingStartDate, setBillingStartDate] = useState('');
    const [billingEndDate, setBillingEndDate] = useState('');
    const [report, setReport] = useState<any>(null);
    const [reportLoading, setReportLoading] = useState(false);
    const [timeline, setTimeline] = useState<any[]>([]);

    const isLocked = patient?.status === 'Closed' && user?.role !== 'admin';

    useEffect(() => {
        if (id) fetchData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [id]);

    const fetchData = async () => {
        try {
            setLoading(true);
            setError(null);
            const [pRes, nRes, hRes, tRes] = await Promise.all([
                patientsApi.getById(id as string),
                patientsApi.getTimeline(id as string),
                clinicalApi.getHistory(id as string),
                patientsApi.getTimeline(id as string) // Re-fetch unified timeline
            ]);
            setTimeline(tRes.data);
            setPatient(pRes.data);
            setNotes(nRes.data);
            setMedicalHistory(hRes.data);

            // Sync clinical data states from patient response
            if (pRes.data.medications) setMedications(pRes.data.medications);
            if (pRes.data.procedures) setProcedures(pRes.data.procedures);
            if (pRes.data.documents) setDocuments(pRes.data.documents);
            if (pRes.data.tasks) setTasks(pRes.data.tasks);
            if (pRes.data.billing_items) setBilling(pRes.data.billing_items);
            if (pRes.data.admissions) setAdmissions(pRes.data.admissions);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || "Failed to load patient data");
            showToast("Error loading patient details", "error");
        } finally {
            setLoading(false);
        }
    };


    // Sync with URL
    useEffect(() => {
        const tab = searchParams.get('tab');
        if (tab && tab !== activeTab) {
            setActiveTab(tab);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchParams]);

    const handleTabChange = (tab: string) => {
        setActiveTab(tab);
        const params = new URLSearchParams(searchParams.toString());
        params.set('tab', tab);
        router.push(`/patients/${id}?${params.toString()}`, { scroll: false });
    };

    // Fetch tab specific data when tab changes to avoid over-fetching on initial load
    useEffect(() => {
        if (!id) return;
        const fetchTabData = async () => {
            try {
                setTabLoading(true);
                if (activeTab === 'timeline') {
                    const res = await patientsApi.getTimeline(id as string);
                    setTimeline(res.data);
                } else if (activeTab === 'medications' && medications.length === 0) {
                    const res = await clinicalApi.getMedications(id as string);
                    setMedications(res.data);
                } else if (activeTab === 'procedures' && procedures.length === 0) {
                    const res = await clinicalApi.getProcedures(id as string);
                    setProcedures(res.data);
                } else if (activeTab === 'documents' && documents.length === 0) {
                    const res = await clinicalApi.getDocuments(id as string);
                    setDocuments(res.data);
                } else if (activeTab === 'tasks' && tasks.length === 0) {
                    const res = await clinicalApi.getTasks(id as string);
                    setTasks(res.data);
                } else if (activeTab === 'billing' && billing.length === 0) {
                    const res = await clinicalApi.getBilling(id as string);
                    setBilling(res.data);
                } else if (activeTab === 'admissions' && admissions.length === 0) {
                    const res = await clinicalApi.getAdmissions(id as string);
                    setAdmissions(res.data);
                } else if (activeTab === 'report') {
                    setReportLoading(true);
                    const res = await patientsApi.getReport(id as string);
                    setReport(res.data);
                    setReportLoading(false);
                }
            } catch (err) {
                console.error(`Failed to fetch ${activeTab} data`, err);
                showToast(`Failed to load ${activeTab}`, "error");
            } finally {
                setTabLoading(false);
            }
        };
        fetchTabData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab, id]);

    const openModal = (type: string, item: any = null) => {
        if (isLocked && type !== 'patient') { // Allow viewing but forms should be disabled
            showToast("Case is closed. Records are read-only.", "warning");
            return;
        }
        setModalType(type);
        setEditingItem(item);
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setEditingItem(null);
        setModalType(null);
    };

    const handleFormSubmit = async (data: any) => {
        if (isSubmitting) return;
        try {
            setIsSubmitting(true);
            if (modalType === 'patient') {
                const res = await patientsApi.update(id as string, data);
                setPatient(res.data);
                showToast("Patient record updated", "success");
            } else if (modalType === 'medication') {
                if (editingItem) {
                    await clinicalApi.updateMedication(editingItem.id, data);
                    showToast("Medication updated", "success");
                } else {
                    await clinicalApi.addMedication(id as string, data);
                    showToast("Medication added", "success");
                }
                const res = await clinicalApi.getMedications(id as string);
                setMedications(res.data);
            } else if (modalType === 'procedure') {
                if (editingItem) {
                    await clinicalApi.updateProcedure(editingItem.id, data);
                    showToast("Procedure updated", "success");
                } else {
                    await clinicalApi.addProcedure(id as string, data);
                    showToast("Procedure added", "success");
                }
                const res = await clinicalApi.getProcedures(id as string);
                setProcedures(res.data);
            } else if (modalType === 'document') {
                if (editingItem) {
                    await clinicalApi.updateDocument(editingItem.id, data);
                    showToast("Document updated", "success");
                } else {
                    if (data.file) {
                        const formData = new FormData();
                        formData.append('file', data.file);
                        formData.append('title', data.title);
                        if (data.summary) formData.append('summary', data.summary);
                        await clinicalApi.uploadDocument(id as string, formData);
                    } else {
                        await clinicalApi.addDocument(id as string, data);
                    }
                    showToast("Document uploaded", "success");
                }
                const res = await clinicalApi.getDocuments(id as string);
                setDocuments(res.data);
            } else if (modalType === 'task') {
                if (editingItem) {
                    await clinicalApi.updateTask(editingItem.id, data);
                    showToast("Task updated", "success");
                } else {
                    await clinicalApi.addTask(id as string, data);
                    showToast("Task assigned", "success");
                }
                const res = await clinicalApi.getTasks(id as string);
                setTasks(res.data);
            } else if (modalType === 'billing') {
                if (editingItem) {
                    await clinicalApi.updateBilling(editingItem.id, data);
                    showToast("Billing item updated", "success");
                } else {
                    await clinicalApi.addBilling(id as string, data);
                    showToast("Billing item added", "success");
                }
                const resBilling = await clinicalApi.getBilling(id as string);
                setBilling(resBilling.data);
                const resPatient = await patientsApi.getById(id as string);
                setPatient(resPatient.data);
            } else if (modalType === 'allergy') {
                if (editingItem) {
                    await clinicalApi.updateAllergy(editingItem.id, data);
                    showToast("Allergy updated", "success");
                } else {
                    await clinicalApi.addAllergy(id as string, data);
                    showToast("Allergy recorded", "success");
                }
                const resPatient = await patientsApi.getById(id as string);
                setPatient(resPatient.data);
            } else if (modalType === 'admission') {
                if (editingItem) {
                    await clinicalApi.updateAdmission(editingItem.id, data);
                    showToast("Admission record updated", "success");
                } else {
                    await clinicalApi.addAdmission(id as string, data);
                    showToast("Admission recorded", "success");
                }
                const resAdmissions = await clinicalApi.getAdmissions(id as string);
                setAdmissions(resAdmissions.data);
            } else if (modalType === 'history') {
                if (editingItem) {
                    await clinicalApi.updateHistory(editingItem.id, data);
                    showToast("Condition updated", "success");
                } else {
                    await clinicalApi.addHistory(id as string, data);
                    showToast("Condition recorded", "success");
                }
                const resHist = await clinicalApi.getHistory(id as string);
                setMedicalHistory(resHist.data);
            }

            // Refresh timeline on any change
            const resTimeline = await patientsApi.getTimeline(id as string);
            setTimeline(resTimeline.data);
        } catch (err: any) {
            console.error("Failed to submit form", err);
            showToast(err.response?.data?.detail || "Action failed", "error");
        } finally {
            setIsSubmitting(false);
            closeModal();
        }
    };

    const handleDelete = async (type: string, itemId: number) => {
        if (isLocked) {
            showToast("Cannot delete records in a closed case.", "error");
            return;
        }
        if (!confirm(`Are you sure you want to delete this ${type}?`)) return;
        try {
            if (type === 'medication') {
                await clinicalApi.deleteMedication(itemId);
                setMedications(medications.filter(m => m.id !== itemId));
            } else if (type === 'procedure') {
                await clinicalApi.deleteProcedure(itemId);
                setProcedures(procedures.filter(p => p.id !== itemId));
            } else if (type === 'document') {
                await clinicalApi.deleteDocument(itemId);
                setDocuments(documents.filter(d => d.id !== itemId));
            } else if (type === 'task') {
                await clinicalApi.deleteTask(itemId);
                setTasks(tasks.filter(t => t.id !== itemId));
            } else if (type === 'billing') {
                await clinicalApi.deleteBilling(itemId);
                setBilling(billing.filter(b => b.id !== itemId));
            } else if (type === 'allergy') {
                await clinicalApi.deleteAllergy(itemId);
                setPatient({ ...patient, allergies: patient.allergies.filter((a: any) => a.id !== itemId) });
            } else if (type === 'history') {
                await clinicalApi.deleteHistory(itemId);
                setMedicalHistory(medicalHistory.filter(h => h.id !== itemId));
            } else if (type === 'admission') {
                await clinicalApi.deleteAdmission(itemId);
                setAdmissions(admissions.filter(a => a.id !== itemId));
            }

            // Refresh patient for totals
            const pRes = await patientsApi.getById(id as string);
            setPatient(pRes.data);

            showToast("Record deleted", "success");
        } catch (err: any) {
            console.error("Failed to delete", err);
            showToast(err.response?.data?.detail || "Delete failed", "error");
        }
    };

    const handleDownloadReport = async () => {
        try {
            showToast("Generating PDF report...", "info");
            const response = await patientsApi.downloadReportPdf(id as string);

            // Create a blob from the response data
            const blob = new Blob([response.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);

            // Create a temporary link and trigger download
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `patient_report_${patient?.mrn || id}.pdf`);
            document.body.appendChild(link);
            link.click();

            // Cleanup
            link.remove();
            window.URL.revokeObjectURL(url);

            showToast("Report downloaded successfully", "success");
        } catch (err: any) {
            console.error("PDF download failed", err);
            showToast("Failed to download PDF report", "error");
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-screen bg-slate-50 gap-4">
                <div className="relative">
                    <div className="animate-spin rounded-full h-16 w-16 border-4 border-slate-200 border-t-teal-600"></div>
                </div>
                <p className="text-slate-500 font-bold animate-pulse uppercase tracking-[0.2em] text-[10px]">Retrieving Clinical Records...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center h-screen bg-slate-50 gap-6 px-8 text-center max-w-md mx-auto">
                <div className="w-16 h-16 bg-red-50 text-red-600 rounded-full flex items-center justify-center shadow-sm">
                    <TriangleAlert size={32} />
                </div>
                <div className="space-y-2">
                    <h2 className="text-xl font-bold text-slate-900">System Error</h2>
                    <p className="text-slate-500 text-sm leading-relaxed">{error}</p>
                </div>
                <button
                    onClick={() => fetchData()}
                    className="flex items-center gap-2 px-6 py-3 bg-slate-900 text-white font-bold rounded-xl hover:bg-slate-800 transition shadow-lg"
                >
                    <RefreshCw size={18} /> Retry Connection
                </button>
            </div>
        );
    }

    if (!patient) return null;

    const EmptyState = ({ icon: Icon, title, description, actionText, onAction }: any) => (
        <div className="flex flex-col items-center justify-center py-20 bg-white rounded-3xl border border-dashed border-slate-200">
            <div className="bg-slate-50 w-16 h-16 rounded-full flex items-center justify-center mb-4 border border-slate-100 shadow-inner">
                <Icon className="text-slate-300" size={32} />
            </div>
            <h3 className="text-lg font-bold text-slate-900">{title}</h3>
            <p className="text-slate-500 text-sm max-w-xs mx-auto text-center mt-2 leading-relaxed">
                {description}
            </p>
            {actionText && (
                <button
                    onClick={onAction}
                    className="mt-6 flex items-center gap-2 text-teal-600 font-bold hover:text-teal-700 transition-colors"
                >
                    <Plus size={18} /> {actionText}
                </button>
            )}
        </div>
    );

    const tabs = [
        { id: 'overview', label: 'Overview', icon: User },
        { id: 'timeline', label: 'Timeline', icon: Clock },
        { id: 'notes', label: 'Notes', icon: FileText },
        { id: 'medications', label: 'Medications', icon: Pill },
        { id: 'procedures', label: 'Procedures', icon: Stethoscope },
        { id: 'documents', label: 'Documents', icon: ClipboardList },
        { id: 'tasks', label: 'Tasks', icon: CheckSquare },
        { id: 'billing', label: 'Billing', icon: CreditCard },
        { id: 'admissions', label: 'Admissions', icon: Clock },
        { id: 'report', label: 'Final Report', icon: ClipboardCheck },
    ];

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col">
            {/* Header */}
            <nav className="bg-white border-b border-slate-200 px-8 py-4 flex items-center gap-6 sticky top-0 z-20 shadow-sm">
                <Link href="/patients" className="text-slate-500 hover:text-teal-600 transition-colors">
                    <ChevronLeft size={24} />
                </Link>
                <div>
                    <h1 className="text-xl font-bold text-slate-900">{patient.name}</h1>
                    <div className="flex gap-2 text-xs text-slate-500 uppercase tracking-widest mt-1">
                        <span>{patient.mrn}</span>
                        <span>•</span>
                        <span>{patient.gender || 'Unknown'}</span>
                        <span>•</span>
                        <span>{new Date(patient.date_of_birth).getFullYear() > 1900 ? new Date().getFullYear() - new Date(patient.date_of_birth).getFullYear() : 'N/A'} yo</span>
                    </div>
                </div>
                <div className="ml-auto flex gap-3">
                    <Link
                        href={`/notes/new?patientId=${patient.id}`} // Assuming we pass patientId via query param
                        className="bg-teal-600 text-white px-4 py-2 rounded-lg font-bold hover:bg-teal-700 transition-colors shadow-sm text-sm flex items-center gap-2"
                    >
                        + New Clinical Note
                    </Link>
                </div>
            </nav>

            <main className="flex-1 p-8 max-w-7xl mx-auto w-full">
                {/* Tabs Navigation */}
                <div className="flex overflow-x-auto gap-1 bg-white p-1 rounded-xl shadow-sm border border-slate-100 mb-8 sticky top-[88px] z-10 mx-auto w-fit">
                    {tabs.map((tab) => {
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => handleTabChange(tab.id)}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all whitespace-nowrap ${activeTab === tab.id
                                    ? 'bg-teal-50 text-teal-700 shadow-sm ring-1 ring-teal-200'
                                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                                    }`}
                            >
                                <Icon size={16} />
                                {tab.label}
                            </button>
                        );
                    })}
                </div>

                {/* PATIENT SNAPSHOT (Phase 2) */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 flex flex-col justify-center">
                        <span className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Current Status</span>
                        <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${patient.status === 'Active' ? 'bg-green-500 animate-pulse' : 'bg-slate-400'}`}></div>
                            <span className="font-bold text-slate-900">{patient.status || 'Active'}</span>
                            <button
                                onClick={async () => {
                                    const nextStatus = patient.status === 'Active' ? 'Closed' : 'Active';
                                    if (confirm(`Change case status to ${nextStatus}?`)) {
                                        const res = await patientsApi.toggleStatus(id as string, nextStatus);
                                        setPatient(res.data);
                                        showToast(`Case ${nextStatus.toLowerCase()} successfully`, "success");
                                    }
                                }}
                                className="ml-auto text-[10px] font-bold text-teal-600 hover:underline"
                            >
                                {patient.status === 'Active' ? 'Close Case' : 'Reactivate'}
                            </button>
                        </div>
                    </div>
                    <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100">
                        <span className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Active Problems</span>
                        <div className="font-bold text-slate-900 truncate">
                            {medicalHistory.filter(h => h.status === 'Active').length > 0
                                ? medicalHistory.filter(h => h.status === 'Active').map(h => h.condition_name).join(', ')
                                : 'None Documented'}
                        </div>
                    </div>
                    <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100">
                        <span className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Active Medications</span>
                        <div className="font-bold text-slate-900 truncate">
                            {medications.filter(m => m.status === 'Active').length > 0
                                ? medications.filter(m => m.status === 'Active').map(m => m.name).join(', ')
                                : 'None Documented'}
                        </div>
                    </div>
                    <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100">
                        <span className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Primary Insurance</span>
                        <div className="font-bold text-slate-900 truncate">
                            {patient.insurance_provider || 'Not Recorded'}
                        </div>
                    </div>
                </div>

                {
                    patient.status === 'Closed' && (
                        <div className="bg-amber-50 border border-amber-200 p-4 rounded-2xl mb-8 flex items-center gap-4 text-amber-800">
                            <AlertCircle className="shrink-0" />
                            <div>
                                <p className="font-bold text-sm">This case is CLOSED</p>
                                <p className="text-xs opacity-80">All records are currently read-only. Reactivate the case to make changes.</p>
                            </div>
                        </div>
                    )
                }

                <div className="min-h-[500px]">
                    {/* OVERVIEW TAB */}
                    {activeTab === 'overview' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {/* Demographics */}
                            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 col-span-2">
                                <div className="flex justify-between items-center mb-6">
                                    <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                                        <User size={20} className="text-teal-600" /> Demographics
                                    </h3>
                                    <div className="flex items-center gap-4">
                                        {patient.updated_at && (
                                            <span className="text-xs text-slate-400 font-medium">
                                                Last updated: {new Date(patient.updated_at).toLocaleString()}
                                            </span>
                                        )}
                                        <button onClick={() => openModal('patient', patient)} className="text-slate-400 hover:text-teal-600 transition-colors">
                                            <Edit2 size={16} />
                                        </button>
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-y-6 gap-x-12">
                                    <div>
                                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Full Name</label>
                                        <div className="text-slate-800 font-medium">{patient.name}</div>
                                    </div>
                                    <div>
                                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">MRN (Identifier)</label>
                                        <div className="text-slate-800 font-medium font-mono">{patient.mrn}</div>
                                    </div>
                                    <div>
                                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Date of Birth</label>
                                        <div className="text-slate-800 font-medium">{new Date(patient.date_of_birth).toLocaleDateString()}</div>
                                    </div>
                                    <div>
                                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Gender</label>
                                        <div className="text-slate-800 font-medium">{patient.gender || 'Not Recorded'}</div>
                                    </div>
                                    <div>
                                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Address</label>
                                        <div className="text-slate-800 font-medium">{patient.address || 'Not Recorded'}</div>
                                    </div>
                                    <div>
                                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Primary Phone</label>
                                        <div className="text-slate-800 font-medium">{patient.phone_number || 'Not Recorded'}</div>
                                    </div>
                                </div>

                                <div className="mt-8 pt-8 border-t border-slate-100">
                                    <h4 className="text-sm font-bold text-slate-900 mb-4 uppercase tracking-wider flex items-center gap-2">
                                        <Shield size={16} className="text-teal-600" /> Emergency Contact
                                    </h4>
                                    <div className="grid grid-cols-3 gap-4">
                                        <div>
                                            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Name</label>
                                            <div className="text-slate-800 font-medium">{patient.emergency_contact_name || '-'}</div>
                                        </div>
                                        <div>
                                            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Relation</label>
                                            <div className="text-slate-800 font-medium">{patient.emergency_contact_relation || '-'}</div>
                                        </div>
                                        <div>
                                            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Phone</label>
                                            <div className="text-slate-800 font-medium">{patient.emergency_contact_phone || '-'}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Allergies & Alerts */}
                            <div className="bg-white p-8 rounded-[2.5rem] shadow-xl border border-slate-100 h-fit">
                                <div className="flex justify-between items-center mb-6">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 bg-red-50 text-red-600 rounded-xl flex items-center justify-center">
                                            <AlertTriangle size={20} />
                                        </div>
                                        <h3 className="text-xl font-black text-slate-900">Critical Alerts</h3>
                                    </div>
                                    <button onClick={() => openModal('allergy')} className="w-8 h-8 flex items-center justify-center bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition shadow-lg shadow-slate-900/10">
                                        <Plus size={16} />
                                    </button>
                                </div>
                                {(!patient.allergies || patient.allergies.length === 0) ? (
                                    <div className="py-12 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-200">
                                        <p className="text-slate-400 font-bold italic text-sm">No clinical allergies documented.</p>
                                    </div>
                                ) : (
                                    <ul className="space-y-4">
                                        {patient.allergies.map((alg: any, i: number) => (
                                            <li key={i} className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex justify-between items-start group hover:border-red-200 transition-colors">
                                                <div className="flex items-start gap-3">
                                                    <div className={`w-1.5 h-10 rounded-full mt-1 ${alg.severity === 'High' ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.4)]' : 'bg-orange-400 shadow-[0_0_8px_rgba(251,146,60,0.4)]'}`}></div>
                                                    <div>
                                                        <div className="font-black text-slate-900 text-base">{alg.allergen}</div>
                                                        <div className="text-[10px] font-black uppercase tracking-widest text-slate-400 mt-0.5">
                                                            {alg.severity} Severity • {alg.reaction}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <button onClick={() => openModal('allergy', alg)} className="p-2 text-slate-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"><Edit2 size={14} /></button>
                                                    <button onClick={() => handleDelete('allergy', alg.id)} className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"><Trash2 size={14} /></button>
                                                </div>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>

                            {/* Past Medical History */}
                            <div className="bg-white p-8 rounded-[2.5rem] shadow-xl border border-slate-100 h-fit lg:col-span-2">
                                <div className="flex justify-between items-center mb-6">
                                    <h3 className="text-xl font-black text-slate-900 flex items-center gap-3">
                                        <HistoryIcon size={20} className="text-blue-500" /> Past Medical History
                                    </h3>
                                    <button onClick={() => openModal('history')} className="flex items-center gap-2 px-4 py-2 bg-slate-50 text-slate-600 font-bold rounded-xl hover:bg-slate-100 transition">
                                        <Plus size={16} /> Add Condition
                                    </button>
                                </div>
                                {medicalHistory.length === 0 ? (
                                    <div className="py-8 text-center text-slate-400 font-medium italic">
                                        No historical medical conditions recorded.
                                    </div>
                                ) : (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {medicalHistory.map((h, i) => (
                                            <div key={i} className="p-4 bg-slate-50/50 rounded-2xl border border-slate-100 hover:border-blue-200 transition-colors group relative">
                                                <div className="flex justify-between items-start">
                                                    <div>
                                                        <div className="font-black text-slate-900">{h.condition_name}</div>
                                                        <div className="text-xs text-slate-500 mt-1">
                                                            {h.diagnosis_date ? `Diagnosed: ${new Date(h.diagnosis_date).toLocaleDateString()}` : 'Date Unknown'}
                                                        </div>
                                                    </div>
                                                    <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${h.status === 'Active' ? 'bg-orange-50 text-orange-600' : 'bg-slate-100 text-slate-500'}`}>
                                                        {h.status}
                                                    </span>
                                                </div>
                                                <div className="flex gap-1 absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-white/80 p-1 rounded-lg">
                                                    <button onClick={() => openModal('history', h)} className="p-1 text-slate-400 hover:text-teal-600"><Edit2 size={14} /></button>
                                                    <button onClick={() => handleDelete('history', h.id)} className="p-1 text-slate-400 hover:text-red-600"><Trash2 size={14} /></button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* NOTES TAB */}
                    {activeTab === 'notes' && (
                        <div className="space-y-8 max-w-4xl mx-auto">
                            <div className="flex justify-between items-center bg-white p-6 rounded-3xl border border-slate-100 shadow-sm">
                                <div>
                                    <h2 className="text-xl font-black text-slate-900">Clinical Narrative</h2>
                                    <p className="text-xs text-slate-500 uppercase font-black tracking-[0.2em] mt-1">Provider Documentation Timeline</p>
                                </div>
                                <button
                                    onClick={() => openModal('note')}
                                    className="flex items-center gap-2 px-6 py-3 bg-slate-900 text-white font-black rounded-xl hover:bg-slate-800 shadow-xl shadow-slate-900/20 transition-all hover:-translate-y-0.5"
                                >
                                    <Plus size={18} /> Compose New Note
                                </button>
                            </div>

                            {notes.length === 0 ? (
                                <EmptyState
                                    icon={FileText}
                                    title="A quiet timeline"
                                    description="No clinical notes have been recorded for this patient yet."
                                    actionText="Create First Note"
                                    onAction={() => openModal('note')}
                                />
                            ) : (
                                <div className="relative pl-12 border-l-4 border-slate-200/50 ml-6 space-y-8">
                                    {notes.map((note) => (
                                        <div key={note.id} className="relative">
                                            <div className="absolute -left-[41px] top-6 w-5 h-5 rounded-full bg-white border-4 border-teal-500"></div>

                                            <Link href={`/notes/${note.id}`} className="block group">
                                                <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-all">
                                                    <div className="flex justify-between items-start mb-3">
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-xs font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2.5 py-1 rounded-md border border-teal-100">
                                                                {note.note_type}
                                                            </span>
                                                            {note.structured_content && (
                                                                <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2 py-1 rounded border border-indigo-100 flex items-center gap-1">
                                                                    <Clock size={10} /> AI Structured
                                                                </span>
                                                            )}
                                                        </div>
                                                        <span className="text-xs text-slate-400 font-medium">{new Date(note.created_at).toLocaleString()}</span>
                                                    </div>

                                                    <h4 className="text-lg font-bold text-slate-900 group-hover:text-teal-600 transition-colors mb-2">{note.title}</h4>
                                                    <p className="text-slate-500 text-sm line-clamp-3 leading-relaxed">
                                                        {note.raw_content}
                                                    </p>
                                                </div>
                                            </Link>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* MEDICATIONS TAB */}
                    {activeTab === 'medications' && (
                        <div className="space-y-6">
                            <div className="flex justify-between items-center bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                                <div>
                                    <h2 className="text-xl font-bold text-slate-900">Current Medications</h2>
                                    <p className="text-xs text-slate-500 uppercase font-bold tracking-widest mt-1">Pharmacological History</p>
                                </div>
                                <button
                                    onClick={() => openModal('medication')}
                                    className="flex items-center gap-2 px-6 py-3 bg-slate-900 text-white font-bold rounded-xl hover:bg-slate-800 shadow-lg shadow-slate-900/20 transition-all hover:-translate-y-0.5"
                                >
                                    <Plus size={18} /> New Prescription
                                </button>
                            </div>

                            {medications.length === 0 ? (
                                <EmptyState
                                    icon={Pill}
                                    title="No medications found"
                                    description="There are no active or past medications recorded for this patient."
                                    actionText="Add Medication"
                                    onAction={() => openModal('medication')}
                                />
                            ) : (
                                <div className="bg-white rounded-3xl shadow-xl border border-slate-100 overflow-hidden">
                                    <table className="w-full text-sm text-left">
                                        <thead className="bg-slate-50 text-slate-500 uppercase font-black text-[10px] tracking-wider">
                                            <tr>
                                                <th className="px-8 py-5">Medication</th>
                                                <th className="px-6 py-5">Dosage</th>
                                                <th className="px-6 py-5">Frequency</th>
                                                <th className="px-6 py-5">Status</th>
                                                <th className="px-6 py-5 text-right">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-100">
                                            {medications.map((med, i) => (
                                                <tr key={i} className="hover:bg-slate-50/50 transition-colors group">
                                                    <td className="px-8 py-5">
                                                        <div className="flex items-center gap-3">
                                                            <div className="w-10 h-10 bg-teal-50 rounded-xl flex items-center justify-center text-teal-600 border border-teal-100">
                                                                <Pill size={18} />
                                                            </div>
                                                            <div className="font-black text-slate-900 text-base">{med.name}</div>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-5 font-bold text-slate-700">{med.dosage || '-'}</td>
                                                    <td className="px-6 py-5 text-slate-600">{med.frequency || '-'}</td>
                                                    <td className="px-6 py-5">
                                                        <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-tighter ${med.status === 'Active' ? 'bg-green-100 text-green-700 border border-green-200' : 'bg-slate-100 text-slate-500 border border-slate-200'}`}>
                                                            {med.status}
                                                        </span>
                                                    </td>
                                                    <td className="px-8 py-5 text-right">
                                                        <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                            <button onClick={() => openModal('medication', med)} className="p-2 text-slate-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"><Edit2 size={16} /></button>
                                                            <button onClick={() => handleDelete('medication', med.id)} className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"><Trash2 size={16} /></button>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    )}

                    {/* PROCEDURES TAB */}
                    {activeTab === 'procedures' && (
                        <div className="space-y-6">
                            <div className="flex justify-between items-center bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                                <div>
                                    <h2 className="text-xl font-bold text-slate-900">Surgical & Clinical Procedures</h2>
                                    <p className="text-xs text-slate-500 uppercase font-bold tracking-widest mt-1">Intervention History</p>
                                </div>
                                <button
                                    onClick={() => openModal('procedure')}
                                    className="flex items-center gap-2 px-6 py-3 bg-slate-900 text-white font-bold rounded-xl hover:bg-slate-800 shadow-lg shadow-slate-900/20 transition-all hover:-translate-y-0.5"
                                >
                                    <Plus size={18} /> Record Procedure
                                </button>
                            </div>

                            {procedures.length === 0 ? (
                                <EmptyState
                                    icon={Stethoscope}
                                    title="No procedures recorded"
                                    description="No surgical or diagnostic procedures have been logged for this patient."
                                    actionText="Add Procedure"
                                    onAction={() => openModal('procedure')}
                                />
                            ) : (
                                <div className="bg-white rounded-3xl shadow-xl border border-slate-100 overflow-hidden">
                                    <table className="w-full text-sm text-left">
                                        <thead className="bg-slate-50 text-slate-500 uppercase font-black text-[10px] tracking-wider">
                                            <tr>
                                                <th className="px-8 py-5">Procedure</th>
                                                <th className="px-6 py-5">Code</th>
                                                <th className="px-6 py-5">Date</th>
                                                <th className="px-8 py-5 text-right">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-100">
                                            {procedures.map((proc, i) => (
                                                <tr key={i} className="hover:bg-slate-50/50 transition-colors group">
                                                    <td className="px-8 py-5">
                                                        <div className="flex items-center gap-3">
                                                            <div className="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center text-indigo-600 border border-indigo-100">
                                                                <Stethoscope size={18} />
                                                            </div>
                                                            <div>
                                                                <div className="font-black text-slate-900 text-base">{proc.name}</div>
                                                                <div className="text-xs text-slate-500 font-medium max-w-xs truncate">{proc.notes}</div>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-5">
                                                        <span className="font-mono text-[10px] font-black bg-slate-100 px-2 py-1 rounded text-slate-600 border border-slate-200">
                                                            {proc.code || 'N/A'}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-5 font-bold text-slate-600">{new Date(proc.date).toLocaleDateString()}</td>
                                                    <td className="px-8 py-5 text-right">
                                                        <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                            <button onClick={() => openModal('procedure', proc)} className="p-2 text-slate-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"><Edit2 size={16} /></button>
                                                            <button onClick={() => handleDelete('procedure', proc.id)} className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"><Trash2 size={16} /></button>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    )}

                    {/* DOCUMENTS TAB */}
                    {activeTab === 'documents' && (
                        <div className="space-y-6">
                            <div className="flex justify-between items-center bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                                <div>
                                    <h2 className="text-xl font-bold text-slate-900">Patient Documentation</h2>
                                    <p className="text-xs text-slate-500 uppercase font-bold tracking-widest mt-1">Uploaded Files & Diagnostic Reports</p>
                                </div>
                                <button
                                    onClick={() => openModal('document')}
                                    className="flex items-center gap-2 px-6 py-3 bg-slate-900 text-white font-bold rounded-xl hover:bg-slate-800 shadow-lg shadow-slate-900/20 transition-all hover:-translate-y-0.5"
                                >
                                    <Plus size={18} /> Upload New File
                                </button>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {documents.length === 0 ? (
                                    <div className="col-span-full">
                                        <EmptyState
                                            icon={ClipboardList}
                                            title="Vault is empty"
                                            description="No external documents or scans have been uploaded for this patient yet."
                                            actionText="Upload Document"
                                            onAction={() => openModal('document')}
                                        />
                                    </div>
                                ) : (
                                    documents.map((doc, i) => (
                                        <div key={i} className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 hover:shadow-xl transition-all group relative border-t-4 border-t-teal-500">
                                            <div className="absolute top-6 right-6 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button onClick={() => openModal('document', doc)} className="p-2 text-slate-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"><Edit2 size={16} /></button>
                                                <button onClick={() => handleDelete('document', doc.id)} className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"><Trash2 size={16} /></button>
                                            </div>

                                            <div className="flex flex-col h-full">
                                                <div className="w-12 h-12 bg-teal-50 text-teal-600 rounded-2xl flex items-center justify-center mb-4">
                                                    <FileText size={24} />
                                                </div>

                                                <h4 className="font-black text-slate-900 text-lg line-clamp-1 mb-1">{doc.title}</h4>
                                                <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">
                                                    {doc.file_type || 'PDF Document'} • {new Date(doc.created_at).toLocaleDateString()}
                                                </div>

                                                {doc.summary && (
                                                    <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 mb-6 flex-1">
                                                        <p className="text-slate-600 text-xs leading-relaxed line-clamp-3 italic">
                                                            &quot;{doc.summary}&quot;
                                                        </p>
                                                    </div>
                                                )}

                                                <a
                                                    href={doc.file_url.startsWith('http') ? doc.file_url : (process.env.NEXT_PUBLIC_API_URL || '').replace('/api/v1', '') + doc.file_url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="w-full py-3 bg-slate-900 text-white rounded-xl font-bold text-center text-sm hover:bg-slate-800 transition-colors shadow-lg shadow-slate-900/10"
                                                >
                                                    View Document
                                                </a>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    )}

                    {/* TASKS TAB */}
                    {activeTab === 'tasks' && (
                        <div className="space-y-6">
                            <div className="flex justify-between items-center bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                                <div>
                                    <h2 className="text-xl font-bold text-slate-900">Clinical Workflow Tasks</h2>
                                    <p className="text-xs text-slate-500 uppercase font-bold tracking-widest mt-1">Care Coordination & Follow-ups</p>
                                </div>
                                <button
                                    onClick={() => openModal('task')}
                                    className="flex items-center gap-2 px-6 py-3 bg-slate-900 text-white font-bold rounded-xl hover:bg-slate-800 shadow-lg shadow-slate-900/20 transition-all hover:-translate-y-0.5"
                                >
                                    <Plus size={18} /> New Task
                                </button>
                            </div>

                            {tasks.length === 0 ? (
                                <EmptyState
                                    icon={CheckSquare}
                                    title="All tasks completed"
                                    description="No pending care tasks or follow-ups for this patient."
                                    actionText="Create Task"
                                    onAction={() => openModal('task')}
                                />
                            ) : (
                                <div className="space-y-4">
                                    {tasks.sort((a, b) => (a.status === 'Completed' ? 1 : -1)).map((task, i) => (
                                        <div key={i} className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 flex items-center gap-6 group hover:shadow-md transition-shadow">
                                            <div className={`w-1.5 h-12 rounded-full ${task.status === 'Completed' ? 'bg-slate-200' : 'bg-teal-500 shadow-[0_0_12px_rgba(20,184,166,0.4)]'}`}></div>
                                            <div className="flex-1">
                                                <h4 className={`text-lg font-black ${task.status === 'Completed' ? 'text-slate-400 line-through' : 'text-slate-900'}`}>{task.description}</h4>
                                                <div className="flex items-center gap-3 mt-1">
                                                    <span className={`text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded border ${task.status === 'Completed' ? 'bg-slate-50 text-slate-400 border-slate-100' : 'bg-teal-50 text-teal-600 border-teal-100'}`}>
                                                        {task.status}
                                                    </span>
                                                    <p className="text-[11px] text-slate-400 font-bold uppercase tracking-tighter">Due: {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'Pending'}</p>
                                                </div>
                                            </div>
                                            <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button onClick={() => openModal('task', task)} className="p-2 text-slate-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"><Edit2 size={16} /></button>
                                                <button onClick={() => handleDelete('task', task.id)} className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"><Trash2 size={16} /></button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* BILLING TAB */}
                    {activeTab === 'billing' && (
                        <div className="space-y-6">
                            <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 bg-white p-8 rounded-[2.5rem] shadow-xl border border-slate-100 relative overflow-hidden">
                                <div className="absolute top-0 right-0 w-64 h-64 bg-teal-50/50 rounded-full -mr-32 -mt-32 blur-3xl -z-10"></div>

                                <div className="flex flex-wrap items-center gap-6">
                                    <div className="space-y-1.5">
                                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Service Start</label>
                                        <div className="flex items-center gap-3 px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl focus-within:ring-2 focus-within:ring-teal-500 transition-all">
                                            <Calendar size={18} className="text-slate-400" />
                                            <input
                                                type="date"
                                                value={billingStartDate}
                                                onChange={(e) => setBillingStartDate(e.target.value)}
                                                className="bg-transparent border-none text-slate-700 font-bold outline-none text-sm"
                                            />
                                        </div>
                                    </div>
                                    <div className="mt-6 font-black text-slate-300">→</div>
                                    <div className="space-y-1.5">
                                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Service End</label>
                                        <div className="flex items-center gap-3 px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl focus-within:ring-2 focus-within:ring-teal-500 transition-all">
                                            <input
                                                type="date"
                                                value={billingEndDate}
                                                onChange={(e) => setBillingEndDate(e.target.value)}
                                                className="bg-transparent border-none text-slate-700 font-bold outline-none text-sm"
                                            />
                                        </div>
                                    </div>
                                    {(billingStartDate || billingEndDate) && (
                                        <button
                                            onClick={() => { setBillingStartDate(''); setBillingEndDate(''); }}
                                            className="mt-6 w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center text-slate-500 hover:bg-slate-200 transition-colors"
                                        >
                                            <RefreshCw size={18} />
                                        </button>
                                    )}
                                </div>

                                <div className="flex items-center gap-8 w-full lg:w-auto pt-6 lg:pt-0 border-t lg:border-t-0 border-slate-100">
                                    <div className="text-right">
                                        <p className="text-[10px] text-slate-400 uppercase tracking-[0.2em] font-black mb-1">Total Outstanding</p>
                                        <p className="text-4xl font-black text-slate-900 tracking-tighter">
                                            <span className="text-teal-600 mr-1">$</span>
                                            {patient.outstanding_billing_amount?.toLocaleString(undefined, { minimumFractionDigits: 2 }) || '0.00'}
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => openModal('billing')}
                                        className="flex items-center gap-2 px-8 py-4 bg-slate-900 text-white font-black rounded-2xl hover:bg-slate-800 shadow-2xl shadow-slate-900/20 transition-all hover:-translate-y-1 active:scale-95"
                                    >
                                        <Plus size={20} /> Add Item
                                    </button>
                                </div>
                            </div>

                            <div className="bg-white rounded-[2.5rem] shadow-xl border border-slate-100 overflow-hidden mt-8">
                                <table className="w-full text-sm text-left">
                                    <thead className="bg-slate-50/50 text-slate-400 uppercase font-black text-[10px] tracking-widest">
                                        <tr>
                                            <th className="px-8 py-6">Service Date</th>
                                            <th className="px-6 py-6">Description</th>
                                            <th className="px-6 py-6">Code</th>
                                            <th className="px-6 py-6 text-right">Cost</th>
                                            <th className="px-8 py-6 text-center">Status</th>
                                            <th className="px-8 py-6 text-right">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {billing.filter(item => {
                                            const date = new Date(item.created_at).toISOString().split('T')[0];
                                            if (billingStartDate && date < billingStartDate) return false;
                                            if (billingEndDate && date > billingEndDate) return false;
                                            return true;
                                        }).length === 0 ? (
                                            <tr>
                                                <td colSpan={user?.role === 'doctor' ? 5 : 6} className="px-8 py-20 text-center">
                                                    <div className="flex flex-col items-center gap-3">
                                                        <CreditCard className="text-slate-200" size={48} />
                                                        <p className="text-slate-400 font-bold italic">No financial records matching your criteria.</p>
                                                    </div>
                                                </td>
                                            </tr>
                                        ) : (
                                            billing
                                                .filter(item => {
                                                    const date = new Date(item.created_at).toISOString().split('T')[0];
                                                    if (billingStartDate && date < billingStartDate) return false;
                                                    if (billingEndDate && date > billingEndDate) return false;
                                                    return true;
                                                })
                                                .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                                                .map((item, i) => (
                                                    <tr key={i} className="hover:bg-slate-50/50 transition-colors group">
                                                        <td className="px-8 py-6 text-slate-500 font-bold whitespace-nowrap">
                                                            {new Date(item.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                                                        </td>
                                                        <td className="px-6 py-6 font-black text-slate-900 text-lg">{item.item_name}</td>
                                                        <td className="px-6 py-6">
                                                            <span className="font-mono text-[10px] font-black bg-slate-100 px-2 py-1 rounded text-slate-500 border border-slate-200">
                                                                {item.code || '-'}
                                                            </span>
                                                        </td>
                                                        <td className="px-6 py-6 text-right font-black text-slate-900 text-lg">${(item.cost || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                                                        <td className="px-8 py-6 text-center">
                                                            <span className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest ${item.status === 'Paid' ? 'bg-green-100 text-green-700 shadow-sm border border-green-200'
                                                                : item.status === 'Pending' ? 'bg-orange-100 text-orange-700 shadow-sm border border-orange-200'
                                                                    : 'bg-slate-100 text-slate-500 border border-slate-200'
                                                                }`}>
                                                                {item.status}
                                                            </span>
                                                        </td>
                                                        <td className="px-8 py-6 text-right">
                                                            <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                <button onClick={() => openModal('billing', item)} className="p-2 text-slate-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"><Edit2 size={16} /></button>
                                                                <button onClick={() => handleDelete('billing', item.id)} className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"><Trash2 size={16} /></button>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* ADMISSIONS TAB */}
                    {activeTab === 'admissions' && (
                        <div className="space-y-6">
                            <div className="flex justify-between items-center bg-white p-8 rounded-3xl shadow-sm border border-slate-100">
                                <div>
                                    <h3 className="text-2xl font-black text-slate-900">Hospital Stays</h3>
                                    <p className="text-slate-500 font-medium tracking-tight">Timeline of inpatient and observational admissions.</p>
                                </div>
                                <button
                                    onClick={() => openModal('admission')}
                                    className="px-6 py-3 bg-slate-900 text-white font-black rounded-2xl hover:bg-slate-800 transition-all flex items-center gap-2"
                                >
                                    <Plus size={20} /> Record Stay
                                </button>
                            </div>

                            {admissions.length === 0 ? (
                                <EmptyState
                                    icon={Clock}
                                    title="No hospitalizations recorded"
                                    description="This patient has no historical or active inpatient admissions in the system."
                                    actionText="Record Admission"
                                    onAction={() => openModal('admission')}
                                />
                            ) : (
                                <div className="grid grid-cols-1 gap-6">
                                    {admissions.sort((a, b) => new Date(b.admission_date).getTime() - new Date(a.admission_date).getTime()).map((stay, i) => (
                                        <div key={i} className="bg-white p-8 rounded-[2rem] border border-slate-100 shadow-sm hover:shadow-md transition-all group">
                                            <div className="flex justify-between items-start mb-6">
                                                <div className="flex gap-4 items-center">
                                                    <div className="w-14 h-14 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center font-black text-xl">
                                                        {new Date(stay.admission_date).getDate()}
                                                    </div>
                                                    <div>
                                                        <h4 className="text-xl font-black text-slate-900">{stay.reason}</h4>
                                                        <p className="text-slate-500 font-bold text-sm">
                                                            {new Date(stay.admission_date).toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' })}
                                                            {stay.discharge_date ? ` — ${new Date(stay.discharge_date).toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' })}` : ' (Current)'}
                                                        </p>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <span className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest ${stay.status === 'Discharged' ? 'bg-green-50 text-green-700 border border-green-100' : 'bg-blue-50 text-blue-700 border border-blue-100 shadow-[0_0_12px_rgba(59,130,246,0.2)]'
                                                        }`}>
                                                        {stay.status}
                                                    </span>
                                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-4">
                                                        <button onClick={() => openModal('admission', stay)} className="p-2 text-slate-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"><Edit2 size={16} /></button>
                                                        <button onClick={() => handleDelete('admission', stay.id)} className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"><Trash2 size={16} /></button>
                                                    </div>
                                                </div>
                                            </div>
                                            {stay.notes && (
                                                <div className="pl-6 border-l-4 border-slate-50 p-4 bg-slate-50/50 rounded-2xl text-slate-600 text-sm leading-relaxed whitespace-pre-wrap italic">
                                                    &quot;{stay.notes}&quot;
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* REPORT TAB */}
                    {activeTab === 'report' && (
                        <div className="space-y-8 max-w-5xl mx-auto">
                            <div className="flex justify-between items-center bg-white p-8 rounded-3xl border border-slate-100 shadow-sm">
                                <div>
                                    <h2 className="text-2xl font-black text-slate-900">Final Patient Summary</h2>
                                    <p className="text-xs text-slate-500 uppercase font-bold tracking-[0.2em] mt-2">Aggregated Clinical Documentation Report</p>
                                </div>
                                <div className="flex gap-4">
                                    <button
                                        onClick={() => handleTabChange('report')}
                                        className="flex items-center gap-2 px-6 py-3 bg-slate-100 text-slate-600 font-bold rounded-xl hover:bg-slate-200 transition-all"
                                    >
                                        <RefreshCw size={18} /> Refresh
                                    </button>
                                    <button
                                        onClick={handleDownloadReport}
                                        className="flex items-center gap-2 px-6 py-3 bg-teal-600 text-white font-black rounded-xl hover:bg-teal-700 shadow-xl shadow-teal-600/20 transition-all hover:-translate-y-0.5"
                                    >
                                        <Download size={18} /> Download PDF Report
                                    </button>
                                </div>
                            </div>

                            {reportLoading ? (
                                <div className="flex flex-col items-center justify-center py-40 gap-4">
                                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-slate-200 border-t-teal-600"></div>
                                    <p className="text-slate-400 font-bold uppercase tracking-widest text-[10px]">Assembling Report Data...</p>
                                </div>
                            ) : report && (
                                <div className="space-y-10 bg-white p-12 rounded-[3rem] shadow-2xl border border-slate-100 min-h-screen relative overflow-hidden">
                                    {/* Hospital Logo Style Header */}
                                    <div className="flex justify-between items-start border-b-2 border-slate-50 pb-10">
                                        <div>
                                            <div className="text-teal-600 font-black text-2xl tracking-tighter mb-1">CLINICAL DOC</div>
                                            <div className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">Documentation Assistant</div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-sm font-bold text-slate-900">Internal Medical Record</div>
                                            <div className="text-xs text-slate-400 font-medium">Ref: {patient.mrn}</div>
                                            <div className="text-xs text-slate-400 font-medium">Generated: {new Date(report.generated_at).toLocaleString()}</div>
                                        </div>
                                    </div>

                                    {/* Demographics Grid */}
                                    <section>
                                        <h3 className="text-xs font-black uppercase tracking-[0.2em] text-teal-600 mb-6 flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-teal-500"></div> Patient Information
                                        </h3>
                                        <div className="grid grid-cols-4 gap-8">
                                            <div>
                                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider block mb-1">Full Name</label>
                                                <div className="text-slate-900 font-bold">{patient.name}</div>
                                            </div>
                                            <div>
                                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider block mb-1">Date of Birth</label>
                                                <div className="text-slate-900 font-bold">{new Date(patient.date_of_birth).toLocaleDateString()}</div>
                                            </div>
                                            <div>
                                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider block mb-1">Gender</label>
                                                <div className="text-slate-900 font-bold">{patient.gender || 'N/A'}</div>
                                            </div>
                                            <div>
                                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider block mb-1">MRN</label>
                                                <div className="text-slate-900 font-bold font-mono">{patient.mrn}</div>
                                            </div>
                                        </div>
                                    </section>

                                    {/* Clinical Sections */}
                                    <div className="grid grid-cols-2 gap-12">
                                        <section>
                                            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-orange-600 mb-6 flex items-center gap-2">
                                                <div className="w-2 h-2 rounded-full bg-orange-500"></div> Allergies & Severity
                                            </h3>
                                            <div className="space-y-3">
                                                {patient.allergies?.length > 0 ? patient.allergies.map((a: any, i: number) => (
                                                    <div key={i} className="flex justify-between items-center p-3 bg-slate-50 rounded-xl border border-slate-100">
                                                        <span className="font-bold text-slate-800">{a.allergen}</span>
                                                        <span className="text-[10px] font-black uppercase tracking-widest text-orange-600 bg-orange-50 px-2 py-0.5 rounded-md">{a.severity}</span>
                                                    </div>
                                                )) : <p className="text-slate-400 italic text-sm">No documented allergies.</p>}
                                            </div>
                                        </section>

                                        <section>
                                            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-blue-600 mb-6 flex items-center gap-2">
                                                <div className="w-2 h-2 rounded-full bg-blue-500"></div> Active Medications
                                            </h3>
                                            <div className="space-y-3">
                                                {patient.medications?.filter((m: any) => m.status === 'Active').length > 0 ?
                                                    patient.medications.filter((m: any) => m.status === 'Active').map((m: any, i: number) => (
                                                        <div key={i} className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                                                            <div className="font-bold text-slate-800">{m.name}</div>
                                                            <div className="text-[10px] text-slate-500 font-bold uppercase mt-0.5">{m.dosage} • {m.frequency}</div>
                                                        </div>
                                                    )) : <p className="text-slate-400 italic text-sm">No active medications.</p>}
                                            </div>
                                        </section>
                                    </div>

                                    <section>
                                        <h3 className="text-xs font-black uppercase tracking-[0.2em] text-indigo-600 mb-6 flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-indigo-500"></div> Surgical & Procedure History
                                        </h3>
                                        <div className="bg-slate-50 rounded-[2rem] border border-slate-100 overflow-hidden">
                                            <table className="w-full text-left text-xs">
                                                <thead>
                                                    <tr className="bg-slate-100/50 text-slate-400 font-black uppercase tracking-widest">
                                                        <th className="px-6 py-4">Procedure</th>
                                                        <th className="px-6 py-4">Date</th>
                                                        <th className="px-6 py-4">Clinical Notes</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-slate-100">
                                                    {patient.procedures?.map((p: any, i: number) => (
                                                        <tr key={i}>
                                                            <td className="px-6 py-4 font-bold text-slate-900">{p.name}</td>
                                                            <td className="px-6 py-4 text-slate-500">{new Date(p.date).toLocaleDateString()}</td>
                                                            <td className="px-6 py-4 text-slate-500 italic">{p.notes || '-'}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </section>

                                    <section>
                                        <h3 className="text-xs font-black uppercase tracking-[0.2em] text-rose-600 mb-6 flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-rose-500"></div> Financial Summary
                                        </h3>
                                        <div className="flex gap-8">
                                            <div className="flex-1 bg-rose-50/50 p-6 rounded-3xl border border-rose-100">
                                                <div className="text-[10px] font-black text-rose-400 uppercase tracking-widest mb-1">Total Billed</div>
                                                <div className="text-3xl font-black text-slate-900">${(patient.total_billing_amount || 0).toLocaleString()}</div>
                                            </div>
                                            <div className="flex-1 bg-teal-50/50 p-6 rounded-3xl border border-teal-100">
                                                <div className="text-[10px] font-black text-teal-400 uppercase tracking-widest mb-1">Outstanding</div>
                                                <div className="text-3xl font-black text-slate-900">${(patient.outstanding_billing_amount || 0).toLocaleString()}</div>
                                            </div>
                                        </div>
                                    </section>

                                    <section className="pb-20">
                                        <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-900 mb-6 flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-slate-900"></div> Provider Documentation
                                        </h3>
                                        <div className="space-y-6">
                                            {report.notes?.map((n: any, i: number) => (
                                                <div key={i} className="pl-6 border-l-2 border-slate-100">
                                                    <div className="flex justify-between items-center mb-2">
                                                        <div className="font-bold text-slate-900">{n.title}</div>
                                                        <div className="text-[10px] text-slate-400 font-medium">{new Date(n.created_at).toLocaleDateString()}</div>
                                                    </div>
                                                    <p className="text-xs text-slate-500 leading-relaxed whitespace-pre-wrap line-clamp-4 italic">
                                                        &quot;{n.raw_content}&quot;
                                                    </p>
                                                </div>
                                            ))}
                                        </div>
                                    </section>

                                    {/* Report Footer */}
                                    <div className="absolute bottom-8 left-12 right-12 flex justify-between items-center text-[9px] font-black uppercase tracking-[0.2em] text-slate-300">
                                        <div>AI-Assisted Documentation System</div>
                                        <div>Confidential Patient Record • NO MEDICAL ADVICE</div>
                                        <div>Page 01 of 01</div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </main>

            <footer className="bg-slate-900 text-slate-400 py-6 text-center text-xs px-8">
                <div className="flex items-center justify-center gap-2 mb-2 text-amber-500 font-bold uppercase tracking-wider">
                    <AlertCircle size={16} />
                    <span>Documentation Assistance Only</span>
                </div>
                <p>
                    This system uses AI to restructure clinical data. It does <strong>NOT</strong> provide medical advice, diagnosis, or treatment recommendations.
                    <br />
                    All generated content must be reviewed and verified by a licensed clinician before finalizing.
                </p>
            </footer>

            <Modal
                isOpen={isModalOpen}
                onClose={closeModal}
                title={
                    modalType === 'patient' ? 'Edit Patient Details' :
                        modalType === 'medication' ? (editingItem ? 'Edit Medication' : 'Add Medication') :
                            modalType === 'procedure' ? (editingItem ? 'Edit Procedure' : 'Add Procedure') :
                                modalType === 'document' ? (editingItem ? 'Edit Document' : 'Add Document') :
                                    modalType === 'task' ? (editingItem ? 'Edit Task' : 'Add Task') :
                                        modalType === 'billing' ? (editingItem ? 'Edit Billing Item' : 'Add Billing Item') :
                                            modalType === 'allergy' ? (editingItem ? 'Edit Allergy' : 'Add Allergy') :
                                                modalType === 'admission' ? (editingItem ? 'Update Stay Record' : 'Record Hospital Stay') :
                                                    modalType === 'history' ? (editingItem ? 'Edit Condition' : 'Record Medical Condition') : 'Action'
                }
            >
                {modalType === 'patient' && <PatientForm initialData={editingItem} onSubmit={handleFormSubmit} onCancel={closeModal} />}
                {modalType === 'medication' && <MedicationForm initialData={editingItem} notes={notes} onSubmit={handleFormSubmit} onCancel={closeModal} />}
                {modalType === 'procedure' && <ProcedureForm initialData={editingItem} notes={notes} admissions={admissions} onSubmit={handleFormSubmit} onCancel={closeModal} />}
                {modalType === 'document' && <DocumentForm initialData={editingItem} onSubmit={handleFormSubmit} onCancel={closeModal} />}
                {modalType === 'task' && <TaskForm initialData={editingItem} onSubmit={handleFormSubmit} onCancel={closeModal} />}
                {modalType === 'billing' && <BillingForm initialData={editingItem} onSubmit={handleFormSubmit} onCancel={closeModal} />}
                {modalType === 'allergy' && <AllergyForm initialData={editingItem} onSubmit={handleFormSubmit} onCancel={closeModal} />}
                {modalType === 'admission' && <AdmissionForm initialData={editingItem} onSubmit={handleFormSubmit} onCancel={closeModal} />}
                {modalType === 'history' && <HistoryForm initialData={editingItem} onSubmit={handleFormSubmit} onCancel={closeModal} />}
            </Modal>
        </div >
    );
}

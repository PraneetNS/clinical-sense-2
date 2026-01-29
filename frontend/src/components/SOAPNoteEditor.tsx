"use client";

import React, { useState } from 'react';
import { Save, Copy, RotateCcw, AlertTriangle } from 'lucide-react';

interface NoteData {
    [key: string]: string;
}

const NOTE_SCHEMAS: Record<string, { key: string; label: string; description: string }[]> = {
    SOAP: [
        { key: 'subjective', label: 'Subjective', description: "Patient's reports, history, symptoms" },
        { key: 'objective', label: 'Objective', description: 'Exam findings, vitals, labs' },
        { key: 'assessment', label: 'Assessment', description: 'Summary of status' },
        { key: 'plan', label: 'Plan', description: 'Next steps, follow-up, education' },
    ],
    PROGRESS: [
        { key: 'interval_history', label: 'Interval History', description: 'Events or changes since last visit' },
        { key: 'exam', label: 'Exam', description: 'Current physical findings' },
        { key: 'impression', label: 'Impression', description: 'Current status of problems' },
        { key: 'plan', label: 'Plan', description: 'Changes to medication or care plan' },
    ],
    DISCHARGE: [
        { key: 'admission_diagnosis', label: 'Admission Diagnosis', description: 'Reason for admission' },
        { key: 'hospital_course', label: 'Hospital Course', description: 'Brief summary of treatment' },
        { key: 'discharge_condition', label: 'Discharge Condition', description: 'Stable, Improved, etc.' },
        { key: 'discharge_medication', label: 'Discharge Medication', description: 'List of meds to take home' },
        { key: 'follow_up', label: 'Follow Up', description: 'Instructions for next appointment' },
    ]
};

export default function DynamicNoteEditor({
    initialData,
    onSave,
    noteType = 'SOAP'
}: {
    initialData: any,
    onSave: (data: any, status: string) => void,
    noteType?: string
}) {
    const [data, setData] = useState<NoteData>(initialData || {});

    // Fallback to SOAP if type unknown or generic keys found
    const sections = NOTE_SCHEMAS[noteType] || NOTE_SCHEMAS['SOAP'];

    const handleChange = (key: string, value: string) => {
        setData({ ...data, [key]: value });
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <h2 className="text-2xl font-bold text-slate-900">Structured {noteType} Note</h2>
                <div className="flex gap-3">
                    <button
                        onClick={() => onSave(data, 'draft')}
                        className="flex items-center gap-2 px-4 py-2 text-teal-600 bg-teal-50 hover:bg-teal-100 rounded-lg transition-colors font-semibold"
                    >
                        Save as Draft
                    </button>
                    <button
                        onClick={() => onSave(data, 'finalized')}
                        className="flex items-center gap-2 px-6 py-2 bg-teal-600 text-white font-semibold rounded-lg hover:bg-teal-700 transition-colors shadow-sm"
                    >
                        <Save size={18} /> Finalize Note
                    </button>
                </div>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-3 text-amber-800 text-sm">
                <AlertTriangle className="shrink-0" size={20} />
                <div>
                    <strong>AI Safety Review Required:</strong> Please verify all facts and clinical details. This AI does not provide diagnoses or treatment plans. You are responsible for the clinical accuracy of this document.
                </div>
            </div>

            <div className="grid grid-cols-1 gap-6">
                {sections.map((section) => (
                    <div key={section.key} className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
                        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
                            <h3 className="font-bold text-slate-800 text-lg">{section.label}</h3>
                            <p className="text-xs text-slate-500 uppercase tracking-wider">{section.description}</p>
                        </div>
                        <textarea
                            className="w-full h-48 p-6 text-slate-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-teal-500 resize-none"
                            value={data[section.key] || ''}
                            onChange={(e) => handleChange(section.key, e.target.value)}
                        />
                    </div>
                ))}
            </div>
        </div>
    );
}

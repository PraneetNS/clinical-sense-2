import React, { useState } from 'react';

interface ProcedureFormProps {
    initialData?: any;
    notes?: any[];
    admissions?: any[];
    onSubmit: (data: any) => Promise<void>;
    onCancel: () => void;
}

export default function ProcedureForm({ initialData, notes = [], admissions = [], onSubmit, onCancel }: ProcedureFormProps) {
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        name: initialData?.name || '',
        code: initialData?.code || '',
        date: initialData?.date ? new Date(initialData.date).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
        notes: initialData?.notes || '',
        source_note_id: initialData?.source_note_id || '',
        admission_id: initialData?.admission_id || ''
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await onSubmit(formData);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Procedure Name</label>
                <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                    placeholder="e.g. Appendectomy"
                />
            </div>
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">CPT/ICD Code</label>
                    <input
                        type="text"
                        value={formData.code}
                        onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                        placeholder="e.g. 44950"
                    />
                </div>
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Date</label>
                    <input
                        type="date"
                        value={formData.date}
                        onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                    />
                </div>
            </div>
            <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Notes</label>
                <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none h-24 resize-none"
                    placeholder="Additional details..."
                />
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Source Clinical Note (Optional)</label>
                    <select
                        value={formData.source_note_id}
                        onChange={(e) => setFormData({ ...formData, source_note_id: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                    >
                        <option value="">-- None --</option>
                        {notes.map(note => (
                            <option key={note.id} value={note.id}>
                                {new Date(note.created_at).toLocaleDateString()} - {note.title}
                            </option>
                        ))}
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Linked Admission (Optional)</label>
                    <select
                        value={formData.admission_id}
                        onChange={(e) => setFormData({ ...formData, admission_id: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                    >
                        <option value="">-- None --</option>
                        {admissions.map(adm => (
                            <option key={adm.id} value={adm.id}>
                                {new Date(adm.admission_date).toLocaleDateString()} - {adm.reason}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-50 mt-6">
                <button
                    type="button"
                    onClick={onCancel}
                    disabled={loading}
                    className="px-4 py-2 text-slate-600 font-bold hover:bg-slate-50 rounded-lg"
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2 bg-teal-600 text-white font-bold rounded-lg hover:bg-teal-700 disabled:opacity-50"
                >
                    {loading ? 'Saving...' : 'Save Procedure'}
                </button>
            </div>
        </form>
    );
}

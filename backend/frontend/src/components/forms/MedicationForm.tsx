import React, { useState } from 'react';

interface MedicationFormProps {
    initialData?: any;
    notes?: any[];
    onSubmit: (data: any) => Promise<void>;
    onCancel: () => void;
}

export default function MedicationForm({ initialData, notes = [], onSubmit, onCancel }: MedicationFormProps) {
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        name: initialData?.name || '',
        dosage: initialData?.dosage || '',
        frequency: initialData?.frequency || '',
        status: initialData?.status || 'Active',
        start_date: initialData?.start_date ? new Date(initialData.start_date).toISOString().split('T')[0] : '',
        end_date: initialData?.end_date ? new Date(initialData.end_date).toISOString().split('T')[0] : '',
        source_note_id: initialData?.source_note_id || ''
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
                <label className="block text-sm font-bold text-slate-700 mb-1">Medication Name</label>
                <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                    placeholder="e.g. Lisinopril"
                />
            </div>
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Dosage</label>
                    <input
                        type="text"
                        value={formData.dosage}
                        onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                        placeholder="e.g. 10mg"
                    />
                </div>
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Frequency</label>
                    <input
                        type="text"
                        value={formData.frequency}
                        onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                        placeholder="e.g. Daily"
                    />
                </div>
            </div>

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
                <label className="block text-sm font-bold text-slate-700 mb-1">Status</label>
                <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                >
                    <option value="Active">Active</option>
                    <option value="Discontinued">Discontinued</option>
                    <option value="Completed">Completed</option>
                </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Start Date</label>
                    <input
                        type="date"
                        value={formData.start_date}
                        onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                    />
                </div>
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">End Date</label>
                    <input
                        type="date"
                        value={formData.end_date}
                        onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                    />
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
                    {loading ? 'Saving...' : 'Save Medication'}
                </button>
            </div>
        </form>
    );
}

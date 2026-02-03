import React, { useState } from 'react';

export default function HistoryForm({ initialData, onSubmit, onCancel }: { initialData?: any; onSubmit: (data: any) => Promise<void>; onCancel: () => void }) {
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        condition_name: initialData?.condition_name || '',
        diagnosis_date: initialData?.diagnosis_date ? new Date(initialData.diagnosis_date).toISOString().split('T')[0] : '',
        status: initialData?.status || 'Active',
        notes: initialData?.notes || ''
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
                <label className="block text-sm font-bold text-slate-700 mb-1">Medical Condition</label>
                <input
                    type="text"
                    required
                    value={formData.condition_name}
                    onChange={(e) => setFormData({ ...formData, condition_name: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 outline-none"
                    placeholder="e.g. Hypertension, Type 2 Diabetes"
                />
            </div>
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Diagnosis Date</label>
                    <input
                        type="date"
                        value={formData.diagnosis_date}
                        onChange={(e) => setFormData({ ...formData, diagnosis_date: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 outline-none"
                    />
                </div>
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Status</label>
                    <select
                        value={formData.status}
                        onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 outline-none"
                    >
                        <option value="Active">Active</option>
                        <option value="Resolved">Resolved</option>
                        <option value="Chronic">Chronic</option>
                        <option value="Intermittent">Intermittent</option>
                    </select>
                </div>
            </div>
            <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Notes</label>
                <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 outline-none h-24 resize-none"
                />
            </div>

            <div className="flex justify-end gap-3 pt-6 border-t border-slate-50 mt-6">
                <button type="button" onClick={onCancel} className="px-4 py-2 text-slate-600 font-bold">Cancel</button>
                <button type="submit" disabled={loading} className="px-8 py-2 bg-slate-900 text-white font-bold rounded-xl hover:bg-slate-800 transition-all disabled:opacity-50">
                    {loading ? 'Saving...' : 'Record Condition'}
                </button>
            </div>
        </form>
    );
}

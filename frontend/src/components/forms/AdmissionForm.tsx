import React, { useState } from 'react';

interface AdmissionFormProps {
    initialData?: any;
    onSubmit: (data: any) => Promise<void>;
    onCancel: () => void;
}

export default function AdmissionForm({ initialData, onSubmit, onCancel }: AdmissionFormProps) {
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        admission_date: initialData?.admission_date ? new Date(initialData.admission_date).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
        discharge_date: initialData?.discharge_date ? new Date(initialData.discharge_date).toISOString().split('T')[0] : '',
        reason: initialData?.reason || '',
        status: initialData?.status || 'Admitted',
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
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Admission Date</label>
                    <input
                        type="date"
                        required
                        value={formData.admission_date}
                        onChange={(e) => setFormData({ ...formData, admission_date: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 outline-none"
                    />
                </div>
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Discharge Date</label>
                    <input
                        type="date"
                        value={formData.discharge_date}
                        onChange={(e) => setFormData({ ...formData, discharge_date: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 outline-none"
                    />
                </div>
                <div className="col-span-2">
                    <label className="block text-sm font-bold text-slate-700 mb-1">Reason for Admission</label>
                    <input
                        type="text"
                        required
                        value={formData.reason}
                        onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
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
                        <option value="Admitted">Admitted</option>
                        <option value="Observation">Observation</option>
                        <option value="Discharged">Discharged</option>
                        <option value="Transferred">Transferred</option>
                    </select>
                </div>
                <div className="col-span-2">
                    <label className="block text-sm font-bold text-slate-700 mb-1">Clinical Notes</label>
                    <textarea
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 outline-none h-24 resize-none"
                    />
                </div>
            </div>

            <div className="flex justify-end gap-3 pt-6 border-t border-slate-50 mt-6">
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
                    className="px-8 py-2 bg-slate-900 text-white font-bold rounded-xl hover:bg-slate-800 disabled:opacity-50"
                >
                    {loading ? 'Processing...' : 'Record Admission'}
                </button>
            </div>
        </form>
    );
}

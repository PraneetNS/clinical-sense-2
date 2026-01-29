import React, { useState } from 'react';

interface PatientFormProps {
    initialData?: any;
    onSubmit: (data: any) => Promise<void>;
    onCancel: () => void;
}

export default function PatientForm({ initialData, onSubmit, onCancel }: PatientFormProps) {
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        name: initialData?.name || '',
        mrn: initialData?.mrn || '',
        date_of_birth: initialData?.date_of_birth ? new Date(initialData.date_of_birth).toISOString().split('T')[0] : '',
        gender: initialData?.gender || '',
        phone_number: initialData?.phone_number || '',
        address: initialData?.address || '',
        emergency_contact_name: initialData?.emergency_contact_name || '',
        emergency_contact_relation: initialData?.emergency_contact_relation || '',
        emergency_contact_phone: initialData?.emergency_contact_phone || ''
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
                <div className="col-span-2">
                    <label className="block text-sm font-bold text-slate-700 mb-1">Full Name</label>
                    <input
                        type="text"
                        required
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                    />
                </div>
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">MRN</label>
                    <input
                        type="text"
                        required
                        value={formData.mrn}
                        onChange={(e) => setFormData({ ...formData, mrn: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                    />
                </div>
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Date of Birth</label>
                    <input
                        type="date"
                        required
                        value={formData.date_of_birth}
                        onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                    />
                </div>
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Gender</label>
                    <select
                        value={formData.gender}
                        onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                    >
                        <option value="">Select...</option>
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Phone</label>
                    <input
                        type="tel"
                        value={formData.phone_number}
                        onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                    />
                </div>
                <div className="col-span-2">
                    <label className="block text-sm font-bold text-slate-700 mb-1">Address</label>
                    <textarea
                        value={formData.address}
                        onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none h-20 resize-none"
                    />
                </div>
            </div>

            <div className="border-t border-slate-100 my-6 pt-6">
                <h4 className="text-sm font-bold text-slate-900 mb-4 uppercase tracking-wider">Emergency Contact</h4>
                <div className="grid grid-cols-2 gap-4">
                    <div className="col-span-2">
                        <label className="block text-sm font-bold text-slate-700 mb-1">Contact Name</label>
                        <input
                            type="text"
                            value={formData.emergency_contact_name}
                            onChange={(e) => setFormData({ ...formData, emergency_contact_name: e.target.value })}
                            className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Relation</label>
                        <input
                            type="text"
                            value={formData.emergency_contact_relation}
                            onChange={(e) => setFormData({ ...formData, emergency_contact_relation: e.target.value })}
                            className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Contact Phone</label>
                        <input
                            type="tel"
                            value={formData.emergency_contact_phone}
                            onChange={(e) => setFormData({ ...formData, emergency_contact_phone: e.target.value })}
                            className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                        />
                    </div>
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
                    {loading ? 'Saving...' : 'Save Details'}
                </button>
            </div>
        </form>
    );
}

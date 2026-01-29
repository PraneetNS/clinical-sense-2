import React, { useState } from 'react';

interface DocumentFormProps {
    initialData?: any;
    onSubmit: (data: any) => Promise<void>;
    onCancel: () => void;
}

export default function DocumentForm({ initialData, onSubmit, onCancel }: DocumentFormProps) {
    const [loading, setLoading] = useState(false);
    const [file, setFile] = useState<File | null>(null);
    const [formData, setFormData] = useState({
        title: initialData?.title || '',
        file_type: initialData?.file_type || 'PDF',
        file_url: initialData?.file_url || '',
        summary: initialData?.summary || ''
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            // Pass file if selected
            await onSubmit({ ...formData, file });
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Document Title</label>
                <input
                    type="text"
                    required
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                    placeholder="e.g. Lab Results"
                />
            </div>
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">File Type</label>
                    <select
                        value={formData.file_type}
                        onChange={(e) => setFormData({ ...formData, file_type: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                    >
                        <option value="PDF">PDF</option>
                        <option value="Image">Image</option>
                        <option value="Text">Text</option>
                        <option value="Other">Other</option>
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">File URL (or Upload below)</label>
                    <input
                        type="url"
                        value={formData.file_url}
                        onChange={(e) => setFormData({ ...formData, file_url: e.target.value })}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                        placeholder="https://..."
                    />
                </div>
            </div>

            <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">AI Summary (Optional)</label>
                <textarea
                    value={formData.summary}
                    onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none h-24 resize-none"
                    placeholder="Brief summary of the document content..."
                />
            </div>

            {!initialData && (
                <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Upload File</label>
                    <input
                        type="file"
                        onChange={(e) => {
                            if (e.target.files && e.target.files[0]) {
                                setFile(e.target.files[0]);
                                // Auto-set title if empty
                                if (!formData.title) {
                                    setFormData(prev => ({ ...prev, title: e.target.files![0].name }));
                                }
                            }
                        }}
                        className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100"
                    />
                </div>
            )}

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
                    {loading ? 'Saving...' : 'Save Document'}
                </button>
            </div>
        </form >
    );
}

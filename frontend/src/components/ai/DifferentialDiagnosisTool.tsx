import React, { useState } from 'react';
import { aiApi } from '@/lib/api';
import { Loader2, Activity, Play, AlertCircle } from 'lucide-react';

export default function DifferentialDiagnosisTool({ patientAge, patientGender }: { patientAge?: number, patientGender?: string }) {
    const [symptoms, setSymptoms] = useState('');
    const [vitals, setVitals] = useState('');
    const [differentials, setDifferentials] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleRun = async () => {
        if (!symptoms.trim()) return;
        setLoading(true);
        setError(null);
        try {
            const symptomList = symptoms.split(',').map(s => s.trim());
            const response = await aiApi.differential({
                symptoms: symptomList,
                vitals: vitals ? { "raw": vitals } : {},
                age: patientAge || 30, // Default if not provided
                gender: patientGender || "Unknown"
            });
            setDifferentials(response.data.differentials || []);
        } catch (err) {
            setError("Failed to generate diagnosis. Please try again.");
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="px-6 py-4 bg-indigo-50 border-b border-indigo-100 flex items-center justify-between">
                <h3 className="font-bold text-indigo-900 flex items-center gap-2">
                    <Activity size={20} className="text-indigo-600" />
                    Differential Diagnosis Generator
                </h3>
            </div>

            <div className="p-6 space-y-4">
                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Symptoms (comma separated)</label>
                    <input
                        type="text"
                        placeholder="e.g. Chest pain, shortness of breath, nausea"
                        value={symptoms}
                        onChange={(e) => setSymptoms(e.target.value)}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Vitals (Optional)</label>
                    <input
                        type="text"
                        placeholder="e.g. BP 140/90, HR 110"
                        value={vitals}
                        onChange={(e) => setVitals(e.target.value)}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    />
                </div>

                <button
                    onClick={handleRun}
                    disabled={loading || !symptoms}
                    className="w-full bg-indigo-600 text-white font-semibold py-2.5 rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                    {loading ? <Loader2 className="animate-spin" size={20} /> : <Play size={20} />}
                    {loading ? "Analyzing..." : "Generate Differentials"}
                </button>

                {error && (
                    <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm border border-red-100 mt-2">
                        {error}
                    </div>
                )}

                {/* Results */}
                {differentials.length > 0 && (
                    <div className="space-y-4 mt-6 animate-in slide-in-from-top-2">
                        <h4 className="font-bold text-slate-900">Top Potential Conditions</h4>
                        {differentials.map((diff, i) => (
                            <div key={i} className="p-4 bg-slate-50 border border-slate-200 rounded-xl hover:border-indigo-200 transition-colors">
                                <div className="flex justify-between items-start mb-2">
                                    <h5 className="font-bold text-indigo-900">{diff.condition}</h5>
                                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${diff.confidence === 'High' ? 'bg-red-100 text-red-700' : 'bg-slate-200 text-slate-700'}`}>
                                        {diff.confidence} Confidence
                                    </span>
                                </div>
                                <p className="text-sm text-slate-600 mb-3">{diff.reasoning}</p>

                                {diff.suggested_tests?.length > 0 && (
                                    <div className="text-xs text-slate-500">
                                        <strong className="text-slate-700">Recommended Tests:</strong> {diff.suggested_tests.join(', ')}
                                    </div>
                                )}
                            </div>
                        ))}
                        <div className="p-3 bg-amber-50 text-amber-800 text-xs rounded-lg flex items-start gap-2 border border-amber-100">
                            <AlertCircle size={14} className="mt-0.5 shrink-0" />
                            AI-generated suggestion. Clinical validation required. Not a definitive diagnosis.
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}


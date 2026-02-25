import React from 'react';
import { AlertTriangle, Info, CheckCircle, FileText } from 'lucide-react';

interface AIInsightsProps {
    insights: {
        risk_score: string;
        red_flags: string[];
        suggestions: string[];
        missing_info: string[];
    } | null;
}

export default function GlobalRiskPanel({ insights }: AIInsightsProps) {
    if (!insights) return null;

    const getRiskColor = (score: string) => {
        switch (score.toUpperCase()) {
            case 'HIGH': return 'bg-red-100 text-red-800 border-red-200';
            case 'MEDIUM': return 'bg-orange-100 text-orange-800 border-orange-200';
            case 'LOW': return 'bg-green-100 text-green-800 border-green-200';
            default: return 'bg-slate-100 text-slate-800 border-slate-200';
        }
    };

    return (
        <div className="space-y-6">
            <div className={`p-4 rounded-xl border flex items-center justify-between ${getRiskColor(insights.risk_score)}`}>
                <div className="flex items-center gap-3">
                    <AlertTriangle className="shrink-0" />
                    <div>
                        <h3 className="font-bold text-lg">Risk Level: {insights.risk_score}</h3>
                        <p className="text-sm opacity-90">AI-detected clinical risk score based on current note.</p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Red Flags */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <h4 className="font-bold text-red-600 flex items-center gap-2 mb-4">
                        <AlertTriangle size={18} /> Red Flags
                    </h4>
                    {insights.red_flags.length > 0 ? (
                        <ul className="space-y-2">
                            {insights.red_flags.map((flag, i) => (
                                <li key={i} className="text-sm text-slate-700 bg-red-50 p-2 rounded-lg border border-red-100">
                                    {flag}
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-sm text-slate-500 italic">No critical red flags detected.</p>
                    )}
                </div>

                {/* Suggestions */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <h4 className="font-bold text-teal-600 flex items-center gap-2 mb-4">
                        <CheckCircle size={18} /> Clinical Suggestions
                    </h4>
                    {insights.suggestions.length > 0 ? (
                        <ul className="space-y-2">
                            {insights.suggestions.map((sug, i) => (
                                <li key={i} className="text-sm text-slate-700 bg-teal-50 p-2 rounded-lg border border-teal-100">
                                    {sug}
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-sm text-slate-500 italic">No specific suggestions.</p>
                    )}
                </div>

                {/* Missing Info */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm md:col-span-2">
                    <h4 className="font-bold text-amber-600 flex items-center gap-2 mb-4">
                        <FileText size={18} /> Documentation Gaps
                    </h4>
                    {insights.missing_info.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                            {insights.missing_info.map((info, i) => (
                                <span key={i} className="text-xs font-medium text-amber-800 bg-amber-50 px-3 py-1 rounded-full border border-amber-200">
                                    {info}
                                </span>
                            ))}
                        </div>
                    ) : (
                        <p className="text-sm text-slate-500 italic">Documentation appears complete.</p>
                    )}
                </div>
            </div>
        </div>
    );
}


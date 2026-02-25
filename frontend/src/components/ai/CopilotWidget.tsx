import React, { useEffect, useState, useRef } from 'react';
import { Lightbulb, AlertTriangle, ShieldCheck, X } from 'lucide-react';

interface CopilotSuggestion {
    suggestions: string[];
    warnings: string[];
    disclaimer: string;
}

export default function CopilotWidget({
    activeField,
    content,
    isActive
}: {
    activeField: string,
    content: string,
    isActive: boolean
}) {
    const [suggestion, setSuggestion] = useState<CopilotSuggestion | null>(null);
    const [socket, setSocket] = useState<WebSocket | null>(null);
    const debounceTimer = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        // Only connect if active and we have content
        if (!isActive) return;

        const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/copilot`);

        ws.onopen = () => {
            console.log("Copilot Connected");
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                setSuggestion(data);
            } catch (e) {
                console.error("Failed to parse copilot message", e);
            }
        };

        ws.onerror = (error) => {
            console.error("Copilot WebSocket Error:", error);
        };

        setSocket(ws);

        return () => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        };
    }, [isActive]);

    // Send updates when content changes, debounced
    useEffect(() => {
        if (!socket || socket.readyState !== WebSocket.OPEN || !content) return;

        if (debounceTimer.current) clearTimeout(debounceTimer.current);

        debounceTimer.current = setTimeout(() => {
            const payload = JSON.stringify({
                text: content,
                field: activeField
            });
            socket.send(payload);
        }, 1000); // 1-second debounce to avoid spamming

        return () => {
            if (debounceTimer.current) clearTimeout(debounceTimer.current);
        };
    }, [content, activeField, socket]);

    if (!suggestion || (suggestion.suggestions.length === 0 && suggestion.warnings.length === 0)) return null;

    return (
        <div className="fixed bottom-8 right-8 w-80 bg-white rounded-2xl shadow-2xl border border-indigo-100 overflow-hidden animate-in slide-in-from-bottom-4 transition-all z-50">
            <div className="bg-indigo-600 px-4 py-3 flex items-center justify-between text-white">
                <div className="flex items-center gap-2 font-bold text-sm">
                    <ShieldCheck size={16} />
                    Clinical Copilot
                </div>
                <button onClick={() => setSuggestion(null)} className="hover:bg-indigo-700 p-1 rounded">
                    <X size={14} />
                </button>
            </div>

            <div className="p-4 max-h-80 overflow-y-auto space-y-4">
                {/* Warnings */}
                {suggestion.warnings.length > 0 && (
                    <div className="space-y-2">
                        <h5 className="text-xs font-bold text-red-600 uppercase tracking-wider flex items-center gap-1">
                            <AlertTriangle size={12} /> Safety Alerts
                        </h5>
                        <ul className="space-y-2">
                            {suggestion.warnings.map((warn, i) => (
                                <li key={i} className="text-sm text-slate-700 bg-red-50 p-2 rounded border border-red-100">
                                    {warn}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* Suggestions */}
                {suggestion.suggestions.length > 0 && (
                    <div className="space-y-2">
                        <h5 className="text-xs font-bold text-indigo-600 uppercase tracking-wider flex items-center gap-1">
                            <Lightbulb size={12} /> Documentation Tips
                        </h5>
                        <ul className="space-y-2">
                            {suggestion.suggestions.map((sug, i) => (
                                <li key={i} className="text-sm text-slate-700 bg-indigo-50 p-2 rounded border border-indigo-100">
                                    {sug}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                <div className="pt-2 border-t border-slate-100 text-[10px] text-slate-400 text-center">
                    {suggestion.disclaimer}
                </div>
            </div>
        </div>
    );
}

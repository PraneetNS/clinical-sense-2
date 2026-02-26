"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle, XCircle, Brain, ChevronRight } from "lucide-react";

const mockSOAPLines = [
    "S: Patient presents with persistent chest pain for 3 days,",
    "   radiating to left arm, worse with exertion...",
    "O: BP 145/92, HR 88, SpO2 97%, ECG shows ST elevation...",
    "A: Suspect acute coronary syndrome. Rule out MI...",
    "P: Stat troponin, serial ECGs, cardiology consult...",
];

const differentials = [
    { condition: "Acute Myocardial Infarction", confidence: 87, color: "text-red-400", bg: "bg-red-500/10" },
    { condition: "Unstable Angina", confidence: 72, color: "text-amber-400", bg: "bg-amber-500/10" },
    { condition: "Pulmonary Embolism", confidence: 34, color: "text-blue-400", bg: "bg-blue-500/10" },
    { condition: "Costochondritis", confidence: 18, color: "text-emerald-400", bg: "bg-emerald-500/10" },
    { condition: "GERD / Esophageal Spasm", confidence: 12, color: "text-slate-400", bg: "bg-slate-500/10" },
];

const riskItems = [
    { text: "ST elevation detected — urgent cardiology consult needed", type: "critical" },
    { text: "Troponin levels not yet ordered — recommend stat labs", type: "warning" },
    { text: "Allergy to aspirin not documented in chart", type: "warning" },
    { text: "Patient consent for catheterization required", type: "info" },
];

function TypewriterText({ lines }: { lines: string[] }) {
    const [displayedLines, setDisplayedLines] = useState<string[]>([]);
    const [currentLine, setCurrentLine] = useState(0);
    const [currentChar, setCurrentChar] = useState(0);

    useEffect(() => {
        if (currentLine >= lines.length) {
            const timeout = setTimeout(() => {
                setDisplayedLines([]);
                setCurrentLine(0);
                setCurrentChar(0);
            }, 3000);
            return () => clearTimeout(timeout);
        }

        const line = lines[currentLine];
        if (currentChar < line.length) {
            const timeout = setTimeout(() => {
                setDisplayedLines((prev) => {
                    const updated = [...prev];
                    updated[currentLine] = line.substring(0, currentChar + 1);
                    return updated;
                });
                setCurrentChar((c) => c + 1);
            }, 25);
            return () => clearTimeout(timeout);
        } else {
            const timeout = setTimeout(() => {
                setCurrentLine((l) => l + 1);
                setCurrentChar(0);
            }, 200);
            return () => clearTimeout(timeout);
        }
    }, [currentLine, currentChar, lines]);

    return (
        <div className="font-mono text-xs leading-relaxed space-y-1">
            {displayedLines.map((line, i) => (
                <div key={i} className={line.startsWith("S:") ? "text-blue-400" : line.startsWith("O:") ? "text-emerald-400" : line.startsWith("A:") ? "text-amber-400" : line.startsWith("P:") ? "text-violet-400" : "text-slate-400"}>
                    {line}
                    {i === displayedLines.length - 1 && currentLine < lines.length && (
                        <span className="inline-block w-2 h-4 bg-blue-400/70 ml-0.5 animate-blink" />
                    )}
                </div>
            ))}
        </div>
    );
}

function AnimatedConfidenceBar({ value, delay }: { value: number; delay: number }) {
    return (
        <div className="w-full h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
            <motion.div
                initial={{ width: 0 }}
                whileInView={{ width: `${value}%` }}
                viewport={{ once: true }}
                transition={{ duration: 1.2, delay, ease: "easeOut" }}
                className={`h-full rounded-full ${value > 70 ? "bg-gradient-to-r from-red-500 to-red-400" : value > 40 ? "bg-gradient-to-r from-amber-500 to-amber-400" : "bg-gradient-to-r from-blue-500 to-blue-400"}`}
            />
        </div>
    );
}

export default function AIVisualizationSection() {
    return (
        <section className="relative py-32 px-6">
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.8 }}
                className="text-center mb-20"
            >
                <span className="inline-block px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-medium mb-6">
                    Live Preview
                </span>
                <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6">
                    See the AI{" "}
                    <span className="bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">
                        in Action
                    </span>
                </h2>
                <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                    Watch how ClinicalSense processes clinical data in real-time.
                </p>
            </motion.div>

            <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* AI Response Panel */}
                <motion.div
                    initial={{ opacity: 0, x: -30 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.7 }}
                    className="lg:col-span-2 bg-white/[0.02] backdrop-blur-xl border border-white/[0.06] rounded-2xl overflow-hidden"
                >
                    {/* Terminal header */}
                    <div className="flex items-center gap-2 px-5 py-3 bg-white/[0.03] border-b border-white/[0.06]">
                        <div className="flex gap-1.5">
                            <div className="w-3 h-3 rounded-full bg-red-500/50" />
                            <div className="w-3 h-3 rounded-full bg-amber-500/50" />
                            <div className="w-3 h-3 rounded-full bg-emerald-500/50" />
                        </div>
                        <span className="text-xs text-slate-500 font-mono ml-2">ClinicalSense AI Engine — Live Analysis</span>
                        <div className="ml-auto flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                            <span className="text-xs text-emerald-400">Processing</span>
                        </div>
                    </div>

                    {/* Content area */}
                    <div className="p-6 space-y-6">
                        {/* Risk Score Badge */}
                        <div className="flex items-center gap-4">
                            <div className="px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/20">
                                <div className="flex items-center gap-2">
                                    <AlertTriangle className="w-4 h-4 text-red-400" />
                                    <span className="text-sm font-semibold text-red-400">HIGH RISK</span>
                                </div>
                                <span className="text-2xl font-bold text-red-300 mt-1 block">87<span className="text-sm text-red-400/60">/100</span></span>
                            </div>
                            <div className="flex-1">
                                <p className="text-sm text-slate-400 mb-2">AI-Generated SOAP Note</p>
                                <TypewriterText lines={mockSOAPLines} />
                            </div>
                        </div>

                        {/* Risk items */}
                        <div className="space-y-2">
                            <h4 className="text-xs uppercase tracking-wider text-slate-500 mb-3">Detected Alerts</h4>
                            {riskItems.map((item, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -10 }}
                                    whileInView={{ opacity: 1, x: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: 0.5 + i * 0.15 }}
                                    className={`flex items-start gap-3 px-4 py-2.5 rounded-xl ${item.type === "critical" ? "bg-red-500/5 border border-red-500/10" :
                                            item.type === "warning" ? "bg-amber-500/5 border border-amber-500/10" :
                                                "bg-blue-500/5 border border-blue-500/10"
                                        }`}
                                >
                                    {item.type === "critical" ? <XCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" /> :
                                        item.type === "warning" ? <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" /> :
                                            <CheckCircle className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />}
                                    <span className="text-sm text-slate-300">{item.text}</span>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </motion.div>

                {/* Differential Diagnosis Panel */}
                <motion.div
                    initial={{ opacity: 0, x: 30 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.7, delay: 0.2 }}
                    className="bg-white/[0.02] backdrop-blur-xl border border-white/[0.06] rounded-2xl overflow-hidden"
                >
                    <div className="flex items-center gap-2 px-5 py-3 bg-white/[0.03] border-b border-white/[0.06]">
                        <Brain className="w-4 h-4 text-violet-400" />
                        <span className="text-xs text-slate-400 font-medium">Differential Diagnosis</span>
                    </div>
                    <div className="p-5 space-y-4">
                        {differentials.map((d, i) => (
                            <motion.div
                                key={d.condition}
                                initial={{ opacity: 0, y: 10 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: 0.4 + i * 0.12 }}
                                className="space-y-2"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <ChevronRight className={`w-3 h-3 ${d.color}`} />
                                        <span className="text-sm text-slate-300">{d.condition}</span>
                                    </div>
                                    <span className={`text-sm font-mono font-bold ${d.color}`}>
                                        {d.confidence}%
                                    </span>
                                </div>
                                <AnimatedConfidenceBar value={d.confidence} delay={0.4 + i * 0.12} />
                            </motion.div>
                        ))}

                        <div className="pt-4 mt-4 border-t border-white/[0.06]">
                            <h4 className="text-xs uppercase tracking-wider text-slate-500 mb-3">Suggested Tests</h4>
                            {["Troponin I/T (Stat)", "Serial ECG", "D-Dimer", "Chest X-Ray"].map((test, i) => (
                                <motion.div
                                    key={test}
                                    initial={{ opacity: 0 }}
                                    whileInView={{ opacity: 1 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: 1 + i * 0.1 }}
                                    className="flex items-center gap-2 py-1.5"
                                >
                                    <CheckCircle className="w-3 h-3 text-emerald-400" />
                                    <span className="text-xs text-slate-400">{test}</span>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </motion.div>
            </div>
        </section>
    );
}

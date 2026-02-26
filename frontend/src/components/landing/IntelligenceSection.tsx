"use client";

import { motion } from "framer-motion";
import { Brain, Microscope, Scale, Zap } from "lucide-react";

const features = [
    {
        icon: Brain,
        title: "Clinical Risk Detection",
        accent: "blue",
        items: [
            "Red flag identification in clinical notes",
            "Missing documentation alerts",
            "Harmful drug interaction detection",
            "Critical vitals anomaly warnings",
        ],
    },
    {
        icon: Microscope,
        title: "Differential Diagnosis Generator",
        accent: "emerald",
        items: [
            "Top 5 conditions by probability",
            "Confidence scores per diagnosis",
            "Suggested diagnostic tests",
            "Evidence-based reasoning chains",
        ],
    },
    {
        icon: Scale,
        title: "Medico-Legal Guard",
        accent: "violet",
        items: [
            "Documentation completeness scoring",
            "Legal defensibility assessment",
            "Consent validation checks",
            "Audit trail for every action",
        ],
    },
    {
        icon: Zap,
        title: "Real-Time Copilot",
        accent: "amber",
        items: [
            "WebSocket-powered live suggestions",
            "Smart recommendations while typing",
            "Context-aware auto-completions",
            "Instant SOAP structuring feedback",
        ],
    },
];

const accentMap: Record<string, { bg: string; border: string; text: string; glow: string; dot: string }> = {
    blue: {
        bg: "bg-blue-500/10",
        border: "border-blue-500/20 hover:border-blue-500/40",
        text: "text-blue-400",
        glow: "group-hover:shadow-blue-500/10",
        dot: "bg-blue-400",
    },
    emerald: {
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/20 hover:border-emerald-500/40",
        text: "text-emerald-400",
        glow: "group-hover:shadow-emerald-500/10",
        dot: "bg-emerald-400",
    },
    violet: {
        bg: "bg-violet-500/10",
        border: "border-violet-500/20 hover:border-violet-500/40",
        text: "text-violet-400",
        glow: "group-hover:shadow-violet-500/10",
        dot: "bg-violet-400",
    },
    amber: {
        bg: "bg-amber-500/10",
        border: "border-amber-500/20 hover:border-amber-500/40",
        text: "text-amber-400",
        glow: "group-hover:shadow-amber-500/10",
        dot: "bg-amber-400",
    },
};

const cardVariants = {
    hidden: { opacity: 0, y: 40 },
    visible: (i: number) => ({
        opacity: 1,
        y: 0,
        transition: { duration: 0.6, delay: i * 0.15, ease: [0.25, 0.46, 0.45, 0.94] },
    }),
};

export default function IntelligenceSection() {
    return (
        <section className="relative py-32 px-6">
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.8 }}
                className="text-center mb-20"
            >
                <span className="inline-block px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium mb-6">
                    Core Engine
                </span>
                <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6">
                    AI{" "}
                    <span className="bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
                        Intelligence Layer
                    </span>
                </h2>
                <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                    Four specialized AI engines working in parallel to provide comprehensive clinical decision support.
                </p>
            </motion.div>

            <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
                {features.map((feature, i) => {
                    const colors = accentMap[feature.accent];
                    return (
                        <motion.div
                            key={feature.title}
                            custom={i}
                            variants={cardVariants}
                            initial="hidden"
                            whileInView="visible"
                            viewport={{ once: true, margin: "-50px" }}
                        >
                            <motion.div
                                whileHover={{ y: -6 }}
                                transition={{ type: "spring", stiffness: 300 }}
                                className={`group relative bg-white/[0.02] backdrop-blur-xl border ${colors.border} rounded-2xl p-8 cursor-pointer transition-all duration-500 ${colors.glow} hover:shadow-2xl h-full`}
                            >
                                {/* Animated pulse border */}
                                <div className={`absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-700`}>
                                    <div className={`absolute inset-0 rounded-2xl border ${colors.border} animate-pulse-slow`} />
                                </div>

                                {/* Header */}
                                <div className="flex items-center gap-4 mb-6">
                                    <div className={`w-14 h-14 rounded-2xl ${colors.bg} flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                                        <feature.icon className={`w-7 h-7 ${colors.text}`} />
                                    </div>
                                    <h3 className="text-xl font-semibold text-white">{feature.title}</h3>
                                </div>

                                {/* Items */}
                                <ul className="space-y-3">
                                    {feature.items.map((item) => (
                                        <li key={item} className="flex items-start gap-3">
                                            <span className={`w-1.5 h-1.5 rounded-full ${colors.dot} mt-2 flex-shrink-0`} />
                                            <span className="text-sm text-slate-400 leading-relaxed">{item}</span>
                                        </li>
                                    ))}
                                </ul>
                            </motion.div>
                        </motion.div>
                    );
                })}
            </div>
        </section>
    );
}

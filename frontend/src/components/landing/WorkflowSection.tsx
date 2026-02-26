"use client";

import { motion } from "framer-motion";
import {
    FileText,
    Brain,
    AlertTriangle,
    Stethoscope,
    Scale,
    FileOutput,
    ChevronRight,
} from "lucide-react";

const steps = [
    {
        icon: FileText,
        title: "Raw Clinical Note",
        description: "Doctor enters unstructured clinical observations, patient history, and examination findings.",
        color: "from-slate-500 to-slate-400",
        glow: "shadow-slate-500/20",
    },
    {
        icon: Brain,
        title: "AI Structuring (SOAP)",
        description: "AI engine transforms raw text into structured SOAP format with intelligent categorization.",
        color: "from-blue-500 to-blue-400",
        glow: "shadow-blue-500/20",
    },
    {
        icon: AlertTriangle,
        title: "Risk Detection",
        description: "Automated detection of red flags, drug interactions, missing documentation, and critical alerts.",
        color: "from-amber-500 to-orange-400",
        glow: "shadow-amber-500/20",
    },
    {
        icon: Stethoscope,
        title: "Differential Diagnosis",
        description: "AI generates top 5 differential diagnoses with confidence scores and recommended tests.",
        color: "from-emerald-500 to-emerald-400",
        glow: "shadow-emerald-500/20",
    },
    {
        icon: Scale,
        title: "Medico-Legal Guard",
        description: "Documentation completeness audit, legal defensibility checks, and consent validation.",
        color: "from-violet-500 to-purple-400",
        glow: "shadow-violet-500/20",
    },
    {
        icon: FileOutput,
        title: "PDF Report Generation",
        description: "Production-ready clinical PDF with structured format, risk scores, and audit trail.",
        color: "from-cyan-500 to-cyan-400",
        glow: "shadow-cyan-500/20",
    },
];

const containerVariants = {
    hidden: {},
    visible: {
        transition: { staggerChildren: 0.15 },
    },
};

const cardVariants = {
    hidden: { opacity: 0, y: 40 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] },
    },
};

export default function WorkflowSection() {
    return (
        <section id="workflow" className="relative py-32 px-6">
            {/* Section heading */}
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.8 }}
                className="text-center mb-20"
            >
                <span className="inline-block px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-medium mb-6">
                    Intelligent Pipeline
                </span>
                <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6">
                    How{" "}
                    <span className="bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
                        ClinicalSense
                    </span>{" "}
                    Works
                </h2>
                <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                    From raw clinical observations to structured, risk-assessed, legally defensible documentation — in seconds.
                </p>
            </motion.div>

            {/* Pipeline */}
            <motion.div
                variants={containerVariants}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-50px" }}
                className="max-w-7xl mx-auto"
            >
                {/* Desktop: horizontal pipeline */}
                <div className="hidden lg:flex items-stretch gap-2 relative">
                    {steps.map((step, i) => (
                        <motion.div
                            key={step.title}
                            variants={cardVariants}
                            className="flex items-stretch flex-1"
                        >
                            <motion.div
                                whileHover={{ scale: 1.04, y: -8 }}
                                transition={{ type: "spring", stiffness: 300 }}
                                className={`group relative bg-white/[0.03] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-6 flex flex-col items-center text-center cursor-pointer hover:border-white/[0.15] transition-all duration-500 ${step.glow} hover:shadow-lg flex-1`}
                            >
                                {/* Step number */}
                                <div className="absolute -top-3 left-4 px-2.5 py-0.5 rounded-full bg-white/[0.06] border border-white/[0.1] text-xs text-slate-500 font-mono">
                                    {String(i + 1).padStart(2, "0")}
                                </div>

                                {/* Icon */}
                                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${step.color} flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                                    <step.icon className="w-7 h-7 text-white" />
                                </div>

                                <h3 className="text-base font-semibold text-white mb-2">{step.title}</h3>
                                <p className="text-sm text-slate-400 leading-relaxed opacity-70 group-hover:opacity-100 transition-opacity">
                                    {step.description}
                                </p>

                                {/* Pulse border on hover */}
                                <div className="absolute inset-0 rounded-2xl border border-blue-500/0 group-hover:border-blue-500/30 transition-all duration-500" />
                            </motion.div>

                            {/* Arrow connector */}
                            {i < steps.length - 1 && (
                                <div className="flex items-center px-1">
                                    <ChevronRight className="w-5 h-5 text-blue-500/40" />
                                </div>
                            )}
                        </motion.div>
                    ))}
                </div>

                {/* Mobile: vertical pipeline */}
                <div className="lg:hidden space-y-4">
                    {steps.map((step, i) => (
                        <motion.div key={step.title} variants={cardVariants}>
                            <div className="relative bg-white/[0.03] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-6 flex items-start gap-4">
                                {/* Step number line */}
                                <div className="flex flex-col items-center">
                                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${step.color} flex items-center justify-center shadow-lg flex-shrink-0`}>
                                        <step.icon className="w-6 h-6 text-white" />
                                    </div>
                                    {i < steps.length - 1 && (
                                        <div className="w-px h-8 bg-gradient-to-b from-blue-500/30 to-transparent mt-2" />
                                    )}
                                </div>

                                <div>
                                    <h3 className="text-lg font-semibold text-white mb-1">{step.title}</h3>
                                    <p className="text-sm text-slate-400 leading-relaxed">{step.description}</p>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </motion.div>
        </section>
    );
}

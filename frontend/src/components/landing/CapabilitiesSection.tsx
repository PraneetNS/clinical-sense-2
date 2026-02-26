"use client";

import { motion } from "framer-motion";
import {
    Clock,
    FolderKanban,
    ScrollText,
    ShieldCheck,
    KeyRound,
    FileText,
    ClipboardList,
    Users,
} from "lucide-react";

const capabilities = [
    { icon: Clock, title: "Patient Timeline View", desc: "Complete chronological medical journey with AI annotations" },
    { icon: FolderKanban, title: "Case Status Management", desc: "Active, closed, and archive case tracking with smart filters" },
    { icon: ScrollText, title: "Audit Logging", desc: "Every action tracked with immutable, tamper-proof audit trail" },
    { icon: Users, title: "Role-Based Access Control", desc: "Granular permissions for doctors, nurses, and admin staff" },
    { icon: KeyRound, title: "Secure JWT Authentication", desc: "Firebase-backed auth with automatic token refresh" },
    { icon: FileText, title: "PDF Clinical Reports", desc: "One-click professional PDF generation with branding" },
    { icon: ClipboardList, title: "Structured SOAP Formatting", desc: "AI-powered Subjective, Objective, Assessment, Plan structuring" },
    { icon: ShieldCheck, title: "HIPAA Compliance Built-in", desc: "End-to-end encryption and data handling compliance" },
];

const cardVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: (i: number) => ({
        opacity: 1,
        scale: 1,
        transition: { duration: 0.5, delay: i * 0.08, ease: [0.25, 0.46, 0.45, 0.94] },
    }),
};

export default function CapabilitiesSection() {
    return (
        <section className="relative py-32 px-6">
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.8 }}
                className="text-center mb-20"
            >
                <span className="inline-block px-4 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-sm font-medium mb-6">
                    Platform Features
                </span>
                <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6">
                    Built for{" "}
                    <span className="bg-gradient-to-r from-violet-400 to-blue-400 bg-clip-text text-transparent">
                        Clinicians
                    </span>
                </h2>
                <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                    Every feature designed by doctors, for doctors. No compromise on clinical workflow efficiency.
                </p>
            </motion.div>

            <div className="max-w-7xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                {capabilities.map((cap, i) => (
                    <motion.div
                        key={cap.title}
                        custom={i}
                        variants={cardVariants}
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, margin: "-30px" }}
                    >
                        <motion.div
                            whileHover={{ scale: 1.05, y: -4 }}
                            transition={{ type: "spring", stiffness: 400, damping: 20 }}
                            className="group bg-white/[0.03] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-6 h-full cursor-pointer hover:border-white/[0.15] hover:bg-white/[0.05] transition-all duration-300"
                        >
                            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/10 to-emerald-500/10 border border-white/[0.06] flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                                <cap.icon className="w-6 h-6 text-blue-400 group-hover:text-emerald-400 transition-colors duration-300" />
                            </div>
                            <h3 className="text-base font-semibold text-white mb-2">{cap.title}</h3>
                            <p className="text-sm text-slate-500 leading-relaxed">{cap.desc}</p>
                        </motion.div>
                    </motion.div>
                ))}
            </div>
        </section>
    );
}

"use client";

import { motion } from "framer-motion";
import {
    ShieldCheck,
    Lock,
    Gauge,
    ShieldAlert,
    Database,
    FileKey,
    ScrollText,
    Users,
} from "lucide-react";

const securityFeatures = [
    { icon: Lock, title: "JWT Authentication", desc: "Stateless, encrypted token-based authentication with automatic expiry" },
    { icon: Gauge, title: "Rate Limiting", desc: "Endpoint-specific traffic throttling to prevent abuse and DDoS attacks" },
    { icon: ShieldAlert, title: "Input Validation", desc: "Server-side sanitization of all clinical data to prevent injection" },
    { icon: Database, title: "SQL Injection Protection", desc: "Parameterized queries with SQLAlchemy ORM for complete DB safety" },
    { icon: FileKey, title: "Secure File Handling", desc: "Encrypted uploads with size validation and type-checking" },
    { icon: ScrollText, title: "Audit Trail Logging", desc: "Immutable log of every clinical action for regulatory compliance" },
    { icon: Users, title: "Role-Based Permissions", desc: "Granular RBAC with doctor, nurse, and admin role separation" },
    { icon: ShieldCheck, title: "HIPAA Compliant", desc: "Full compliance with healthcare data protection regulations" },
];

const shieldVariants = {
    hidden: { opacity: 0, scale: 0.8, rotateY: -15 },
    visible: {
        opacity: 1,
        scale: 1,
        rotateY: 0,
        transition: { duration: 1, ease: [0.25, 0.46, 0.45, 0.94] },
    },
};

export default function SecuritySection() {
    return (
        <section className="relative py-32 px-6 overflow-hidden">
            {/* Subtle grid background */}
            <div className="absolute inset-0 opacity-[0.03]"
                style={{
                    backgroundImage: `linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)`,
                    backgroundSize: "60px 60px",
                }}
            />

            <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.8 }}
                className="text-center mb-20"
            >
                <span className="inline-block px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium mb-6">
                    Zero-Trust Architecture
                </span>
                <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6">
                    Enterprise-Grade{" "}
                    <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                        Security
                    </span>
                </h2>
                <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                    Clinical data demands the highest security standards. Every layer is hardened for production.
                </p>
            </motion.div>

            <div className="max-w-7xl mx-auto relative">
                {/* Feature cards grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                    {securityFeatures.map((feature, i) => (
                        <motion.div
                            key={feature.title}
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-30px" }}
                            transition={{ duration: 0.5, delay: i * 0.08 }}
                        >
                            <motion.div
                                whileHover={{ scale: 1.04, y: -4 }}
                                className="group bg-white/[0.02] backdrop-blur-xl border border-white/[0.06] rounded-2xl p-6 h-full hover:border-emerald-500/20 transition-all duration-300 cursor-pointer"
                            >
                                <div className="w-11 h-11 rounded-xl bg-emerald-500/10 flex items-center justify-center mb-4 group-hover:bg-emerald-500/20 transition-colors">
                                    <feature.icon className="w-5 h-5 text-emerald-400" />
                                </div>
                                <h3 className="text-sm font-semibold text-white mb-2">{feature.title}</h3>
                                <p className="text-xs text-slate-500 leading-relaxed">{feature.desc}</p>
                            </motion.div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
}

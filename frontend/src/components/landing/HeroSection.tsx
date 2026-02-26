"use client";

import { motion } from "framer-motion";
import { ArrowRight, Play, Shield, Brain, Activity } from "lucide-react";
import { useRouter } from "next/navigation";

const FloatingCard = ({
    children,
    className = "",
    delay = 0,
}: {
    children: React.ReactNode;
    className?: string;
    delay?: number;
}) => (
    <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay, ease: [0.25, 0.46, 0.45, 0.94] }}
        className={`absolute ${className}`}
    >
        <motion.div
            animate={{ y: [0, -12, 0] }}
            transition={{ duration: 5 + delay, repeat: Infinity, ease: "easeInOut" }}
        >
            {children}
        </motion.div>
    </motion.div>
);

const GlassCard = ({
    icon,
    label,
    value,
    color,
}: {
    icon: React.ReactNode;
    label: string;
    value: string;
    color: string;
}) => (
    <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.08] rounded-2xl p-4 shadow-2xl min-w-[180px]">
        <div className="flex items-center gap-3 mb-2">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${color}`}>
                {icon}
            </div>
            <span className="text-xs text-slate-400 uppercase tracking-wider">{label}</span>
        </div>
        <p className="text-lg font-semibold text-white">{value}</p>
    </div>
);

export default function HeroSection() {
    const router = useRouter();

    return (
        <section className="relative min-h-screen flex items-center justify-center overflow-hidden px-6">
            {/* Heartbeat ring */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="w-[800px] h-[800px] rounded-full border border-blue-500/[0.06] animate-heartbeat" />
                <div className="absolute w-[600px] h-[600px] rounded-full border border-emerald-500/[0.05] animate-heartbeat" style={{ animationDelay: "0.5s" }} />
                <div className="absolute w-[400px] h-[400px] rounded-full border border-blue-400/[0.04] animate-heartbeat" style={{ animationDelay: "1s" }} />
            </div>

            {/* Floating Cards - Desktop only */}
            <div className="hidden lg:block">
                <FloatingCard className="top-[18%] left-[8%]" delay={0.6}>
                    <GlassCard
                        icon={<Brain className="w-4 h-4 text-blue-400" />}
                        label="AI Analysis"
                        value="98.7% Accuracy"
                        color="bg-blue-500/20"
                    />
                </FloatingCard>

                <FloatingCard className="top-[25%] right-[6%]" delay={0.9}>
                    <GlassCard
                        icon={<Activity className="w-4 h-4 text-emerald-400" />}
                        label="Risk Score"
                        value="Low (12/100)"
                        color="bg-emerald-500/20"
                    />
                </FloatingCard>

                <FloatingCard className="bottom-[22%] left-[5%]" delay={1.2}>
                    <GlassCard
                        icon={<Shield className="w-4 h-4 text-violet-400" />}
                        label="Legal Shield"
                        value="Protected"
                        color="bg-violet-500/20"
                    />
                </FloatingCard>
            </div>

            {/* Hero Content */}
            <div className="relative z-10 text-center max-w-5xl mx-auto">
                {/* Badge */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/[0.05] border border-white/[0.1] backdrop-blur-sm mb-8"
                >
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-sm text-slate-300 font-medium">AI-Powered Clinical Intelligence</span>
                </motion.div>

                {/* Main Heading */}
                <motion.h1
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                    className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-6"
                >
                    <span className="bg-gradient-to-r from-white via-blue-100 to-white bg-clip-text text-transparent">
                        AI Clinical Copilot
                    </span>
                    <br />
                    <span className="bg-gradient-to-r from-blue-400 via-emerald-400 to-blue-400 bg-clip-text text-transparent">
                        for Modern Healthcare
                    </span>
                </motion.h1>

                {/* Subheading */}
                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.4 }}
                    className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed"
                >
                    Structure notes. Detect risks. Generate differentials.
                    <br className="hidden md:block" />
                    Protect legally. All in one intelligent platform.
                </motion.p>

                {/* CTA Buttons */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.6 }}
                    className="flex flex-col sm:flex-row items-center justify-center gap-4"
                >
                    <button
                        onClick={() => router.push("/login")}
                        className="group relative px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-500 rounded-2xl text-white font-semibold text-lg shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all duration-300 hover:scale-[1.02] overflow-hidden"
                    >
                        <span className="absolute inset-0 bg-gradient-to-r from-blue-400 to-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                        <span className="relative flex items-center gap-2">
                            Enter Dashboard
                            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </span>
                    </button>

                    <button
                        onClick={() => {
                            const workflow = document.getElementById("workflow");
                            workflow?.scrollIntoView({ behavior: "smooth" });
                        }}
                        className="group px-8 py-4 bg-white/[0.05] border border-white/[0.1] backdrop-blur-sm rounded-2xl text-white font-medium text-lg hover:bg-white/[0.1] transition-all duration-300 hover:scale-[1.02]"
                    >
                        <span className="flex items-center gap-2">
                            <Play className="w-5 h-5 text-emerald-400" />
                            Watch Workflow
                        </span>
                    </button>
                </motion.div>

                {/* Stats row */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 1, delay: 1 }}
                    className="flex flex-wrap items-center justify-center gap-8 mt-16 text-sm"
                >
                    {[
                        { label: "Clinical Notes Processed", value: "1M+" },
                        { label: "Active Hospitals", value: "250+" },
                        { label: "Risk Detection Rate", value: "99.2%" },
                        { label: "HIPAA Compliant", value: "✓" },
                    ].map((stat) => (
                        <div key={stat.label} className="text-center">
                            <p className="text-2xl font-bold text-white">{stat.value}</p>
                            <p className="text-slate-500 mt-1">{stat.label}</p>
                        </div>
                    ))}
                </motion.div>
            </div>

            {/* Scroll indicator */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.5 }}
                className="absolute bottom-8 left-1/2 -translate-x-1/2"
            >
                <motion.div
                    animate={{ y: [0, 8, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="w-6 h-10 rounded-full border-2 border-white/20 flex items-start justify-center p-1.5"
                >
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                </motion.div>
            </motion.div>
        </section>
    );
}

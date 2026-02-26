"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import NeuralBackground from "@/components/landing/NeuralBackground";
import HeroSection from "@/components/landing/HeroSection";
import WorkflowSection from "@/components/landing/WorkflowSection";
import IntelligenceSection from "@/components/landing/IntelligenceSection";
import CapabilitiesSection from "@/components/landing/CapabilitiesSection";
import SecuritySection from "@/components/landing/SecuritySection";
import AIVisualizationSection from "@/components/landing/AIVisualizationSection";
import CTASection from "@/components/landing/CTASection";
import { Brain, Menu, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

function Navbar() {
    const router = useRouter();
    const [scrolled, setScrolled] = useState(false);
    const [menuOpen, setMenuOpen] = useState(false);

    useEffect(() => {
        const onScroll = () => setScrolled(window.scrollY > 50);
        window.addEventListener("scroll", onScroll);
        return () => window.removeEventListener("scroll", onScroll);
    }, []);

    const navLinks = [
        { label: "Workflow", href: "#workflow" },
        { label: "Intelligence", href: "#intelligence" },
        { label: "Security", href: "#security" },
    ];

    const scrollTo = (id: string) => {
        const el = document.querySelector(id);
        el?.scrollIntoView({ behavior: "smooth" });
        setMenuOpen(false);
    };

    return (
        <motion.nav
            initial={{ y: -80 }}
            animate={{ y: 0 }}
            transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
            className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled
                    ? "bg-[#0f172a]/80 backdrop-blur-xl border-b border-white/[0.06] shadow-2xl"
                    : "bg-transparent"
                }`}
        >
            <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                {/* Logo */}
                <div className="flex items-center gap-3 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
                        <Brain className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <span className="text-lg font-bold text-white">ClinicalSense</span>
                        <span className="hidden sm:block text-[10px] text-slate-500 uppercase tracking-widest -mt-0.5">AI Clinical Copilot</span>
                    </div>
                </div>

                {/* Desktop nav */}
                <div className="hidden md:flex items-center gap-8">
                    {navLinks.map((link) => (
                        <button
                            key={link.label}
                            onClick={() => scrollTo(link.href)}
                            className="text-sm text-slate-400 hover:text-white transition-colors duration-200"
                        >
                            {link.label}
                        </button>
                    ))}
                    <button
                        onClick={() => router.push("/login")}
                        className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-blue-500 rounded-xl text-white text-sm font-medium shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 hover:scale-[1.03] transition-all duration-200"
                    >
                        Enter Dashboard
                    </button>
                </div>

                {/* Mobile menu toggle */}
                <button className="md:hidden text-white" onClick={() => setMenuOpen(!menuOpen)}>
                    {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                </button>
            </div>

            {/* Mobile nav dropdown */}
            <AnimatePresence>
                {menuOpen && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="md:hidden bg-[#0f172a]/95 backdrop-blur-xl border-b border-white/[0.06] overflow-hidden"
                    >
                        <div className="px-6 py-4 space-y-3">
                            {navLinks.map((link) => (
                                <button
                                    key={link.label}
                                    onClick={() => scrollTo(link.href)}
                                    className="block w-full text-left text-slate-400 hover:text-white transition-colors py-2"
                                >
                                    {link.label}
                                </button>
                            ))}
                            <button
                                onClick={() => router.push("/login")}
                                className="block w-full px-5 py-3 bg-gradient-to-r from-blue-600 to-blue-500 rounded-xl text-white text-sm font-medium text-center mt-2"
                            >
                                Enter Dashboard
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.nav>
    );
}

function Footer() {
    return (
        <footer className="relative border-t border-white/[0.04] py-12 px-6">
            <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center">
                        <Brain className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-sm text-slate-500">
                        © {new Date().getFullYear()} ClinicalSense. AI-Powered Clinical Intelligence.
                    </span>
                </div>
                <div className="flex items-center gap-6 text-xs text-slate-600">
                    <span>HIPAA Compliant</span>
                    <span>•</span>
                    <span>SOC 2 Type II</span>
                    <span>•</span>
                    <span>ISO 27001</span>
                </div>
            </div>
        </footer>
    );
}

// Loading screen
function LoadingScreen({ onComplete }: { onComplete: () => void }) {
    useEffect(() => {
        const timer = setTimeout(onComplete, 2200);
        return () => clearTimeout(timer);
    }, [onComplete]);

    return (
        <motion.div
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="fixed inset-0 z-[100] bg-[#020617] flex flex-col items-center justify-center"
        >
            {/* Pulsing logo */}
            <motion.div
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.6 }}
                className="relative"
            >
                <div className="absolute inset-0 w-20 h-20 rounded-2xl bg-blue-500/20 animate-ping" />
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center shadow-2xl shadow-blue-500/30">
                    <Brain className="w-10 h-10 text-white" />
                </div>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="mt-8 text-center"
            >
                <p className="text-xl font-semibold text-white">ClinicalSense</p>
                <p className="text-xs text-slate-500 uppercase tracking-[0.3em] mt-1">AI Clinical Copilot</p>
            </motion.div>

            {/* Loading bar */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
                className="mt-10 w-48 h-1 bg-white/[0.06] rounded-full overflow-hidden"
            >
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: "100%" }}
                    transition={{ duration: 1.5, delay: 0.8, ease: "easeInOut" }}
                    className="h-full bg-gradient-to-r from-blue-500 to-emerald-500 rounded-full"
                />
            </motion.div>
        </motion.div>
    );
}

export default function LandingPage() {
    const { token, isLoading: authLoading } = useAuth();
    const router = useRouter();
    const [loading, setLoading] = useState(true);

    // If already authenticated, redirect to dashboard
    useEffect(() => {
        if (!authLoading && token) {
            router.push("/dashboard");
        }
    }, [token, authLoading, router]);

    if (authLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-[#020617]">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
            </div>
        );
    }

    // If authenticated, don't render landing
    if (token) return null;

    return (
        <div className="relative min-h-screen bg-[#020617] text-white overflow-x-hidden">
            <AnimatePresence>
                {loading && <LoadingScreen onComplete={() => setLoading(false)} />}
            </AnimatePresence>

            {!loading && (
                <>
                    <NeuralBackground />
                    <Navbar />

                    <main className="relative z-10">
                        <HeroSection />

                        <div id="workflow">
                            <WorkflowSection />
                        </div>

                        <div id="intelligence">
                            <IntelligenceSection />
                        </div>

                        <CapabilitiesSection />

                        <div id="security">
                            <SecuritySection />
                        </div>

                        <AIVisualizationSection />
                        <CTASection />
                    </main>

                    <Footer />
                </>
            )}
        </div>
    );
}

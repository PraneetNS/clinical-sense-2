"use client";

import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";

export default function CTASection() {
    const router = useRouter();

    return (
        <section className="relative py-32 px-6 overflow-hidden">
            {/* Gradient background */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-600/10 via-transparent to-emerald-600/10" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#020617] via-transparent to-[#020617]" />

            {/* Glowing orbs */}
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-[120px]" />
            <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-[120px]" />

            <div className="relative z-10 max-w-4xl mx-auto text-center">
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, margin: "-100px" }}
                    transition={{ duration: 0.8 }}
                >
                    <motion.div
                        animate={{ rotate: [0, 5, -5, 0] }}
                        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                        className="inline-block mb-8"
                    >
                        <Sparkles className="w-12 h-12 text-blue-400" />
                    </motion.div>

                    <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
                        Empower Clinical Decisions
                        <br />
                        <span className="bg-gradient-to-r from-blue-400 via-emerald-400 to-blue-400 bg-clip-text text-transparent">
                            with AI Intelligence
                        </span>
                    </h2>

                    <p className="text-lg text-slate-400 max-w-xl mx-auto mb-12">
                        Join hundreds of hospitals already transforming clinical documentation with ClinicalSense.
                    </p>

                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => router.push("/login")}
                            className="group relative px-10 py-5 bg-gradient-to-r from-blue-600 to-emerald-600 rounded-2xl text-white font-semibold text-lg shadow-2xl shadow-blue-500/20 overflow-hidden"
                        >
                            {/* Shimmer effect */}
                            <span
                                className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                                style={{
                                    background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)",
                                    backgroundSize: "200% 100%",
                                    animation: "shimmer 2s linear infinite",
                                }}
                            />
                            <span className="relative flex items-center gap-2">
                                Login
                                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                            </span>
                        </motion.button>

                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => router.push("/login")}
                            className="px-10 py-5 bg-white/[0.05] border border-white/[0.1] backdrop-blur-sm rounded-2xl text-white font-semibold text-lg hover:bg-white/[0.1] transition-all duration-300"
                        >
                            Request Demo
                        </motion.button>
                    </div>
                </motion.div>
            </div>
        </section>
    );
}

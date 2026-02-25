import React, { useEffect, useState } from 'react';
import { workflowApi } from '../lib/api';

interface WorkflowDashboardProps {
    patientId: string | number;
}

interface WorkflowData {
    trajectory: {
        trend: string;
        risk_score: number;
        confidence_score: number;
    };
    discharge: {
        score: number;
        target: string;
        missing: string[];
    };
    pending_tasks: number;
    pending_tasks_list?: {
        id: number;
        description: string;
        priority: string;
        due_date: string;
    }[];
}

interface WorkflowDashboardProps {
    patientId: string | number;
    onViewTasks?: () => void;
}

export default function WorkflowDashboard({ patientId, onViewTasks }: WorkflowDashboardProps) {
    const [data, setData] = useState<WorkflowData | null>(null);
    const [loading, setLoading] = useState(true);
    const [checking, setChecking] = useState(false);

    const handleRunDischargeCheck = async () => {
        setChecking(true);
        try {
            await workflowApi.checkDischarge(patientId);
            // Wait slightly for AI processing (mock latency or real)
            setTimeout(() => {
                fetchData();
                setChecking(false);
            }, 3000); // Give AI time to process
        } catch (error) {
            console.error("Failed to run discharge check", error);
            setChecking(false);
        }
    };

    const fetchData = async () => {
        try {
            const response = await workflowApi.getDashboard(patientId);
            setData(response.data);
        } catch (error) {
            console.error("Failed to load workflow data", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 15000); // Poll every 15s
        return () => clearInterval(interval);
    }, [patientId]);

    if (loading && !data) return <div className="p-4 bg-gray-50 rounded animate-pulse">Loading AI Workflow...</div>;
    if (!data) return null;

    // Trend Visuals
    const getTrendColor = (trend: string) => {
        switch (trend?.toLowerCase()) {
            case 'improving': return 'text-green-600';
            case 'deteriorating': return 'text-red-600';
            case 'stable': return 'text-blue-600';
            default: return 'text-gray-500';
        }
    };

    const getTrendIcon = (trend: string) => {
        switch (trend?.toLowerCase()) {
            case 'improving': return '↑';
            case 'deteriorating': return '↓';
            case 'stable': return '→';
            default: return '?';
        }
    };

    return (
        <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 mb-8">
            <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                <span className="text-2xl">🤖</span> AI Clinical Workflow Engine
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* 1. Trajectory Engine */}
                <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100 relative overflow-hidden group hover:shadow-md transition-all">
                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Trajectory Analysis</h4>
                    <div className="flex items-center gap-4">
                        <span className={`text-5xl font-black ${getTrendColor(data.trajectory.trend)} transition-transform group-hover:scale-110`}>
                            {getTrendIcon(data.trajectory.trend)}
                        </span>
                        <div>
                            <div className={`text-xl font-black ${getTrendColor(data.trajectory.trend)}`}>
                                {data.trajectory.trend || "Uncertain"}
                            </div>
                            <div className="text-xs font-bold text-slate-500 mt-1">
                                Risk Score: <span className="text-slate-900">{data.trajectory.risk_score}/100</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 2. Discharge Readiness */}
                <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
                    <div className="flex justify-between items-start mb-4">
                        <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Discharge Readiness</h4>
                        <button
                            onClick={handleRunDischargeCheck}
                            disabled={checking}
                            className={`text-[10px] font-bold uppercase tracking-wider px-3 py-1.5 rounded-lg border transition-all ${checking
                                ? 'bg-indigo-100 text-indigo-400 border-indigo-100 cursor-wait'
                                : 'text-indigo-600 bg-white border-indigo-100 hover:bg-indigo-50 hover:shadow-sm'}`}
                        >
                            {checking ? 'Analyzing...' : 'Re-Check'}
                        </button>
                    </div>

                    <div className="flex items-end gap-2 mb-2">
                        <span className="text-4xl font-black text-slate-900">{data.discharge.score}%</span>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Ready</span>
                    </div>

                    <div className="w-full bg-slate-200 rounded-full h-2 mb-4 overflow-hidden">
                        <div
                            className="bg-indigo-600 h-full rounded-full transition-all duration-1000 ease-out"
                            style={{ width: `${data.discharge.score}%` }}
                        ></div>
                    </div>

                    {data.discharge.missing && data.discharge.missing.length > 0 ? (
                        <div className="space-y-1">
                            {data.discharge.missing.slice(0, 2).map((req, i) => (
                                <div key={i} className="flex items-start gap-2 text-[10px] font-bold text-slate-500">
                                    <span className="text-red-500 mt-0.5">●</span> {req}
                                </div>
                            ))}
                            {data.discharge.missing.length > 2 && (
                                <p className="text-[10px] font-bold text-slate-400 pl-3">+{data.discharge.missing.length - 2} more requirements</p>
                            )}
                        </div>
                    ) : (
                        <p className="text-xs font-bold text-green-600 flex items-center gap-1">
                            <span>✓</span> All criteria met
                        </p>
                    )}
                </div>

                {/* 3. Auto Tasks */}
                <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100 flex flex-col">
                    <div className="flex justify-between items-start mb-4">
                        <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Pending Tasks</h4>
                        <span className="bg-teal-100 text-teal-700 text-[10px] font-black px-2 py-1 rounded-md">
                            {data.pending_tasks} Active
                        </span>
                    </div>

                    <div className="flex-1 space-y-3 mb-4">
                        {data.pending_tasks_list && data.pending_tasks_list.length > 0 ? (
                            data.pending_tasks_list.map((task) => (
                                <div key={task.id} className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm flex items-center gap-3">
                                    <div className={`w-1.5 h-8 rounded-full ${task.priority === 'High' ? 'bg-red-500' : 'bg-teal-500'}`}></div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-xs font-bold text-slate-900 truncate">{task.description}</p>
                                        <p className="text-[10px] font-medium text-slate-400">Due {new Date(task.due_date).toLocaleDateString()}</p>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="h-full flex items-center justify-center text-slate-400 text-xs font-bold italic">
                                No pending tasks
                            </div>
                        )}
                    </div>

                    <button
                        onClick={onViewTasks}
                        className="w-full py-2 bg-white text-slate-600 text-xs font-black uppercase tracking-wider rounded-xl border border-slate-200 hover:bg-slate-100 hover:text-slate-900 transition-colors"
                    >
                        View All Tasks
                    </button>
                </div>
            </div>

            <div className="mt-4 flex justify-end items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                    AI confidence: {Math.round((data.trajectory.confidence_score || 0) * 100)}%
                </span>
            </div>
        </div>
    );
}

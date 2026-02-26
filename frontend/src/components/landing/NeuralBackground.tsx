"use client";

import { useEffect, useRef } from "react";

interface Node {
    x: number;
    y: number;
    vx: number;
    vy: number;
    radius: number;
    opacity: number;
    pulsePhase: number;
}

export default function NeuralBackground() {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let animationId: number;
        let nodes: Node[] = [];
        const NODE_COUNT = 60;
        const CONNECTION_DISTANCE = 180;
        const MOUSE = { x: -1000, y: -1000 };

        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };

        const initNodes = () => {
            nodes = Array.from({ length: NODE_COUNT }, () => ({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                radius: Math.random() * 2 + 1,
                opacity: Math.random() * 0.5 + 0.2,
                pulsePhase: Math.random() * Math.PI * 2,
            }));
        };

        const drawNode = (node: Node, time: number) => {
            const pulse = Math.sin(time * 0.002 + node.pulsePhase) * 0.3 + 0.7;
            const r = node.radius * pulse;

            // Outer glow
            const gradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, r * 4);
            gradient.addColorStop(0, `rgba(59, 130, 246, ${node.opacity * pulse * 0.6})`);
            gradient.addColorStop(0.5, `rgba(16, 185, 129, ${node.opacity * pulse * 0.2})`);
            gradient.addColorStop(1, "rgba(59, 130, 246, 0)");
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(node.x, node.y, r * 4, 0, Math.PI * 2);
            ctx.fill();

            // Core
            ctx.fillStyle = `rgba(147, 197, 253, ${node.opacity * pulse})`;
            ctx.beginPath();
            ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
            ctx.fill();
        };

        const drawConnections = (time: number) => {
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const dx = nodes[i].x - nodes[j].x;
                    const dy = nodes[i].y - nodes[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < CONNECTION_DISTANCE) {
                        const opacity = (1 - dist / CONNECTION_DISTANCE) * 0.15;
                        const flowOffset = (time * 0.001 + i * 0.1) % 1;

                        ctx.strokeStyle = `rgba(59, 130, 246, ${opacity})`;
                        ctx.lineWidth = 0.5;
                        ctx.beginPath();
                        ctx.moveTo(nodes[i].x, nodes[i].y);
                        ctx.lineTo(nodes[j].x, nodes[j].y);
                        ctx.stroke();

                        // Data flow particle on connection
                        if (opacity > 0.06) {
                            const px = nodes[i].x + (nodes[j].x - nodes[i].x) * flowOffset;
                            const py = nodes[i].y + (nodes[j].y - nodes[i].y) * flowOffset;
                            ctx.fillStyle = `rgba(52, 211, 153, ${opacity * 3})`;
                            ctx.beginPath();
                            ctx.arc(px, py, 1.5, 0, Math.PI * 2);
                            ctx.fill();
                        }
                    }
                }
            }
        };

        const animate = (time: number) => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            drawConnections(time);

            nodes.forEach((node) => {
                node.x += node.vx;
                node.y += node.vy;

                // Mouse repulsion
                const mdx = node.x - MOUSE.x;
                const mdy = node.y - MOUSE.y;
                const mDist = Math.sqrt(mdx * mdx + mdy * mdy);
                if (mDist < 150) {
                    node.vx += (mdx / mDist) * 0.05;
                    node.vy += (mdy / mDist) * 0.05;
                }

                // Speed limit
                const speed = Math.sqrt(node.vx * node.vx + node.vy * node.vy);
                if (speed > 0.8) {
                    node.vx *= 0.8 / speed;
                    node.vy *= 0.8 / speed;
                }

                // Wrap around
                if (node.x < -10) node.x = canvas.width + 10;
                if (node.x > canvas.width + 10) node.x = -10;
                if (node.y < -10) node.y = canvas.height + 10;
                if (node.y > canvas.height + 10) node.y = -10;

                drawNode(node, time);
            });

            animationId = requestAnimationFrame(animate);
        };

        const handleMouseMove = (e: MouseEvent) => {
            MOUSE.x = e.clientX;
            MOUSE.y = e.clientY;
        };

        resize();
        initNodes();
        animationId = requestAnimationFrame(animate);

        window.addEventListener("resize", () => { resize(); initNodes(); });
        window.addEventListener("mousemove", handleMouseMove);

        return () => {
            cancelAnimationFrame(animationId);
            window.removeEventListener("resize", resize);
            window.removeEventListener("mousemove", handleMouseMove);
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 z-0 pointer-events-none"
            style={{ background: "linear-gradient(to bottom, #0f172a, #020617)" }}
        />
    );
}

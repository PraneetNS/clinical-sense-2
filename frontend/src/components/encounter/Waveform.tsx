"use client";

import React, { useEffect, useRef } from 'react';

interface WaveformProps {
    stream: MediaStream | null;
    isRecording: boolean;
}

export default function Waveform({ stream, isRecording }: WaveformProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<number | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

    useEffect(() => {
        if (isRecording && stream && canvasRef.current) {
            const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
            const analyser = audioContext.createAnalyser();
            const source = audioContext.createMediaStreamAudioSource(stream);
            
            source.connect(analyser);
            analyser.fftSize = 256;
            
            audioContextRef.current = audioContext;
            analyserRef.current = analyser;
            sourceRef.current = source;
            
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            
            const canvas = canvasRef.current;
            const ctx = canvas.getContext('2d');
            
            const draw = () => {
                if (!ctx) return;
                
                animationRef.current = requestAnimationFrame(draw);
                analyser.getByteFrequencyData(dataArray);
                
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                const barWidth = (canvas.width / bufferLength) * 2.5;
                let barHeight;
                let x = 0;
                
                for (let i = 0; i < bufferLength; i++) {
                    barHeight = dataArray[i] / 2;
                    
                    // Gradient bars
                    const gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
                    gradient.addColorStop(0, '#14b8a6'); // teal-500
                    gradient.addColorStop(1, '#06b6d4'); // cyan-500
                    
                    ctx.fillStyle = gradient;
                    ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
                    
                    x += barWidth + 1;
                }
            };
            
            draw();
        } else {
            if (animationRef.current) cancelAnimationFrame(animationRef.current);
            if (audioContextRef.current) audioContextRef.current.close();
        }
        
        return () => {
            if (animationRef.current) cancelAnimationFrame(animationRef.current);
            if (audioContextRef.current) audioContextRef.current.close();
        };
    }, [isRecording, stream]);

    return (
        <canvas 
            ref={canvasRef} 
            width={300} 
            height={40} 
            className="w-full h-10 opacity-80"
        />
    );
}

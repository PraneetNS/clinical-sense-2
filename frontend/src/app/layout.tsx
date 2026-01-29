"use client";

import React from 'react';
import { AuthProvider } from '@/context/AuthContext';
import { ToastProvider } from '@/components/ui/Toast';
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-slate-50 text-slate-900 min-h-screen`}>
        <AuthProvider>
          <ToastProvider>
            <div className="flex flex-col min-h-screen">
              <header className="bg-red-600 text-white py-2 px-4 text-center text-sm font-bold shadow-md z-50">
                ⚠️ This tool assists with documentation only. It does NOT provide medical advice or diagnoses.
              </header>
              <div className="flex-1">
                {children}
              </div>
            </div>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}

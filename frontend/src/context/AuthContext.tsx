"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { authApi } from '@/lib/api';
import { auth } from '@/lib/firebase';
import { onAuthStateChanged, User, signOut } from 'firebase/auth';

interface AuthContextType {
    user: any | null;
    fbUser: User | null;
    token: string | null;
    logout: () => void;
    isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<any | null>(null);
    const [fbUser, setFbUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
            if (firebaseUser) {
                setFbUser(firebaseUser);
                const idToken = await firebaseUser.getIdToken();
                setToken(idToken);
                localStorage.setItem('token', idToken);

                try {
                    const res = await authApi.getMe();
                    setUser(res.data);
                    if (pathname === '/login' || pathname === '/register') {
                        router.push('/dashboard');
                    }
                } catch (err) {
                    console.error("Backend sync failed", err);
                }
            } else {
                setFbUser(null);
                setToken(null);
                setUser(null);
                localStorage.removeItem('token');
                if (pathname !== '/login' && pathname !== '/register' && !pathname.startsWith('/public')) {
                    router.push('/login');
                }
            }
            setIsLoading(false);
        });

        return () => unsubscribe();
    }, [pathname, router]);

    const logout = async () => {
        await signOut(auth);
        router.push('/login');
    };

    return (
        <AuthContext.Provider value={{ user, fbUser, token, logout, isLoading }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

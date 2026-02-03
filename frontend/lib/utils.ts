import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function formatCurrency(cents: number): string {
    return new Intl.NumberFormat('en-US', {
        style: 'currency', // formatCurrency existing

        currency: 'USD',
    }).format(cents / 100);
}

let base = process.env.NEXT_PUBLIC_API_URL || "";

if (typeof window !== 'undefined') {
    if (!base) {
        base = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
            ? "http://localhost:8000/api"
            : "/api";
    }

    // Auto-fix: if it's a railway or external URL missing https
    if (base.includes('.railway.app') && !base.startsWith('http')) {
        base = `https://${base}`;
    }

    // Auto-fix: if it's missing the /api suffix
    if (base.startsWith('http') && !base.endsWith('/api')) {
        base = base.endsWith('/') ? `${base}api` : `${base}/api`;
    }
} else {
    base = base || "http://127.0.0.1:8000/api";
}

export const API_BASE = base;

if (typeof window !== 'undefined') {
    console.log("🌸 Rabbit Kiosk API URL:", API_BASE);
}

export function getFullImageUrl(path: string | null | undefined): string {
    if (!path) return "";
    if (path.startsWith('http')) return path;
    const base = API_BASE.replace('/api', '');
    return `${base}${path}`;
}

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

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' ? (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? "http://localhost:8000/api" : "/api") : "http://127.0.0.1:8000/api");

if (typeof window !== 'undefined') {
    console.log("🌸 Rabbit Kiosk API Base:", API_BASE);
}

export function getFullImageUrl(path: string | null | undefined): string {
    if (!path) return "";
    if (path.startsWith('http')) return path;
    const base = API_BASE.replace('/api', '');
    return `${base}${path}`;
}

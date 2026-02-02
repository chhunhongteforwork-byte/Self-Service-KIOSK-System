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

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

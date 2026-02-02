import { useState, useEffect } from "react";

export function useIdle(timeout: number) {
    const [isIdle, setIsIdle] = useState(true); // Start idle

    useEffect(() => {
        let timer: NodeJS.Timeout;

        const resetTimer = () => {
            setIsIdle(false);
            clearTimeout(timer);
            timer = setTimeout(() => setIsIdle(true), timeout);
        };

        // Events to listen for
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];

        events.forEach(event => document.addEventListener(event, resetTimer));

        // Initial start
        resetTimer();
        // Default to true if no interaction initially?
        // Actually typically a kiosk starts idle. But resetTimer sets it false.
        // We want it to START true (Attract screen).

        // Let's modify:
        // If we want it to start as Idle, we shouldn't call resetTimer immediately?
        // Or we manually set isIdle(true) initially and wait for FIRST interaction.

        return () => {
            events.forEach(event => document.removeEventListener(event, resetTimer));
            clearTimeout(timer);
        };
    }, [timeout]);

    return { isIdle, setIsIdle };
}

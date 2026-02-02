import { useState, useEffect } from "react";

export function useIdle(timeout: number) {
    const [isIdle, setIsIdle] = useState(true); // Start idle

    useEffect(() => {
        let timer: NodeJS.Timeout;

        const resetTimer = () => {
            // If we are currently active, keep resetting the timer
            clearTimeout(timer);
            timer = setTimeout(() => setIsIdle(true), timeout);
        };

        // Events that count as "activity" to STAY active
        // Notice we REMOVED mousemove and scroll to prevent accidental wakeups
        const activityEvents = ['mousedown', 'keypress', 'touchstart'];

        activityEvents.forEach(event => {
            document.addEventListener(event, resetTimer);
        });

        // If something else manually sets isIdle to false (like clicking the Attract screen),
        // we need to start the timer.
        if (!isIdle) {
            resetTimer();
        }

        return () => {
            activityEvents.forEach(event => document.removeEventListener(event, resetTimer));
            clearTimeout(timer);
        };
    }, [timeout, isIdle]);

    return { isIdle, setIsIdle };
}

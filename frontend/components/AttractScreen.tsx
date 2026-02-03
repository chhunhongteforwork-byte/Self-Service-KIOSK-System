"use client";

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
// import RabbitImage from "@/public/rabbit.png"; // We don't have it yet, use placeholder or CSS art

export default function AttractScreen({ onStart }: { onStart: () => void }) {
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    return (
        <div className="fixed inset-0 z-50 bg-white/20 backdrop-blur-sm flex flex-col items-center justify-center cursor-pointer" onClick={onStart}>

            <motion.div
                animate={{ y: [0, -20, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                className="text-9xl mb-8"
            >
                🐰
            </motion.div>

            <motion.h1
                className="text-6xl font-black text-primary mb-4 text-center"
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
            >
                Welcome!
            </motion.h1>

            <p className="text-2xl text-muted-foreground animate-pulse">Tap anywhere to order</p>
        </div>
    );
}

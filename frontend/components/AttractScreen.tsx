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
        <div className="fixed inset-0 z-50 bg-background flex flex-col items-center justify-center cursor-pointer" onClick={onStart}>
            {/* Background decorations */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                {mounted && [...Array(20)].map((_, i) => (
                    <motion.div
                        key={i}
                        className="absolute text-primary/20 text-4xl"
                        initial={{
                            x: Math.random() * window.innerWidth,
                            y: Math.random() * window.innerHeight,
                            scale: 0.5 + Math.random()
                        }}
                        animate={{
                            y: [null, Math.random() * -100],
                            opacity: [0.2, 0.5, 0]
                        }}
                        transition={{
                            duration: 3 + Math.random() * 5,
                            repeat: Infinity,
                            ease: "linear"
                        }}
                    >
                        ✨
                    </motion.div>
                ))}
            </div>

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

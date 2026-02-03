"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

const RABBITS = ["🐰", "🐇", "🎀"];
const STRAWBERRIES = ["🍓", "🌸", "✨"];

interface Element {
    id: number;
    type: string;
    x: number;
    y: number;
    size: number;
    duration: number;
    delay: number;
}

export default function RabbitBackground() {
    const [elements, setElements] = useState<Element[]>([]);

    useEffect(() => {
        const newElements: Element[] = [];
        // Create 15 rabbits and 15 strawberries
        for (let i = 0; i < 30; i++) {
            newElements.push({
                id: i,
                type: i % 2 === 0
                    ? RABBITS[Math.floor(Math.random() * RABBITS.length)]
                    : STRAWBERRIES[Math.floor(Math.random() * STRAWBERRIES.length)],
                x: Math.random() * 100,
                y: Math.random() * 100,
                size: 20 + Math.random() * 40,
                duration: 15 + Math.random() * 25,
                delay: Math.random() * -20 // Start at different times
            });
        }
        setElements(newElements);
    }, []);

    return (
        <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10 bg-[#FFF0F5]/50">
            {elements.map((el) => (
                <motion.div
                    key={el.id}
                    initial={{
                        x: `${el.x}vw`,
                        y: `${el.y}vh`,
                        opacity: 0,
                        rotate: 0
                    }}
                    animate={{
                        x: [
                            `${el.x}vw`,
                            `${(el.x + 20) % 100}vw`,
                            `${(el.x - 20 + 100) % 100}vw`,
                            `${el.x}vw`
                        ],
                        y: [
                            `${el.y}vh`,
                            `${(el.y - 30 + 100) % 100}vh`,
                            `${(el.y + 30) % 100}vh`,
                            `${el.y}vh`
                        ],
                        opacity: [0.1, 0.3, 0.1],
                        rotate: [0, 45, -45, 0],
                        scale: [1, 1.2, 0.8, 1]
                    }}
                    transition={{
                        duration: el.duration,
                        repeat: Infinity,
                        delay: el.delay,
                        ease: "linear"
                    }}
                    style={{
                        position: "absolute",
                        fontSize: el.size,
                        filter: "blur(1px)"
                    }}
                >
                    {el.type}
                </motion.div>
            ))}

            {/* Soft pink gradient overlays for depth */}
            <div className="absolute inset-0 bg-gradient-to-tr from-primary/5 via-transparent to-accent/5" />
        </div>
    );
}

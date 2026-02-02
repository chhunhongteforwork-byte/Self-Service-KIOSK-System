"use client";

import { Product } from "@/types";
import { useCartStore } from "@/lib/store";
import { formatCurrency } from "@/lib/utils";
import { motion } from "framer-motion";
import { Plus } from "lucide-react";
import Image from "next/image";

interface ProductCardProps {
    product: Product;
}

export default function ProductCard({ product }: ProductCardProps) {
    const addToCart = useCartStore((state) => state.addToCart);

    return (
        <motion.div
            whileTap={{ scale: 0.95 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-card text-card-foreground rounded-2xl shadow-lg overflow-hidden border border-border flex flex-col h-full"
        >
            <div className="relative aspect-square w-full bg-muted">
                {product.image_url ? (
                    <Image
                        src={product.image_url.startsWith('http') ? product.image_url : `http://localhost:8000${product.image_url}`}
                        alt={product.name}
                        fill
                        className="object-cover"
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                        No Image
                    </div>
                )}
            </div>

            <div className="p-4 flex flex-col flex-1">
                <h3 className="font-bold text-lg leading-tight mb-2 line-clamp-2">{product.name}</h3>
                <div className="mt-auto flex items-center justify-between">
                    <span className="text-xl font-bold text-primary">
                        {formatCurrency(product.price)}
                    </span>
                    <button
                        onClick={() => addToCart(product)}
                        className="bg-primary text-primary-foreground p-3 rounded-full hover:bg-primary/90 transition-colors shadow-md active:scale-95"
                    >
                        <Plus size={24} />
                    </button>
                </div>
            </div>
        </motion.div>
    );
}

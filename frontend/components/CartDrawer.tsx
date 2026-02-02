"use client";

import { useCartStore } from "@/lib/store";
import { formatCurrency } from "@/lib/utils";
import { AnimatePresence, motion } from "framer-motion";
import { Minus, Plus, ShoppingBag, Trash2, X } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";

export default function CartDrawer() {
    const { items, isOpen, toggleCart, updateQuantity, removeFromCart, total } = useCartStore();
    const router = useRouter();

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 0.5 }}
                        exit={{ opacity: 0 }}
                        onClick={toggleCart}
                        className="fixed inset-0 bg-black z-40"
                    />

                    {/* Drawer */}
                    <motion.div
                        initial={{ x: "100%" }}
                        animate={{ x: 0 }}
                        exit={{ x: "100%" }}
                        transition={{ type: "spring", damping: 25, stiffness: 200 }}
                        className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-background border-l border-border z-50 flex flex-col shadow-2xl"
                    >
                        {/* Header */}
                        <div className="p-6 border-b border-border flex items-center justify-between bg-white/50 backdrop-blur-sm">
                            <div className="flex items-center gap-2">
                                <ShoppingBag className="text-primary" />
                                <h2 className="text-2xl font-bold text-primary">Your Order</h2>
                            </div>
                            <button onClick={toggleCart} className="p-2 hover:bg-muted rounded-full">
                                <X />
                            </button>
                        </div>

                        {/* Items */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-4">
                            {items.length === 0 ? (
                                <div className="text-center text-muted-foreground mt-20">
                                    <ShoppingBag size={48} className="mx-auto mb-4 opacity-50" />
                                    <p>Your cart is empty</p>
                                </div>
                            ) : (
                                items.map((item) => (
                                    <div key={item.product.id} className="flex gap-4 bg-white p-4 rounded-xl shadow-sm border border-border/50">
                                        <div className="relative w-20 h-20 rounded-lg overflow-hidden bg-muted flex-shrink-0">
                                            {item.product.image_url && (
                                                <Image
                                                    src={item.product.image_url.startsWith('http') ? item.product.image_url : `http://localhost:8000${item.product.image_url}`}
                                                    alt={item.product.name}
                                                    fill
                                                    className="object-cover"
                                                />
                                            )}
                                        </div>
                                        <div className="flex-1 flex flex-col justify-between">
                                            <h4 className="font-bold line-clamp-1">{item.product.name}</h4>
                                            <div className="flex items-center justify-between mt-2">
                                                <span className="font-bold text-primary">{formatCurrency(item.product.price * item.quantity)}</span>
                                                <div className="flex items-center gap-3 bg-muted rounded-full px-2 py-1">
                                                    <button onClick={() => updateQuantity(item.product.id, -1)} className="p-1 hover:text-primary">
                                                        <Minus size={16} />
                                                    </button>
                                                    <span className="font-bold text-sm w-4 text-center">{item.quantity}</span>
                                                    <button onClick={() => updateQuantity(item.product.id, 1)} className="p-1 hover:text-primary">
                                                        <Plus size={16} />
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        {/* Footer */}
                        {items.length > 0 && (
                            <div className="p-6 border-t border-border bg-white space-y-4">
                                <div className="flex justify-between text-xl font-bold">
                                    <span>Total</span>
                                    <span className="text-primary">{formatCurrency(total())}</span>
                                </div>
                                <button
                                    onClick={() => {
                                        toggleCart();
                                        router.push('/checkout');
                                    }}
                                    className="w-full bg-primary text-primary-foreground text-xl font-bold py-4 rounded-2xl shadow-lg hover:brightness-110 active:scale-95 transition-all flex items-center justify-center gap-2"
                                >
                                    Checkout
                                </button>
                            </div>
                        )}
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}

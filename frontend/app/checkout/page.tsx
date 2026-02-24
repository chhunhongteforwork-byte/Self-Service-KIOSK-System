"use client";

import { useCartStore } from "@/lib/store";
import { formatCurrency, API_BASE } from "@/lib/utils";
import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { ArrowLeft, CheckCircle, Loader2, FileText, Printer } from "lucide-react";
import { motion } from "framer-motion";

type CheckoutState = 'SUMMARY' | 'PROCESSING' | 'AWAITING_PAYMENT' | 'SUCCESS';

export default function CheckoutPage() {
    const { items, total, clearCart } = useCartStore();
    const router = useRouter();
    const [state, setState] = useState<CheckoutState>('SUMMARY');
    const [qrData, setQrData] = useState<any>(null); // ABA Response
    const [orderId, setOrderId] = useState<number | null>(null);
    const [orderNumber, setOrderNumber] = useState<string | null>(null);

    // Polling ref
    const pollTimer = useRef<NodeJS.Timeout>(undefined); // Fix for TS typing in browser env but using NodeJS namespace is standard in Next projects usually, or just use ReturnType<typeof setInterval>

    useEffect(() => {
        if (items.length === 0 && state === 'SUMMARY') {
            router.push('/');
        }
    }, [items, router, state]);

    // Polling Logic removed for manual confirmation

    // Cleanup to attract screen after success
    useEffect(() => {
        if (state === 'SUCCESS') {
            const t = setTimeout(() => {
                router.push('/');
            }, 10000); // 10s auto close
            return () => clearTimeout(t);
        }
    }, [state, router]);

    const handlePay = async () => {
        setState('PROCESSING');
        try {
            const payload = {
                items: items.map(i => ({
                    product_id: i.product.id,
                    quantity: i.quantity
                })),
                total_amount: Math.round(total()) // Backend should verify
            };

            const res = await fetch(`${API_BASE}/payments/checkout`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("Checkout failed");

            const data = await res.json();
            setQrData(data.qr_data);
            setOrderId(data.order_id);
            setOrderNumber(data.order_number);
            setState('AWAITING_PAYMENT');

        } catch (e) {
            alert("Payment initialization failed. Please try again.");
            setState('SUMMARY');
        }
    };

    if (state === 'SUCCESS') {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-green-50 p-6 text-center">
                <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="text-green-500 mb-6"
                >
                    <CheckCircle size={100} />
                </motion.div>
                <h1 className="text-4xl font-bold mb-4">Payment Successful!</h1>
                <p className="text-xl text-muted-foreground mb-8">Order #{orderNumber}</p>

                <div className="flex flex-col gap-4">
                    <a
                        href={`${API_BASE}/payments/orders/${orderId}/receipt`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-accent text-white px-8 py-4 rounded-2xl font-bold text-xl shadow-lg hover:scale-105 transition-transform flex items-center justify-center gap-3"
                    >
                        <Printer size={24} />
                        Get Receipt (PDF)
                    </a>

                    <button
                        onClick={() => router.push('/')}
                        className="mt-4 bg-primary/10 text-primary px-8 py-3 rounded-full font-bold hover:bg-primary/20 transition-colors"
                    >
                        Start New Order
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-muted/30 p-6">
            <div className="max-w-4xl mx-auto bg-white rounded-3xl shadow-xl overflow-hidden min-h-[80vh] flex flex-col">
                {/* Header */}
                <div className="p-6 border-b border-border flex items-center">
                    <button onClick={() => router.back()} className="p-2 hover:bg-muted rounded-full mr-4">
                        <ArrowLeft />
                    </button>
                    <h1 className="text-2xl font-bold">Checkout</h1>
                </div>

                <div className="flex-1 flex flex-col md:flex-row">
                    {/* Left: Summary */}
                    <div className="flex-1 p-8 border-r border-border">
                        <h2 className="text-xl font-bold mb-6">Order Summary</h2>
                        <div className="space-y-4">
                            {items.map(item => (
                                <div key={item.product.id} className="flex justify-between items-center">
                                    <div className="flex items-center gap-2">
                                        <div className="bg-primary/10 text-primary w-8 h-8 flex items-center justify-center rounded-full font-bold text-sm">
                                            {item.quantity}x
                                        </div>
                                        <span className="font-medium">{item.product.name}</span>
                                    </div>
                                    <span className="font-bold">{formatCurrency(item.product.price * item.quantity)}</span>
                                </div>
                            ))}
                        </div>

                        <div className="mt-8 pt-6 border-t border-border flex justify-between items-center text-2xl font-bold">
                            <span>Total</span>
                            <span className="text-primary">{formatCurrency(total())}</span>
                        </div>
                    </div>

                    {/* Right: Payment Action */}
                    <div className="flex-1 p-8 bg-muted/20 flex flex-col items-center justify-center">
                        {state === 'SUMMARY' && (
                            <div className="w-full max-w-sm space-y-6">
                                <div className="bg-white p-6 rounded-2xl shadow-sm border border-border">
                                    <h3 className="font-bold mb-2">Payment Method</h3>
                                    <div className="flex items-center gap-3 p-3 bg-primary/5 rounded-xl border border-primary/20">
                                        <div className="w-10 h-10 bg-red-600 rounded flex items-center justify-center text-white font-bold text-xs">ABA</div>
                                        <span className="font-bold">KHQR PayWay</span>
                                    </div>
                                </div>

                                <button
                                    onClick={handlePay}
                                    className="w-full bg-primary text-primary-foreground text-xl font-bold py-4 rounded-2xl shadow-lg hover:brightness-110 active:scale-95 transition-all"
                                >
                                    Pay {formatCurrency(total())}
                                </button>
                            </div>
                        )}

                        {state === 'PROCESSING' && (
                            <div className="text-center">
                                <Loader2 className="animate-spin text-primary mx-auto mb-4" size={48} />
                                <p className="text-lg font-medium">Generating KHQR...</p>
                            </div>
                        )}

                        {state === 'AWAITING_PAYMENT' && qrData && (
                            <div className="text-center w-full">
                                <h3 className="text-xl font-bold mb-6">Scan to Pay</h3>
                                <div className="bg-white p-4 rounded-xl shadow-sm border border-border inline-block relative">
                                    {/* ABA returns qr_image as a specific URL or base64. 
                                Looking at aba_payway.py: `document.getElementById("qr").src = data.qrImage;`
                                So the field in response is `qrImage`.
                            */}
                                    {qrData.qrImage ? (
                                        <img
                                            src={qrData.qrImage}
                                            alt="KHQR"
                                            className="w-full h-auto max-w-[300px] object-contain rounded-xl"
                                        />
                                    ) : (
                                        <div className="w-64 h-64 bg-gray-200 flex items-center justify-center">
                                            QR Error
                                        </div>
                                    )}
                                </div>
                                <p className="mt-6 text-muted-foreground animate-pulse">Waiting for payment confirmation...</p>

                                <div className="mt-4 text-xs text-muted-foreground">
                                    Order: {orderNumber}
                                </div>
                                <button
                                    onClick={async () => {
                                        try {
                                            const res = await fetch(`${API_BASE}/payments/orders/${orderId}/mock-pay`, {
                                                method: 'POST'
                                            });
                                            if (res.ok) {
                                                setState('SUCCESS');
                                                clearCart();
                                            }
                                        } catch (e) {
                                            console.error('Mock pay error:', e);
                                        }
                                    }}
                                    className="mt-6 w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-xl transition-colors"
                                >
                                    Simulate Payment Success
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

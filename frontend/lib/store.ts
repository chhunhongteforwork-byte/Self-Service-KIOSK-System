import { create } from 'zustand';
import { Product, CartItem } from '@/types';

interface CartState {
    items: CartItem[];
    isOpen: boolean;
    addToCart: (product: Product) => void;
    removeFromCart: (productId: number) => void;
    updateQuantity: (productId: number, delta: number) => void;
    clearCart: () => void;
    toggleCart: () => void;
    total: () => number;
}

export const useCartStore = create<CartState>((set, get) => ({
    items: [],
    isOpen: false,
    addToCart: (product) => set((state) => {
        const existing = state.items.find(i => i.product.id === product.id);
        if (existing) {
            return {
                items: state.items.map(i =>
                    i.product.id === product.id
                        ? { ...i, quantity: i.quantity + 1 }
                        : i
                ),
                isOpen: true
            };
        }
        return {
            items: [...state.items, { product, quantity: 1 }],
            isOpen: true
        };
    }),
    removeFromCart: (productId) => set((state) => ({
        items: state.items.filter(i => i.product.id !== productId)
    })),
    updateQuantity: (productId, delta) => set((state) => ({
        items: state.items.map(i => {
            if (i.product.id === productId) {
                const newQty = Math.max(0, i.quantity + delta);
                return { ...i, quantity: newQty };
            }
            return i;
        }).filter(i => i.quantity > 0)
    })),
    clearCart: () => set({ items: [] }),
    toggleCart: () => set((state) => ({ isOpen: !state.isOpen })),
    total: () => {
        const state = get();
        return state.items.reduce((sum, item) => sum + (item.product.price * item.quantity), 0);
    }
}));

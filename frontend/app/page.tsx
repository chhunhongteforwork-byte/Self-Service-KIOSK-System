"use client";

import { useState, useEffect } from "react";
import AttractScreen from "@/components/AttractScreen";
import CategoryTabs from "@/components/CategoryTabs";
import ProductCard from "@/components/ProductCard";
import CartDrawer from "@/components/CartDrawer";
import { useIdle } from "@/lib/useIdle";
import { Category, Product } from "@/types";
import { API_BASE } from "@/lib/utils";
import { ShoppingBag } from "lucide-react";
import { useCartStore } from "@/lib/store";

export default function Home() {
  const { isIdle, setIsIdle } = useIdle(45000); // 45s idle timeout
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [activeCategory, setActiveCategory] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toggleCart, total, items } = useCartStore();

  useEffect(() => {
    async function fetchData() {
      try {
        const [catsRes, prodsRes] = await Promise.all([
          fetch(`${API_BASE}/store/categories`),
          fetch(`${API_BASE}/store/products`)
        ]);

        const cats = await catsRes.json();
        const prods = await prodsRes.json();

        setCategories(cats);
        setProducts(prods);

        if (cats.length > 0) {
          setActiveCategory(cats[0].id);
        }
      } catch (error) {
        console.error("Failed to fetch data", error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, []);

  const filteredProducts = activeCategory
    ? products.filter(p => p.category_id === activeCategory)
    : products;

  if (isIdle) {
    return <AttractScreen onStart={() => setIsIdle(false)} />;
  }

  return (
    <div className="min-h-screen pb-24">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-md border-b border-border shadow-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-black text-primary flex items-center gap-2">
            🐰 Rabbit Kiosk
          </h1>
          <button
            onClick={toggleCart}
            className="relative bg-white p-3 rounded-full shadow-sm hover:shadow-md transition-all active:scale-95"
          >
            <ShoppingBag className="text-primary" />
            {items.length > 0 && (
              <span className="absolute -top-1 -right-1 bg-accent text-white rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold animate-bounce">
                {items.reduce((a, b) => a + b.quantity, 0)}
              </span>
            )}
          </button>
        </div>

        {/* Categories (Sticky below header) */}
        <div className="container mx-auto px-4 pb-4">
          <CategoryTabs
            categories={categories}
            activeId={activeCategory}
            onSelect={setActiveCategory}
          />
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {isLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="aspect-square bg-muted animate-pulse rounded-2xl" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {filteredProducts.map(product => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </main>

      <CartDrawer />
    </div>
  );
}

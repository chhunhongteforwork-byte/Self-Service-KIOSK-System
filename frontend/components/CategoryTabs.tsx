"use client";

import { Category } from "@/types";
import { cn } from "@/lib/utils"; // We need clsx helper, I used cn in imports but didn't define it in utils yet!

interface CategoryTabsProps {
    categories: Category[];
    activeId: number | null;
    onSelect: (id: number) => void;
}

export default function CategoryTabs({ categories, activeId, onSelect }: CategoryTabsProps) {
    return (
        <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide">
            {categories.map((cat) => (
                <button
                    key={cat.id}
                    onClick={() => onSelect(cat.id)}
                    className={cn(
                        "flex-none px-6 py-3 rounded-full text-lg font-bold transition-all border-2",
                        activeId === cat.id
                            ? "bg-primary text-primary-foreground border-primary"
                            : "bg-white text-muted-foreground border-transparent hover:border-primary/50"
                    )}
                >
                    {cat.name}
                </button>
            ))}
        </div>
    );
}

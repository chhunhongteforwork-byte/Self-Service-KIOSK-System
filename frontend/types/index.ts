export interface Category {
    id: number;
    name: string;
    icon_url?: string | null;
}

export interface Product {
    id: number;
    category_id: number;
    name: string;
    price: number;
    description?: string;
    image_url?: string | null;
}

export interface CartItem {
    product: Product;
    quantity: number;
}

import { useEffect, useState, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useAuth, useUser } from '@/store/auth-store';
import AdminNav from '@/components/nav/AdminNav';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
    UtensilsCrossed,
    Plus,
    Coffee,
    Sun,
    Moon,
    RefreshCw,
    Trash2,
    Edit,
    Save,
    X
} from 'lucide-react';
import { API_CONFIG, API_ENDPOINTS } from '@/config/api';
import toast from 'react-hot-toast';

interface MenuItem {
    id: string;
    name: string;
    description?: string;
    price: number;
    slot: string;
    category: string;
    is_available: boolean;
}

const SLOTS = ['breakfast', 'lunch', 'snacks', 'dinner'];
const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

const slotIcons: Record<string, React.ReactNode> = {
    breakfast: <Coffee className="h-4 w-4" />,
    lunch: <Sun className="h-4 w-4" />,
    snacks: <UtensilsCrossed className="h-4 w-4" />,
    dinner: <Moon className="h-4 w-4" />,
};

export default function AdminMessPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading } = useAuth();
    const { user } = useUser();

    const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAddForm, setShowAddForm] = useState(false);
    const [editingItem, setEditingItem] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState('menu');

    // Form state
    const [form, setForm] = useState({
        name: '',
        description: '',
        price: '',
        slot: 'lunch',
        category: 'main',
    });

    // Auth guard
    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.replace('/auth/login?redirect=/admin/mess');
        }
        if (!isLoading && isAuthenticated && user?.role !== 'admin') {
            router.replace('/tenant');
        }
    }, [isLoading, isAuthenticated, user?.role, router]);

    // Fetch menu items
    const fetchMenu = useCallback(async () => {
        try {
            const res = await fetch(`${API_CONFIG.BASE_URL}${API_ENDPOINTS.MESS.MENU}/items`);
            if (res.ok) {
                const data = await res.json();
                setMenuItems(data.items || data || []);
            }
        } catch (error) {
            console.error('Failed to fetch menu:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchMenu();
    }, [fetchMenu]);

    const handleAddItem = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const token = localStorage.getItem('pgwallah_access_token');
            const res = await fetch(
                `${API_CONFIG.BASE_URL}${API_ENDPOINTS.MESS.MENU}/items`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(token ? { Authorization: `Bearer ${token}` } : {}),
                    },
                    body: JSON.stringify({
                        name: form.name,
                        description: form.description || null,
                        price: parseFloat(form.price),
                        slot: form.slot,
                        category: form.category,
                        is_available: true,
                    }),
                }
            );

            if (res.ok) {
                toast.success('Menu item added');
                setForm({ name: '', description: '', price: '', slot: 'lunch', category: 'main' });
                setShowAddForm(false);
                fetchMenu();
            } else {
                const error = await res.json();
                toast.error(error.detail || 'Failed to add item');
            }
        } catch (error) {
            toast.error('Failed to add item');
        }
    };

    const handleDeleteItem = async (id: string) => {
        if (!confirm('Delete this menu item?')) return;
        try {
            const token = localStorage.getItem('pgwallah_access_token');
            const res = await fetch(
                `${API_CONFIG.BASE_URL}${API_ENDPOINTS.MESS.MENU}/items/${id}`,
                {
                    method: 'DELETE',
                    headers: token ? { Authorization: `Bearer ${token}` } : {},
                }
            );

            if (res.ok) {
                toast.success('Item deleted');
                fetchMenu();
            } else {
                toast.error('Failed to delete item');
            }
        } catch (error) {
            toast.error('Failed to delete item');
        }
    };

    const handleSeedMenu = async () => {
        try {
            const token = localStorage.getItem('pgwallah_access_token');
            const res = await fetch(
                `${API_CONFIG.BASE_URL}${API_ENDPOINTS.MESS.MENU}/seed_default`,
                {
                    method: 'POST',
                    headers: token ? { Authorization: `Bearer ${token}` } : {},
                }
            );

            if (res.ok) {
                toast.success('Default menu seeded!');
                fetchMenu();
            } else {
                toast.error('Failed to seed menu');
            }
        } catch (error) {
            toast.error('Failed to seed menu');
        }
    };

    if (isLoading || !isAuthenticated || user?.role !== 'admin') {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    const itemsBySlot = SLOTS.reduce((acc, slot) => {
        acc[slot] = menuItems.filter(item => item.slot === slot);
        return acc;
    }, {} as Record<string, MenuItem[]>);

    return (
        <>
            <Head>
                <title>Mess Management • Admin • PGwallah</title>
            </Head>

            <AdminNav />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                            <UtensilsCrossed className="h-8 w-8" />
                            Mess Management
                        </h1>
                        <p className="mt-1 text-muted-foreground">
                            Manage menu items and weekly schedule
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline" onClick={handleSeedMenu}>
                            Seed Default Menu
                        </Button>
                        <Button onClick={() => setShowAddForm(!showAddForm)}>
                            <Plus className="mr-2 h-4 w-4" />
                            Add Item
                        </Button>
                    </div>
                </div>

                {/* Add Item Form */}
                {showAddForm && (
                    <Card className="mb-6">
                        <CardHeader>
                            <CardTitle className="text-lg">Add Menu Item</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleAddItem} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <Label htmlFor="name">Name *</Label>
                                    <Input
                                        id="name"
                                        value={form.name}
                                        onChange={(e) => setForm({ ...form, name: e.target.value })}
                                        required
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="price">Price (₹) *</Label>
                                    <Input
                                        id="price"
                                        type="number"
                                        value={form.price}
                                        onChange={(e) => setForm({ ...form, price: e.target.value })}
                                        required
                                        min="0"
                                        step="0.5"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="slot">Slot *</Label>
                                    <select
                                        id="slot"
                                        value={form.slot}
                                        onChange={(e) => setForm({ ...form, slot: e.target.value })}
                                        className="w-full px-3 py-2 border rounded-md"
                                    >
                                        {SLOTS.map(slot => (
                                            <option key={slot} value={slot} className="capitalize">
                                                {slot.charAt(0).toUpperCase() + slot.slice(1)}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div className="md:col-span-2">
                                    <Label htmlFor="description">Description</Label>
                                    <Input
                                        id="description"
                                        value={form.description}
                                        onChange={(e) => setForm({ ...form, description: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="category">Category</Label>
                                    <select
                                        id="category"
                                        value={form.category}
                                        onChange={(e) => setForm({ ...form, category: e.target.value })}
                                        className="w-full px-3 py-2 border rounded-md"
                                    >
                                        <option value="main">Main</option>
                                        <option value="side">Side</option>
                                        <option value="dessert">Dessert</option>
                                        <option value="beverage">Beverage</option>
                                    </select>
                                </div>
                                <div className="md:col-span-3 flex justify-end gap-2">
                                    <Button type="button" variant="outline" onClick={() => setShowAddForm(false)}>
                                        Cancel
                                    </Button>
                                    <Button type="submit">
                                        <Save className="mr-2 h-4 w-4" />
                                        Save Item
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                )}

                {/* Menu Items by Slot */}
                {loading ? (
                    <div className="text-center py-12">
                        <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2 text-muted-foreground" />
                        <p className="text-muted-foreground">Loading menu...</p>
                    </div>
                ) : menuItems.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {SLOTS.map(slot => (
                            <Card key={slot}>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2 capitalize">
                                        {slotIcons[slot]}
                                        {slot}
                                        <Badge variant="secondary" className="ml-auto">
                                            {(itemsBySlot[slot] ?? []).length} items
                                        </Badge>
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    {(itemsBySlot[slot] ?? []).length > 0 ? (
                                        <div className="divide-y">
                                            {(itemsBySlot[slot] ?? []).map(item => (
                                                <div key={item.id} className="py-3 flex items-center justify-between">
                                                    <div>
                                                        <p className="font-medium">{item.name}</p>
                                                        {item.description && (
                                                            <p className="text-xs text-muted-foreground">{item.description}</p>
                                                        )}
                                                        <div className="flex gap-2 mt-1">
                                                            <Badge variant="outline">₹{item.price}</Badge>
                                                            <Badge variant={item.is_available ? 'default' : 'secondary'}>
                                                                {item.is_available ? 'Available' : 'Unavailable'}
                                                            </Badge>
                                                        </div>
                                                    </div>
                                                    <Button
                                                        size="icon"
                                                        variant="ghost"
                                                        className="text-red-500 hover:text-red-700 hover:bg-red-50"
                                                        onClick={() => handleDeleteItem(item.id)}
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="text-sm text-muted-foreground text-center py-4">
                                            No items for {slot}. Add some!
                                        </p>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : (
                    <Card>
                        <CardContent className="py-12 text-center">
                            <UtensilsCrossed className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                            <h3 className="text-lg font-medium mb-2">No menu items</h3>
                            <p className="text-muted-foreground text-sm mb-4">
                                Start by adding items or seed the default menu
                            </p>
                            <Button onClick={handleSeedMenu}>
                                Seed Default Menu
                            </Button>
                        </CardContent>
                    </Card>
                )}
            </main>
        </>
    );
}

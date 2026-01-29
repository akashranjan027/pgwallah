import { useEffect, useState, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useAuth, useUser } from '@/store/auth-store';
import AdminNav from '@/components/nav/AdminNav';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
    ChefHat,
    Clock,
    CheckCircle,
    XCircle,
    RefreshCw,
    Package,
    User,
    Timer,
    TrendingUp
} from 'lucide-react';
import { API_CONFIG, API_ENDPOINTS } from '@/config/api';
import toast from 'react-hot-toast';

interface OrderItem {
    id: string;
    menu_item_id: string;
    menu_item_name: string;
    quantity: number;
    unit_price: number;
    total_price: number;
}

interface Order {
    id: string;
    order_number: string;
    tenant_id: string;
    status: string;
    payment_status: string;
    total_amount: number;
    items: OrderItem[];
    delivery_address?: string;
    delivery_instructions?: string;
    customer_notes?: string;
    created_at: string;
    updated_at: string;
}

const statusConfig: Record<string, { color: string; icon: React.ReactNode }> = {
    pending: { color: 'bg-yellow-100 text-yellow-800', icon: <Clock className="h-4 w-4" /> },
    confirmed: { color: 'bg-blue-100 text-blue-800', icon: <CheckCircle className="h-4 w-4" /> },
    preparing: { color: 'bg-orange-100 text-orange-800', icon: <ChefHat className="h-4 w-4" /> },
    ready: { color: 'bg-green-100 text-green-800', icon: <Package className="h-4 w-4" /> },
    delivered: { color: 'bg-gray-100 text-gray-800', icon: <CheckCircle className="h-4 w-4" /> },
    cancelled: { color: 'bg-red-100 text-red-800', icon: <XCircle className="h-4 w-4" /> },
};

const STATUS_FLOW = ['pending', 'confirmed', 'preparing', 'ready', 'delivered'];

export default function AdminOrdersPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading } = useAuth();
    const { user } = useUser();

    const [orders, setOrders] = useState<Order[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<string>('pending');

    // Auth guard
    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.replace('/auth/login?redirect=/admin/orders');
        }
        if (!isLoading && isAuthenticated && user?.role !== 'admin') {
            router.replace('/tenant');
        }
    }, [isLoading, isAuthenticated, user?.role, router]);

    // Fetch orders
    const fetchOrders = useCallback(async () => {
        try {
            const token = localStorage.getItem('pgwallah_access_token');
            const res = await fetch(
                `${API_CONFIG.BASE_URL}${API_ENDPOINTS.ORDERS.KITCHEN}`,
                { headers: token ? { Authorization: `Bearer ${token}` } : {} }
            );
            if (res.ok) {
                const data = await res.json();
                setOrders(data.orders || []);
            }
        } catch (error) {
            console.error('Failed to fetch orders:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchOrders();
        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchOrders, 30000);
        return () => clearInterval(interval);
    }, [fetchOrders]);

    const updateOrderStatus = async (orderId: string, newStatus: string) => {
        try {
            const token = localStorage.getItem('pgwallah_access_token');
            const res = await fetch(
                `${API_CONFIG.BASE_URL}${API_ENDPOINTS.ORDERS.UPDATE_STATUS(orderId)}`,
                {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(token ? { Authorization: `Bearer ${token}` } : {}),
                    },
                    body: JSON.stringify({ status: newStatus }),
                }
            );

            if (res.ok) {
                toast.success(`Order updated to ${newStatus}`);
                fetchOrders();
            } else {
                toast.error('Failed to update order');
            }
        } catch (error) {
            toast.error('Failed to update order');
        }
    };

    if (isLoading || !isAuthenticated || user?.role !== 'admin') {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    const filteredOrders = activeTab === 'all'
        ? orders
        : orders.filter(o => o.status === activeTab);

    const orderCounts = {
        pending: orders.filter(o => o.status === 'pending').length,
        preparing: orders.filter(o => o.status === 'preparing').length,
        ready: orders.filter(o => o.status === 'ready').length,
        delivered: orders.filter(o => o.status === 'delivered').length,
    };

    return (
        <>
            <Head>
                <title>Kitchen Orders • Admin • PGwallah</title>
            </Head>

            <AdminNav />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                            <ChefHat className="h-8 w-8" />
                            Kitchen Dashboard
                        </h1>
                        <p className="mt-1 text-muted-foreground">
                            Manage food orders from tenants
                        </p>
                    </div>
                    <Button variant="outline" onClick={fetchOrders}>
                        <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <Card className="bg-yellow-50 border-yellow-200">
                        <CardContent className="pt-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-yellow-800">Pending</p>
                                    <p className="text-2xl font-bold text-yellow-900">{orderCounts.pending}</p>
                                </div>
                                <Clock className="h-8 w-8 text-yellow-600" />
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="bg-orange-50 border-orange-200">
                        <CardContent className="pt-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-orange-800">Preparing</p>
                                    <p className="text-2xl font-bold text-orange-900">{orderCounts.preparing}</p>
                                </div>
                                <ChefHat className="h-8 w-8 text-orange-600" />
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="bg-green-50 border-green-200">
                        <CardContent className="pt-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-green-800">Ready</p>
                                    <p className="text-2xl font-bold text-green-900">{orderCounts.ready}</p>
                                </div>
                                <Package className="h-8 w-8 text-green-600" />
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="bg-gray-50 border-gray-200">
                        <CardContent className="pt-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-800">Today's Delivered</p>
                                    <p className="text-2xl font-bold text-gray-900">{orderCounts.delivered}</p>
                                </div>
                                <TrendingUp className="h-8 w-8 text-gray-600" />
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
                    {['pending', 'confirmed', 'preparing', 'ready', 'delivered', 'all'].map(tab => (
                        <Button
                            key={tab}
                            variant={activeTab === tab ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setActiveTab(tab)}
                        >
                            <span className="capitalize">{tab}</span>
                            {tab !== 'all' && orderCounts[tab as keyof typeof orderCounts] > 0 && (
                                <Badge variant="secondary" className="ml-2">
                                    {orderCounts[tab as keyof typeof orderCounts]}
                                </Badge>
                            )}
                        </Button>
                    ))}
                </div>

                {/* Orders Grid */}
                {loading ? (
                    <div className="text-center py-12">
                        <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2 text-muted-foreground" />
                        <p className="text-muted-foreground">Loading orders...</p>
                    </div>
                ) : filteredOrders.length > 0 ? (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {filteredOrders.map(order => (
                            <Card key={order.id} className="overflow-hidden">
                                <CardHeader className="pb-2 bg-muted/50">
                                    <div className="flex items-center justify-between">
                                        <CardTitle className="text-lg">#{order.order_number}</CardTitle>
                                        <Badge className={statusConfig[order.status]?.color || 'bg-gray-100'}>
                                            {statusConfig[order.status]?.icon}
                                            <span className="ml-1 capitalize">{order.status}</span>
                                        </Badge>
                                    </div>
                                    <CardDescription className="flex items-center gap-2">
                                        <Timer className="h-3 w-3" />
                                        {new Date(order.created_at).toLocaleTimeString()}
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="pt-4">
                                    {/* Items */}
                                    <div className="space-y-2 mb-4">
                                        {order.items?.map((item, idx) => (
                                            <div key={idx} className="flex justify-between text-sm">
                                                <span>
                                                    {item.quantity}x {item.menu_item_name}
                                                </span>
                                                <span className="text-muted-foreground">₹{item.total_price}</span>
                                            </div>
                                        ))}
                                        <div className="flex justify-between font-semibold pt-2 border-t">
                                            <span>Total</span>
                                            <span>₹{order.total_amount}</span>
                                        </div>
                                    </div>

                                    {/* Notes */}
                                    {(order.delivery_address || order.customer_notes) && (
                                        <div className="text-xs text-muted-foreground mb-4 p-2 bg-muted rounded">
                                            {order.delivery_address && <p>📍 {order.delivery_address}</p>}
                                            {order.customer_notes && <p>📝 {order.customer_notes}</p>}
                                        </div>
                                    )}

                                    {/* Action Buttons */}
                                    {order.status !== 'delivered' && order.status !== 'cancelled' && (
                                        <div className="flex gap-2">
                                            {STATUS_FLOW.indexOf(order.status) < STATUS_FLOW.length - 1 && (() => {
                                                const currentIndex = STATUS_FLOW.indexOf(order.status);
                                                const nextStatus = STATUS_FLOW[currentIndex + 1] ?? 'delivered';
                                                return (
                                                    <Button
                                                        size="sm"
                                                        className="flex-1"
                                                        onClick={() => updateOrderStatus(order.id, nextStatus)}
                                                    >
                                                        Move to {nextStatus}
                                                    </Button>
                                                );
                                            })()}
                                            {order.status === 'pending' && (
                                                <Button
                                                    size="sm"
                                                    variant="destructive"
                                                    onClick={() => updateOrderStatus(order.id, 'cancelled')}
                                                >
                                                    Cancel
                                                </Button>
                                            )}
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : (
                    <Card>
                        <CardContent className="py-12 text-center">
                            <ChefHat className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                            <h3 className="text-lg font-medium mb-2">No orders</h3>
                            <p className="text-muted-foreground text-sm">
                                {activeTab === 'all'
                                    ? "No orders yet today"
                                    : `No ${activeTab} orders`}
                            </p>
                        </CardContent>
                    </Card>
                )}
            </main>
        </>
    );
}

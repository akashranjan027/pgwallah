import { useEffect, useMemo, useState, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import TenantNav from '@/components/nav/TenantNav';
import { useAuth, useUser } from '@/store/auth-store';
import { toast } from 'react-hot-toast';
import { apiClient } from '@/lib/api-client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Search, RefreshCw, Utensils, Ticket, ShoppingBag, XCircle } from 'lucide-react';

type OrderItemInput = {
  menu_item_id: string;
  quantity: number;
};

type OrderRecord = {
  id: string;
  status: string;
  total_amount?: number;
  created_at?: string;
  items?: Array<{
    menu_item_id: string;
    quantity: number;
  }>;
};

type MenuItem = {
  id: string;
  name: string;
  description?: string;
  price: number;
  slot?: 'breakfast' | 'lunch' | 'snacks' | 'dinner';
  is_available?: boolean;
};

type Coupon = {
  id: string;
  slot?: 'breakfast' | 'lunch' | 'snacks' | 'dinner';
  for_date?: string;
  used?: boolean;
};

function localYMD(d = new Date()): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export default function TenantOrdersPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, getProfile } = useAuth();
  const { user } = useUser();

  // UI State
  const [activeTab, setActiveTab] = useState<'place' | 'history'>('place');

  // Place Order form state
  const [menuItemId, setMenuItemId] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [couponId, setCouponId] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Orders list state
  const [orders, setOrders] = useState<OrderRecord[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(false);

  // Menu state
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [menuLoading, setMenuLoading] = useState(false);
  const [menuSearch, setMenuSearch] = useState('');

  // Coupons state
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [couponsLoading, setCouponsLoading] = useState(false);

  // Ensure profile is loaded (guards downstream API calls)
  useEffect(() => {
    const init = async () => {
      try {
        await getProfile();
      } catch {
        // handled by store
      }
    };
    init();
  }, [getProfile]);

  // Redirect unauthenticated users
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/auth/login');
    }
  }, [isLoading, isAuthenticated, router]);

  const tenantId = useMemo(() => user?.id as string | undefined, [user]);

  // Load orders when opening the history tab
  useEffect(() => {
    const load = async () => {
      if (!isAuthenticated || !tenantId || activeTab !== 'history') return;
      setOrdersLoading(true);
      try {
        const data = await apiClient.listOrders({ tenant_id: tenantId, limit: 20, offset: 0 });
        setOrders((data as OrderRecord[]) || []);
      } catch (err: any) {
        toast.error(err?.message || 'Failed to load orders');
      } finally {
        setOrdersLoading(false);
      }
    };
    load();
  }, [activeTab, isAuthenticated, tenantId]);

  // Load menu when on "Place Order" tab
  const loadMenu = useCallback(async () => {
    setMenuLoading(true);
    try {
      const data = await apiClient.getMessMenuItems();
      setMenuItems((data as MenuItem[]) || []);
      if (!data || data.length === 0) {
        toast('No menu items found. You can seed defaults.', { icon: 'ℹ️' });
      } else {
        toast.success('Menu loaded');
      }
    } catch (err: any) {
      toast.error(err?.message || 'Failed to load menu');
    } finally {
      setMenuLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'place') {
      loadMenu().catch(() => { });
    }
  }, [activeTab, loadMenu]);

  const seedDefaultMenu = async () => {
    setMenuLoading(true);
    try {
      await apiClient.reseedDefaultMenu();
      toast.success('Default weekly menu seeded');
      await loadMenu();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to seed default menu');
    } finally {
      setMenuLoading(false);
    }
  };

  const filteredMenu = useMemo(() => {
    const q = menuSearch.trim().toLowerCase();
    if (!q) return menuItems;
    return menuItems.filter((m) => {
      return (
        m.name.toLowerCase().includes(q) ||
        (m.description || '').toLowerCase().includes(q) ||
        (m.slot || '').toLowerCase().includes(q)
      );
    });
  }, [menuSearch, menuItems]);

  // Coupons helpers
  const loadCoupons = useCallback(async () => {
    if (!tenantId) return;
    setCouponsLoading(true);
    try {
      const data = await apiClient.listCoupons({
        tenant_id: tenantId,
        for_date: localYMD(),
        include_used: true,
      });
      setCoupons((data as Coupon[]) || []);
      if (!data || data.length === 0) {
        toast('No coupons for today', { icon: 'ℹ️' });
      }
    } catch (err: any) {
      toast.error(err?.message || 'Failed to load coupons');
    } finally {
      setCouponsLoading(false);
    }
  }, [tenantId]);

  const issueTodayCoupons = useCallback(async () => {
    if (!tenantId) return;
    setCouponsLoading(true);
    try {
      // Explicitly issue 4 default slots as requested
      await apiClient.issueCoupons({
        tenant_id: tenantId,
        for_date: localYMD(),
        slots: ['breakfast', 'lunch', 'snacks', 'dinner'],
      });
      toast.success('Issued today’s 4 meal coupons');
      await loadCoupons();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to issue coupons');
    } finally {
      setCouponsLoading(false);
    }
  }, [tenantId, loadCoupons]);

  // Also load coupons when entering Place tab (so you can pick one)
  useEffect(() => {
    if (activeTab === 'place') {
      loadCoupons().catch(() => { });
    }
  }, [activeTab, loadCoupons]);

  const onCreateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tenantId) {
      toast.error('Missing tenant id');
      return;
    }
    if (!menuItemId) {
      toast.error('Please select a Menu Item');
      return;
    }
    if (quantity <= 0) {
      toast.error('Quantity must be at least 1');
      return;
    }
    setSubmitting(true);
    try {
      const base = {
        tenant_id: tenantId,
        items: [{ menu_item_id: menuItemId, quantity } as OrderItemInput],
      };
      // With exactOptionalPropertyTypes, omit optional keys unless present
      const payload =
        couponId && couponId.trim().length > 0 ? { ...base, coupon_id: couponId.trim() } : base;

      const result = await apiClient.createOrder(payload as any);
      toast.success('Order placed');

      // switch to history and refresh/append
      setActiveTab('history');

      if (result?.id) {
        setOrders((prev) => [
          {
            id: result.id,
            status: result.status || 'created',
            created_at: result.created_at,
            total_amount: result.total_amount,
          },
          ...prev,
        ]);
      } else if (tenantId) {
        const data = await apiClient.listOrders({ tenant_id: tenantId, limit: 20, offset: 0 });
        setOrders((data as OrderRecord[]) || []);
      }

      // reset form fields (keep menu list)
      setQuantity(1);
      // keep couponId so user sees it was used; they can clear it manually
    } catch (err: any) {
      toast.error(err?.message || 'Failed to place order');
    } finally {
      setSubmitting(false);
    }
  };

  const onCancelOrder = async (orderId: string) => {
    try {
      await apiClient.cancelOrder(orderId);
      toast.success('Order cancelled');
      setOrders((prev) => prev.map((o) => (o.id === orderId ? { ...o, status: 'cancelled' } : o)));
    } catch (err: any) {
      toast.error(err?.message || 'Failed to cancel order');
    }
  };

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Tenant • Orders</title>
      </Head>

      <div className="min-h-screen bg-muted/50">
        <TenantNav />

        <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-6">
            <h1 className="text-3xl font-bold tracking-tight">Food Orders</h1>
            <p className="mt-1 text-muted-foreground">
              Place new orders and track status from the mess kitchen.
            </p>
          </div>

          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'place' | 'history')} className="space-y-6">
            <TabsList>
              <TabsTrigger value="place">Place Order</TabsTrigger>
              <TabsTrigger value="history">My Orders</TabsTrigger>
            </TabsList>

            {/* Place Order */}
            <TabsContent value="place" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left: Menu Picker */}
                <div className="lg:col-span-2 space-y-6">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <div className="space-y-1">
                        <CardTitle>Menu</CardTitle>
                        <CardDescription>Select items to order.</CardDescription>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm" onClick={loadMenu} disabled={menuLoading}>
                          <RefreshCw className={`mr-2 h-4 w-4 ${menuLoading ? 'animate-spin' : ''}`} />
                          Reload
                        </Button>
                        <Button size="sm" onClick={seedDefaultMenu} disabled={menuLoading}>
                          Seed Defaults
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="relative mb-4">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                          placeholder="Search menu by name, slot..."
                          value={menuSearch}
                          onChange={(e) => setMenuSearch(e.target.value)}
                          className="pl-8"
                        />
                      </div>

                      {menuLoading ? (
                        <div className="flex justify-center py-8 text-muted-foreground">
                          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mr-2"></div>
                          Loading menu...
                        </div>
                      ) : filteredMenu.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground border-2 border-dashed rounded-lg">
                          No menu items found. Click "Seed Defaults".
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {filteredMenu.map((m) => {
                            const selected = menuItemId === m.id;
                            return (
                              <div
                                key={m.id}
                                onClick={() => {
                                  setMenuItemId(m.id);
                                  if (quantity <= 0) setQuantity(1);
                                }}
                                className={`
                                  cursor-pointer rounded-lg border p-4 transition-all hover:bg-muted/50
                                  ${selected ? 'border-primary ring-1 ring-primary bg-primary/5' : 'border-border'}
                                `}
                              >
                                <div className="flex items-center justify-between mb-1">
                                  <div className="font-semibold">{m.name}</div>
                                  <div className="font-mono text-sm">₹{m.price}</div>
                                </div>
                                <div className="text-sm text-muted-foreground line-clamp-2 mb-2">
                                  {m.description || 'No description'}
                                </div>
                                <div className="flex items-center gap-2">
                                  {m.slot && <Badge variant="secondary">{m.slot}</Badge>}
                                  {m.is_available === false ? (
                                    <Badge variant="destructive">Unavailable</Badge>
                                  ) : (
                                    <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">Available</Badge>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>

                {/* Right: Order Form + Coupons */}
                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Order Details</CardTitle>
                      <CardDescription>Review and place your order.</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <form onSubmit={onCreateOrder} className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="menu_item_id">Selected Item ID</Label>
                          <Input
                            id="menu_item_id"
                            value={menuItemId}
                            onChange={(e) => setMenuItemId(e.target.value)}
                            placeholder="Select from menu..."
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="quantity">Quantity</Label>
                          <Input
                            id="quantity"
                            type="number"
                            min={1}
                            value={quantity}
                            onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value || '1', 10)))}
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="coupon_id">Coupon ID (Optional)</Label>
                          <Input
                            id="coupon_id"
                            value={couponId}
                            onChange={(e) => setCouponId(e.target.value)}
                            placeholder="Select a coupon below..."
                          />
                        </div>

                        <Button type="submit" className="w-full" disabled={submitting}>
                          {submitting ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                              Placing...
                            </>
                          ) : (
                            <>
                              <ShoppingBag className="mr-2 h-4 w-4" />
                              Place Order
                            </>
                          )}
                        </Button>
                      </form>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-base">Today's Coupons</CardTitle>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" onClick={loadCoupons} title="Reload">
                          <RefreshCw className={`h-4 w-4 ${couponsLoading ? 'animate-spin' : ''}`} />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={issueTodayCoupons} title="Issue 4 Meals">
                          <Ticket className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {couponsLoading ? (
                        <div className="text-center py-4 text-sm text-muted-foreground">Loading...</div>
                      ) : coupons.length === 0 ? (
                        <div className="text-center py-4 text-sm text-muted-foreground border-2 border-dashed rounded-lg">
                          No coupons. Click ticket icon to issue.
                        </div>
                      ) : (
                        <div className="space-y-2 mt-2">
                          {coupons.map((c) => (
                            <div key={c.id} className="flex items-center justify-between p-2 border rounded-md bg-background">
                              <div className="flex items-center gap-2">
                                <Badge variant="secondary">{c.slot || 'meal'}</Badge>
                                <span className="text-xs font-mono text-muted-foreground truncate max-w-[80px]">{c.id}</span>
                              </div>
                              {c.used ? (
                                <Badge variant="outline" className="text-muted-foreground">Used</Badge>
                              ) : (
                                <Button size="sm" variant="ghost" className="h-6 text-xs" onClick={() => setCouponId(c.id)}>
                                  Use
                                </Button>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </div>
            </TabsContent>

            {/* History */}
            <TabsContent value="history">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <div className="space-y-1">
                    <CardTitle>Order History</CardTitle>
                    <CardDescription>Recent orders placed.</CardDescription>
                  </div>
                  <Button variant="outline" size="sm" onClick={async () => {
                    if (!tenantId) return;
                    setOrdersLoading(true);
                    try {
                      const data = await apiClient.listOrders({ tenant_id: tenantId, limit: 20, offset: 0 });
                      setOrders((data as OrderRecord[]) || []);
                      toast.success('Orders refreshed');
                    } catch (err: any) {
                      toast.error(err?.message || 'Refresh failed');
                    } finally {
                      setOrdersLoading(false);
                    }
                  }}>
                    <RefreshCw className={`mr-2 h-4 w-4 ${ordersLoading ? 'animate-spin' : ''}`} />
                    Refresh
                  </Button>
                </CardHeader>
                <CardContent>
                  {ordersLoading ? (
                    <div className="flex justify-center py-12 text-muted-foreground">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mr-2"></div>
                      Loading history...
                    </div>
                  ) : orders.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground border-2 border-dashed rounded-lg">
                      <ShoppingBag className="h-12 w-12 mb-4 opacity-20" />
                      <h3 className="text-lg font-medium">No Orders Yet</h3>
                      <p className="max-w-sm mt-2">Place your first order from the "Place Order" tab.</p>
                    </div>
                  ) : (
                    <div className="rounded-md border">
                      <table className="w-full text-sm text-left">
                        <thead className="bg-muted/50 text-muted-foreground font-medium">
                          <tr>
                            <th className="p-4">Order ID</th>
                            <th className="p-4">Status</th>
                            <th className="p-4">Total</th>
                            <th className="p-4">Created</th>
                            <th className="p-4 text-right">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {orders.map((o) => (
                            <tr key={o.id} className="hover:bg-muted/50 transition-colors">
                              <td className="p-4 font-mono text-xs">{o.id}</td>
                              <td className="p-4">
                                <Badge variant={o.status === 'cancelled' ? 'destructive' : 'secondary'}>
                                  {o.status}
                                </Badge>
                              </td>
                              <td className="p-4 font-medium">{o.total_amount != null ? `₹${o.total_amount}` : '—'}</td>
                              <td className="p-4 text-muted-foreground">{o.created_at ? new Date(o.created_at).toLocaleDateString() : '—'}</td>
                              <td className="p-4 text-right">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  disabled={['cancelled', 'delivered', 'completed'].includes(o.status)}
                                  onClick={() => onCancelOrder(o.id)}
                                  className="text-destructive hover:text-destructive hover:bg-destructive/10"
                                >
                                  Cancel
                                </Button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </>
  );
}
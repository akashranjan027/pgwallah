import { useEffect, useMemo, useState, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import TenantNav from '@/components/nav/TenantNav';
import { useAuth, useUser } from '@/store/auth-store';
import { toast } from 'react-hot-toast';
import { apiClient } from '@/lib/api-client';

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
      loadMenu().catch(() => {});
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
      loadCoupons().catch(() => {});
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
      <div className="min-h-screen grid place-items-center bg-gray-50">
        <div className="flex items-center space-x-3 text-gray-600">
          <div className="spinner-lg" />
          <span>Loading orders…</span>
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Tenant • Orders</title>
      </Head>

      <TenantNav />

      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Food Orders</h1>
          <p className="mt-1 text-gray-600">
            Place new orders and track status from the mess kitchen.
          </p>
        </div>

        {/* Tabs */}
        <div className="mb-4 flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('place')}
            className={[
              'inline-flex items-center rounded-md px-3 py-1.5 text-sm font-medium border',
              activeTab === 'place'
                ? 'bg-primary-600 text-white border-primary-600'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50',
            ].join(' ')}
          >
            Place Order
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('history')}
            className={[
              'inline-flex items-center rounded-md px-3 py-1.5 text-sm font-medium border',
              activeTab === 'history'
                ? 'bg-primary-600 text-white border-primary-600'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50',
            ].join(' ')}
          >
            My Orders
          </button>
        </div>

        {/* Place Order */}
        {activeTab === 'place' && (
          <section className="rounded-xl border border-gray-200 bg-white p-5">
            <div className="flex flex-col lg:flex-row gap-6">
              {/* Left: Menu Picker */}
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900">Menu</h2>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={loadMenu}
                      className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
                    >
                      {menuLoading ? 'Loading…' : 'Reload'}
                    </button>
                    <button
                      type="button"
                      onClick={seedDefaultMenu}
                      className="inline-flex items-center rounded-md bg-primary-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-700"
                    >
                      Seed Defaults
                    </button>
                  </div>
                </div>

                <div className="mt-3">
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Search menu by name, slot (breakfast/lunch/snacks/dinner)…"
                    value={menuSearch}
                    onChange={(e) => setMenuSearch(e.target.value)}
                  />
                </div>

                <div className="mt-4">
                  {menuLoading ? (
                    <div className="flex items-center text-gray-600">
                      <div className="spinner-sm mr-2" /> Loading menu…
                    </div>
                  ) : filteredMenu.length === 0 ? (
                    <div className="rounded-lg border border-dashed border-gray-300 p-6 text-sm text-gray-500">
                      No menu items found. Click “Seed Defaults” to populate a weekly menu.
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {filteredMenu.map((m) => {
                        const selected = menuItemId === m.id;
                        return (
                          <button
                            key={m.id}
                            type="button"
                            onClick={() => {
                              setMenuItemId(m.id);
                              if (quantity <= 0) setQuantity(1);
                            }}
                            className={[
                              'text-left rounded-lg border p-4 transition',
                              selected
                                ? 'border-primary-600 ring-2 ring-primary-200 bg-primary-50'
                                : 'border-gray-200 hover:bg-gray-50',
                            ].join(' ')}
                          >
                            <div className="flex items-center justify-between">
                              <div className="font-medium text-gray-900">{m.name}</div>
                              <div className="text-sm font-semibold text-gray-800">₹{m.price}</div>
                            </div>
                            <div className="mt-1 text-sm text-gray-600 line-clamp-2">
                              {m.description || '—'}
                            </div>
                            <div className="mt-2 flex items-center gap-2 text-xs">
                              {m.slot ? (
                                <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-gray-700">
                                  {m.slot}
                                </span>
                              ) : null}
                              {m.is_available === false ? (
                                <span className="inline-flex items-center rounded-md bg-error-100 px-2 py-0.5 text-error-700">
                                  Unavailable
                                </span>
                              ) : (
                                <span className="inline-flex items-center rounded-md bg-success-100 px-2 py-0.5 text-success-700">
                                  Available
                                </span>
                              )}
                              {selected ? (
                                <span className="inline-flex items-center rounded-md bg-primary-100 px-2 py-0.5 text-primary-700">
                                  Selected
                                </span>
                              ) : null}
                            </div>
                            <div className="mt-2 text-xs text-gray-400">ID: {m.id}</div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* Right: Order Form + Coupons */}
              <div className="w-full lg:w-96">
                <h2 className="text-lg font-semibold text-gray-900">Place Order</h2>
                <p className="mt-1 text-sm text-gray-600">
                  Select an item from the menu on the left, then set quantity and optional coupon.
                </p>

                <form className="mt-4 grid grid-cols-1 gap-4" onSubmit={onCreateOrder}>
                  <div>
                    <label className="form-label form-label-required" htmlFor="menu_item_id">
                      Selected Menu Item
                    </label>
                    <input
                      id="menu_item_id"
                      className="form-input"
                      type="text"
                      value={menuItemId}
                      onChange={(e) => setMenuItemId(e.target.value)}
                      placeholder="Select from menu or paste an item id"
                      required
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Pick one from the menu list or paste an ID.
                    </p>
                  </div>

                  <div>
                    <label className="form-label form-label-required" htmlFor="quantity">
                      Quantity
                    </label>
                    <input
                      id="quantity"
                      className="form-input"
                      type="number"
                      min={1}
                      value={quantity}
                      onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value || '1', 10)))}
                      required
                    />
                  </div>

                  <div>
                    <label className="form-label" htmlFor="coupon_id">
                      Coupon ID (optional)
                    </label>
                    <input
                      id="coupon_id"
                      className="form-input"
                      type="text"
                      placeholder="coupon_xyz (optional)"
                      value={couponId}
                      onChange={(e) => setCouponId(e.target.value)}
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Tip: Click a coupon below to auto-fill this field.
                    </p>
                  </div>

                  <div className="pt-2">
                    <button type="submit" disabled={submitting} className="btn btn-primary w-full">
                      {submitting ? (
                        <span className="inline-flex items-center justify-center">
                          <span className="spinner-sm mr-2" /> Placing...
                        </span>
                      ) : (
                        'Place Order'
                      )}
                    </button>
                  </div>
                </form>

                {/* Coupons block */}
                <div className="mt-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-semibold text-gray-900">Today’s Coupons</h3>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={loadCoupons}
                        className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
                      >
                        {couponsLoading ? 'Loading…' : 'Reload'}
                      </button>
                      <button
                        type="button"
                        onClick={issueTodayCoupons}
                        className="inline-flex items-center rounded-md bg-primary-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-700"
                      >
                        Issue 4 Meals (Today)
                      </button>
                    </div>
                  </div>

                  <div className="mt-3">
                    {couponsLoading ? (
                      <div className="flex items-center text-gray-600">
                        <div className="spinner-sm mr-2" /> Loading coupons…
                      </div>
                    ) : coupons.length === 0 ? (
                      <div className="rounded-lg border border-dashed border-gray-300 p-4 text-sm text-gray-500">
                        No coupons for today. Use “Issue 4 Meals (Today)” to create breakfast, lunch,
                        snacks and dinner coupons.
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 gap-2">
                        {coupons.map((c) => (
                          <div
                            key={c.id}
                            className="flex items-center justify-between rounded-lg border border-gray-200 px-3 py-2"
                          >
                            <div className="flex items-center gap-2">
                              <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                                {c.slot || 'meal'}
                              </span>
                              <span className="text-xs text-gray-500">ID: {c.id}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              {c.used ? (
                                <span className="inline-flex items-center rounded-md bg-gray-200 px-2 py-0.5 text-xs text-gray-600">
                                  Used
                                </span>
                              ) : (
                                <button
                                  type="button"
                                  onClick={() => setCouponId(c.id)}
                                  className="inline-flex items-center rounded-md border border-gray-300 bg-white px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
                                >
                                  Use
                                </button>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-3 text-xs text-gray-400">APIs: /api/mess/coupons (issue/list)</div>
              </div>
            </div>
          </section>
        )}

        {/* Orders History */}
        {activeTab === 'history' && (
          <section className="rounded-xl border border-gray-200 bg-white p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">My Orders</h2>
              <button
                type="button"
                onClick={async () => {
                  if (!tenantId) return;
                  setOrdersLoading(true);
                  try {
                    const data = await apiClient.listOrders({
                      tenant_id: tenantId,
                      limit: 20,
                      offset: 0,
                    });
                    setOrders((data as OrderRecord[]) || []);
                    toast.success('Orders refreshed');
                  } catch (err: any) {
                    toast.error(err?.message || 'Refresh failed');
                  } finally {
                    setOrdersLoading(false);
                  }
                }}
                className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
              >
                Refresh
              </button>
            </div>

            {ordersLoading ? (
              <div className="mt-6 flex items-center text-gray-600">
                <div className="spinner-sm mr-2" /> Loading...
              </div>
            ) : orders.length === 0 ? (
              <div className="mt-6 rounded-lg border border-dashed border-gray-300 p-6 text-sm text-gray-500">
                No orders yet.
              </div>
            ) : (
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead>
                    <tr className="text-left text-gray-600">
                      <th className="py-2 pr-4">Order ID</th>
                      <th className="py-2 pr-4">Status</th>
                      <th className="py-2 pr-4">Total</th>
                      <th className="py-2 pr-4">Created</th>
                      <th className="py-2 pr-4">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {orders.map((o) => (
                      <tr key={o.id}>
                        <td className="py-2 pr-4 font-mono text-xs text-gray-700">{o.id}</td>
                        <td className="py-2 pr-4">
                          <span className="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700">
                            {o.status}
                          </span>
                        </td>
                        <td className="py-2 pr-4">
                          {o.total_amount != null ? `₹${o.total_amount}` : '—'}
                        </td>
                        <td className="py-2 pr-4">{o.created_at || '—'}</td>
                        <td className="py-2 pr-4">
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              disabled={
                                o.status === 'cancelled' ||
                                o.status === 'delivered' ||
                                o.status === 'completed'
                              }
                              onClick={() => onCancelOrder(o.id)}
                              className="inline-flex items-center rounded-md border border-gray-300 bg-white px-2 py-1 text-xs text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                            >
                              Cancel
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="mt-3 text-xs text-gray-400">
              API: /api/orders (list), /api/orders/:id/cancel
            </div>
          </section>
        )}

        <section className="mt-8">
          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <h3 className="text-base font-medium text-gray-900">Notes</h3>
            <p className="mt-1 text-sm text-gray-600">
              Use “Issue 4 Meals (Today)” to create the default breakfast, lunch, snacks and dinner
              coupons, then select a menu item and place an order optionally using a coupon.
            </p>
          </div>
        </section>
      </main>
    </>
  );
}
import { useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import TenantNav from '@/components/nav/TenantNav';
import { useAuth, useUser } from '@/store/auth-store';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { UtensilsCrossed, Coffee, Sun, Moon, Ticket, RefreshCw } from 'lucide-react';
import { API_CONFIG, API_ENDPOINTS } from '@/config/api';
import toast from 'react-hot-toast';

interface MenuItem {
    id: string;
    name: string;
    description?: string;
    price: number;
    slot: string;
    is_available: boolean;
}

interface WeeklyMenu {
    weekly: {
        [day: string]: {
            breakfast: MenuItem[];
            lunch: MenuItem[];
            snacks: MenuItem[];
            dinner: MenuItem[];
        };
    };
}

interface Coupon {
    id: string;
    tenant_id: string;
    slot: string;
    for_date: string;
    issued_at: string;
    used_at?: string;
    is_used: boolean;
}

const DAYS_OF_WEEK = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
const SLOTS = ['breakfast', 'lunch', 'snacks', 'dinner'];

const slotIcons: Record<string, React.ReactNode> = {
    breakfast: <Coffee className="h-4 w-4" />,
    lunch: <Sun className="h-4 w-4" />,
    snacks: <UtensilsCrossed className="h-4 w-4" />,
    dinner: <Moon className="h-4 w-4" />,
};

export default function TenantMessPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading } = useAuth();
    const { user } = useUser();

    const [weeklyMenu, setWeeklyMenu] = useState<WeeklyMenu | null>(null);
    const [coupons, setCoupons] = useState<Coupon[]>([]);
    const [menuLoading, setMenuLoading] = useState(true);
    const [couponsLoading, setCouponsLoading] = useState(true);
    const [selectedDay, setSelectedDay] = useState<string>(() => {
        const today = new Date().toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
        return today;
    });

    // Auth guard
    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.replace('/auth/login');
        }
    }, [isLoading, isAuthenticated, router]);

    // Fetch weekly menu
    useEffect(() => {
        const fetchMenu = async () => {
            try {
                const res = await fetch(`${API_CONFIG.BASE_URL}${API_ENDPOINTS.MESS.MENU}`);
                if (res.ok) {
                    const data = await res.json();
                    setWeeklyMenu(data);
                }
            } catch (error) {
                console.error('Failed to fetch menu:', error);
            } finally {
                setMenuLoading(false);
            }
        };
        fetchMenu();
    }, []);

    // Fetch user coupons
    useEffect(() => {
        const fetchCoupons = async () => {
            if (!user?.id) return;
            try {
                const token = localStorage.getItem('pgwallah_access_token');
                const res = await fetch(
                    `${API_CONFIG.BASE_URL}${API_ENDPOINTS.MESS.COUPONS}?tenant_id=${user.id}&include_used=true`,
                    { headers: token ? { Authorization: `Bearer ${token}` } : {} }
                );
                if (res.ok) {
                    const data = await res.json();
                    setCoupons(data);
                }
            } catch (error) {
                console.error('Failed to fetch coupons:', error);
            } finally {
                setCouponsLoading(false);
            }
        };
        if (user?.id) fetchCoupons();
    }, [user?.id]);

    if (isLoading || !isAuthenticated) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    const todayMenu = weeklyMenu?.weekly?.[selectedDay];
    const todaysDate = new Date().toISOString().split('T')[0];
    const todaysCoupons = coupons.filter(c => c.for_date === todaysDate && !c.is_used);
    const usedCoupons = coupons.filter(c => c.is_used);

    return (
        <>
            <Head>
                <title>Mess & Menu • PGwallah</title>
            </Head>

            <TenantNav />

            <main className="mx-auto max-w-6xl px-4 py-8">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">Mess & Menu</h1>
                        <p className="mt-1 text-muted-foreground">
                            View today's menu and your meal coupons
                        </p>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Refresh
                    </Button>
                </div>

                {/* Today's Coupons */}
                <section className="mb-8">
                    <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Ticket className="h-5 w-5 text-primary" />
                        Your Coupons for Today
                    </h2>

                    {couponsLoading ? (
                        <div className="flex items-center gap-2 text-muted-foreground">
                            <RefreshCw className="h-4 w-4 animate-spin" />
                            Loading coupons...
                        </div>
                    ) : todaysCoupons.length > 0 ? (
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                            {todaysCoupons.map(coupon => (
                                <Card key={coupon.id} className="border-primary/50 bg-primary/5">
                                    <CardContent className="pt-4 text-center">
                                        <div className="mb-2">{slotIcons[coupon.slot]}</div>
                                        <p className="font-semibold capitalize">{coupon.slot}</p>
                                        <Badge variant="secondary" className="mt-2">Available</Badge>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    ) : (
                        <Card>
                            <CardContent className="py-8 text-center text-muted-foreground">
                                <Ticket className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                <p>No coupons for today. Contact your PG admin to get coupons.</p>
                            </CardContent>
                        </Card>
                    )}
                </section>

                {/* Weekly Menu */}
                <section>
                    <h2 className="text-lg font-semibold mb-4">Weekly Menu</h2>

                    <Tabs value={selectedDay} onValueChange={setSelectedDay}>
                        <TabsList className="mb-4 w-full justify-start overflow-x-auto flex-nowrap">
                            {DAYS_OF_WEEK.map(day => (
                                <TabsTrigger key={day} value={day} className="capitalize">
                                    {day.slice(0, 3)}
                                </TabsTrigger>
                            ))}
                        </TabsList>

                        {DAYS_OF_WEEK.map(day => (
                            <TabsContent key={day} value={day}>
                                {menuLoading ? (
                                    <div className="text-center py-8 text-muted-foreground">
                                        <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
                                        Loading menu...
                                    </div>
                                ) : weeklyMenu?.weekly?.[day] ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {SLOTS.map(slot => {
                                            const dayMenu = weeklyMenu.weekly[day];
                                            const items = dayMenu?.[slot as keyof typeof dayMenu] ?? [];
                                            return (
                                                <Card key={slot}>
                                                    <CardHeader className="pb-2">
                                                        <CardTitle className="text-base flex items-center gap-2 capitalize">
                                                            {slotIcons[slot]}
                                                            {slot}
                                                        </CardTitle>
                                                    </CardHeader>
                                                    <CardContent>
                                                        {items.length > 0 ? (
                                                            <ul className="space-y-2">
                                                                {items.map((item: MenuItem) => (
                                                                    <li key={item.id} className="flex justify-between items-center text-sm">
                                                                        <div>
                                                                            <span className="font-medium">{item.name}</span>
                                                                            {item.description && (
                                                                                <p className="text-xs text-muted-foreground">{item.description}</p>
                                                                            )}
                                                                        </div>
                                                                        <Badge variant="outline">₹{item.price}</Badge>
                                                                    </li>
                                                                ))}
                                                            </ul>
                                                        ) : (
                                                            <p className="text-sm text-muted-foreground">No items scheduled</p>
                                                        )}
                                                    </CardContent>
                                                </Card>
                                            );
                                        })}
                                    </div>
                                ) : (
                                    <Card>
                                        <CardContent className="py-8 text-center text-muted-foreground">
                                            Menu not available. Use "Seed Default Menu" from admin to populate.
                                        </CardContent>
                                    </Card>
                                )}
                            </TabsContent>
                        ))}
                    </Tabs>
                </section>

                {/* Coupon History */}
                {usedCoupons.length > 0 && (
                    <section className="mt-8">
                        <h2 className="text-lg font-semibold mb-4">Recent Coupon History</h2>
                        <Card>
                            <CardContent className="pt-4">
                                <div className="divide-y">
                                    {usedCoupons.slice(0, 10).map(coupon => (
                                        <div key={coupon.id} className="py-2 flex justify-between items-center text-sm">
                                            <div>
                                                <span className="capitalize font-medium">{coupon.slot}</span>
                                                <span className="text-muted-foreground ml-2">
                                                    {new Date(coupon.for_date).toLocaleDateString()}
                                                </span>
                                            </div>
                                            <Badge variant="secondary">Used</Badge>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </section>
                )}
            </main>
        </>
    );
}

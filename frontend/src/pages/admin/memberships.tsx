import { useEffect, useState, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useAuth, useUser } from '@/store/auth-store';
import AdminNav from '@/components/nav/AdminNav';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Users, UserPlus, Home, Calendar, CheckCircle, XCircle } from 'lucide-react';
import { API_CONFIG } from '@/config/api';

interface Membership {
    id: string;
    tenant_id: string;
    tenant_name?: string;
    tenant_email?: string;
    pg_id: string;
    pg_name?: string;
    room_number?: string;
    start_date: string;
    end_date?: string;
    status: string;
    monthly_rent: number;
    created_at: string;
}

export default function AdminMembershipsPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading, getProfile } = useAuth();
    const { user } = useUser();

    const [memberships, setMemberships] = useState<Membership[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeCount, setActiveCount] = useState(0);

    const fetchMemberships = useCallback(async () => {
        try {
            setLoading(true);
            // Fetch from booking service requests (memberships are confirmed booking requests)
            const res = await fetch(`${API_CONFIG.BASE_URL}/api/booking/requests?status=confirmed`);
            if (res.ok) {
                const data = await res.json();
                setMemberships(data.items || []);
                setActiveCount((data.items || []).filter((m: Membership) => m.status === 'confirmed').length);
            }
        } catch (error) {
            console.error('Failed to fetch memberships:', error);
        } finally {
            setLoading(false);
        }
    }, []);

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

    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.replace('/auth/login?redirect=/admin/memberships');
        }
    }, [isAuthenticated, isLoading, router]);

    useEffect(() => {
        if (!isLoading && isAuthenticated && user?.role !== 'admin') {
            router.replace('/dashboard');
        }
    }, [isAuthenticated, isLoading, router, user?.role]);

    useEffect(() => {
        if (isAuthenticated && user?.role === 'admin') {
            fetchMemberships();
        }
    }, [isAuthenticated, user?.role, fetchMemberships]);

    if (isLoading || !isAuthenticated || user?.role !== 'admin') {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    return (
        <>
            <Head>
                <title>Admin • Memberships</title>
            </Head>

            <div className="min-h-screen bg-muted/50">
                <AdminNav />

                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight">Memberships</h1>
                            <p className="mt-1 text-muted-foreground">Manage tenant memberships and room assignments.</p>
                        </div>
                        <Button onClick={() => router.push('/admin/pg')}>
                            <UserPlus className="mr-2 h-4 w-4" />
                            New Membership
                        </Button>
                    </div>

                    {/* Summary Cards */}
                    <div className="grid gap-4 md:grid-cols-3 mb-6">
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-green-100 rounded-lg">
                                        <CheckCircle className="h-5 w-5 text-green-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Active</p>
                                        <p className="text-xl font-bold">{activeCount}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-blue-100 rounded-lg">
                                        <Users className="h-5 w-5 text-blue-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Total Memberships</p>
                                        <p className="text-xl font-bold">{memberships.length}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-purple-100 rounded-lg">
                                        <Home className="h-5 w-5 text-purple-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Occupied Rooms</p>
                                        <p className="text-xl font-bold">{activeCount}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    <Card>
                        <CardHeader>
                            <CardTitle>Active Memberships</CardTitle>
                            <CardDescription>List of all active tenant memberships.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {loading ? (
                                <div className="flex justify-center py-12">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                                </div>
                            ) : memberships.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground border-2 border-dashed rounded-lg">
                                    <Users className="h-12 w-12 mb-4 opacity-20" />
                                    <h3 className="text-lg font-medium">No Memberships Found</h3>
                                    <p className="max-w-sm mt-2 mb-4">You haven't created any memberships yet. Assign tenants to rooms to get started.</p>
                                    <Button variant="outline" onClick={() => router.push('/admin/pg')}>View Properties</Button>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {memberships.map((membership) => (
                                        <div key={membership.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                                            <div className="flex items-center gap-3">
                                                <div className="p-2 bg-muted rounded-full">
                                                    <Users className="h-4 w-4" />
                                                </div>
                                                <div>
                                                    <p className="font-medium">{membership.tenant_name || membership.tenant_email || 'Unknown Tenant'}</p>
                                                    <p className="text-sm text-muted-foreground flex items-center gap-2">
                                                        <Home className="h-3 w-3" />
                                                        Room {membership.room_number || 'N/A'}
                                                        <Calendar className="h-3 w-3 ml-2" />
                                                        Since {new Date(membership.start_date).toLocaleDateString()}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <span className={`text-xs px-2 py-1 rounded-full ${membership.status === 'confirmed'
                                                        ? 'bg-green-100 text-green-700'
                                                        : 'bg-gray-100 text-gray-700'
                                                    }`}>
                                                    {membership.status}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </main>
            </div>
        </>
    );
}

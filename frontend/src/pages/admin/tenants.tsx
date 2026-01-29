import { useEffect, useState, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useAuth, useUser } from '@/store/auth-store';
import AdminNav from '@/components/nav/AdminNav';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
    Users,
    Search,
    Mail,
    Phone,
    RefreshCw,
    User,
    CheckCircle,
    XCircle,
    Building,
    Calendar
} from 'lucide-react';
import { API_CONFIG, API_ENDPOINTS } from '@/config/api';
import toast from 'react-hot-toast';

interface TenantProfile {
    id: string;
    user_id: string;
    occupation?: string;
    company?: string;
    emergency_contact_name?: string;
    emergency_contact_phone?: string;
}

interface UserData {
    id: string;
    email: string;
    phone?: string;
    full_name?: string;
    role: string;
    is_active: boolean;
    is_verified: boolean;
    created_at: string;
    tenant_profile?: TenantProfile;
}

interface BookingInfo {
    tenant_id: string;
    room_no: string;
    pg_name?: string;
    rent_amount: number;
    status: string;
}

export default function AdminTenantsPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading } = useAuth();
    const { user } = useUser();

    const [tenants, setTenants] = useState<UserData[]>([]);
    const [bookings, setBookings] = useState<Map<string, BookingInfo>>(new Map());
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    // Auth guard
    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.replace('/auth/login?redirect=/admin/tenants');
        }
        if (!isLoading && isAuthenticated && user?.role !== 'admin') {
            router.replace('/tenant');
        }
    }, [isLoading, isAuthenticated, user?.role, router]);

    // Fetch tenants
    const fetchTenants = useCallback(async () => {
        try {
            const token = localStorage.getItem('pgwallah_access_token');

            // Fetch users with tenant role
            // Note: This endpoint would need to exist in the auth service
            // For now, we'll attempt to fetch from a users endpoint
            const res = await fetch(
                `${API_CONFIG.BASE_URL}/api/auth/users?role=tenant&limit=100`,
                { headers: token ? { Authorization: `Bearer ${token}` } : {} }
            );

            if (res.ok) {
                const data = await res.json();
                setTenants(data.items || data || []);
            } else if (res.status === 404) {
                // Endpoint might not exist, show empty state
                setTenants([]);
            }

            // Fetch booking/membership info
            const bookingRes = await fetch(
                `${API_CONFIG.BASE_URL}/api/payments/admin/pg/memberships`,
                { headers: token ? { Authorization: `Bearer ${token}` } : {} }
            );

            if (bookingRes.ok) {
                const bookingData = await bookingRes.json();
                const bookingMap = new Map<string, BookingInfo>();
                (bookingData || []).forEach((b: any) => {
                    bookingMap.set(b.tenant_id, {
                        tenant_id: b.tenant_id,
                        room_no: b.room_no,
                        rent_amount: b.rent_amount,
                        status: b.active ? 'active' : 'inactive',
                    });
                });
                setBookings(bookingMap);
            }
        } catch (error) {
            console.error('Failed to fetch tenants:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchTenants();
    }, [fetchTenants]);

    if (isLoading || !isAuthenticated || user?.role !== 'admin') {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    const filteredTenants = tenants.filter(t =>
        t.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.phone?.includes(searchQuery)
    );

    const activeCount = tenants.filter(t => t.is_active).length;
    const verifiedCount = tenants.filter(t => t.is_verified).length;

    return (
        <>
            <Head>
                <title>Tenant Management • Admin • PGwallah</title>
            </Head>

            <AdminNav />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                            <Users className="h-8 w-8" />
                            Tenant Management
                        </h1>
                        <p className="mt-1 text-muted-foreground">
                            View and manage all registered tenants
                        </p>
                    </div>
                    <Button variant="outline" onClick={fetchTenants}>
                        <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mb-6">
                    <Card>
                        <CardContent className="pt-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">Total Tenants</p>
                                    <p className="text-2xl font-bold">{tenants.length}</p>
                                </div>
                                <Users className="h-8 w-8 text-primary opacity-50" />
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="pt-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">Active</p>
                                    <p className="text-2xl font-bold text-green-600">{activeCount}</p>
                                </div>
                                <CheckCircle className="h-8 w-8 text-green-500 opacity-50" />
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="pt-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">Verified</p>
                                    <p className="text-2xl font-bold text-blue-600">{verifiedCount}</p>
                                </div>
                                <CheckCircle className="h-8 w-8 text-blue-500 opacity-50" />
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Search */}
                <div className="relative mb-6">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search by name, email, or phone..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                    />
                </div>

                {/* Tenants List */}
                {loading ? (
                    <div className="text-center py-12">
                        <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2 text-muted-foreground" />
                        <p className="text-muted-foreground">Loading tenants...</p>
                    </div>
                ) : filteredTenants.length > 0 ? (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {filteredTenants.map(tenant => {
                            const booking = bookings.get(tenant.id);
                            return (
                                <Card key={tenant.id} className="overflow-hidden">
                                    <CardHeader className="pb-2">
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className="h-10 w-10 rounded-full bg-primary/10 text-primary grid place-items-center">
                                                    <User className="h-5 w-5" />
                                                </div>
                                                <div>
                                                    <CardTitle className="text-base">
                                                        {tenant.full_name || 'No Name'}
                                                    </CardTitle>
                                                    <p className="text-xs text-muted-foreground">{tenant.email}</p>
                                                </div>
                                            </div>
                                            <div className="flex flex-col gap-1">
                                                <Badge variant={tenant.is_active ? 'default' : 'secondary'}>
                                                    {tenant.is_active ? 'Active' : 'Inactive'}
                                                </Badge>
                                            </div>
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-2 text-sm">
                                            {tenant.phone && (
                                                <div className="flex items-center gap-2 text-muted-foreground">
                                                    <Phone className="h-3 w-3" />
                                                    {tenant.phone}
                                                </div>
                                            )}

                                            {booking && (
                                                <div className="flex items-center gap-2 text-muted-foreground">
                                                    <Building className="h-3 w-3" />
                                                    Room {booking.room_no} • ₹{booking.rent_amount}/mo
                                                </div>
                                            )}

                                            <div className="flex items-center gap-2 text-muted-foreground">
                                                <Calendar className="h-3 w-3" />
                                                Joined {new Date(tenant.created_at).toLocaleDateString()}
                                            </div>

                                            {tenant.tenant_profile?.occupation && (
                                                <div className="text-muted-foreground">
                                                    {tenant.tenant_profile.occupation}
                                                    {tenant.tenant_profile.company && ` at ${tenant.tenant_profile.company}`}
                                                </div>
                                            )}
                                        </div>

                                        <div className="flex gap-2 mt-4">
                                            <Button size="sm" variant="outline" className="flex-1">
                                                <Mail className="mr-2 h-4 w-4" />
                                                Email
                                            </Button>
                                            {tenant.phone && (
                                                <Button size="sm" variant="outline" className="flex-1">
                                                    <Phone className="mr-2 h-4 w-4" />
                                                    Call
                                                </Button>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            );
                        })}
                    </div>
                ) : tenants.length === 0 ? (
                    <Card>
                        <CardContent className="py-12 text-center">
                            <Users className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                            <h3 className="text-lg font-medium mb-2">No tenants found</h3>
                            <p className="text-muted-foreground text-sm">
                                Tenants will appear here once they register and are assigned tenant role.
                            </p>
                            <p className="text-xs text-muted-foreground mt-4">
                                Note: This page requires an admin users endpoint to be implemented.
                            </p>
                        </CardContent>
                    </Card>
                ) : (
                    <Card>
                        <CardContent className="py-12 text-center">
                            <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                            <h3 className="text-lg font-medium mb-2">No results</h3>
                            <p className="text-muted-foreground text-sm">
                                No tenants match your search
                            </p>
                        </CardContent>
                    </Card>
                )}
            </main>
        </>
    );
}

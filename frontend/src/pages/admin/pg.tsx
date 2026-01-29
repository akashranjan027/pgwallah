import { useEffect, useState, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useAuth, useUser } from '@/store/auth-store';
import AdminNav from '@/components/nav/AdminNav';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Building, Plus, MapPin, Phone, Mail, X } from 'lucide-react';
import { API_CONFIG } from '@/config/api';
import { toast } from 'react-hot-toast';

interface Property {
    id: string;
    name: string;
    address: string;
    city: string;
    state: string;
    pincode: string;
    property_type: string;
    description?: string;
    contact_phone?: string;
    contact_email?: string;
    is_active: boolean;
    created_at: string;
}

interface PropertyListResponse {
    items: Property[];
    total: number;
}

export default function AdminPGPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading, getProfile } = useAuth();
    const { user } = useUser();

    const [properties, setProperties] = useState<Property[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        address: '',
        city: '',
        state: '',
        pincode: '',
        contact_phone: '',
        contact_email: '',
        description: '',
    });

    const fetchProperties = useCallback(async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_CONFIG.BASE_URL}/api/booking/properties`);
            if (res.ok) {
                const data: PropertyListResponse = await res.json();
                setProperties(data.items || []);
            }
        } catch (error) {
            console.error('Failed to fetch properties:', error);
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
            router.replace('/auth/login?redirect=/admin/pg');
        }
    }, [isAuthenticated, isLoading, router]);

    useEffect(() => {
        if (!isLoading && isAuthenticated && user?.role !== 'admin') {
            router.replace('/dashboard');
        }
    }, [isAuthenticated, isLoading, router, user?.role]);

    useEffect(() => {
        if (isAuthenticated && user?.role === 'admin') {
            fetchProperties();
        }
    }, [isAuthenticated, user?.role, fetchProperties]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await fetch(`${API_CONFIG.BASE_URL}/api/booking/properties`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...formData,
                    owner_id: user?.id,
                }),
            });
            if (res.ok) {
                toast.success('Property created successfully');
                setShowForm(false);
                setFormData({
                    name: '', address: '', city: '', state: '',
                    pincode: '', contact_phone: '', contact_email: '', description: '',
                });
                fetchProperties();
            } else {
                toast.error('Failed to create property');
            }
        } catch {
            toast.error('Failed to create property');
        }
    };

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
                <title>Admin • PG Management</title>
            </Head>

            <div className="min-h-screen bg-muted/50">
                <AdminNav />

                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight">PG Management</h1>
                            <p className="mt-1 text-muted-foreground">Manage PG buildings, rooms, and facilities.</p>
                        </div>
                        <Button onClick={() => setShowForm(true)}>
                            <Plus className="mr-2 h-4 w-4" />
                            Add New PG
                        </Button>
                    </div>

                    {/* Add Property Form */}
                    {showForm && (
                        <Card className="mb-6">
                            <CardHeader className="flex flex-row items-center justify-between">
                                <CardTitle>Add New Property</CardTitle>
                                <Button variant="ghost" size="sm" onClick={() => setShowForm(false)}>
                                    <X className="h-4 w-4" />
                                </Button>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleSubmit} className="grid gap-4 md:grid-cols-2">
                                    <div className="space-y-2">
                                        <Label htmlFor="name">Property Name *</Label>
                                        <Input
                                            id="name"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="city">City *</Label>
                                        <Input
                                            id="city"
                                            value={formData.city}
                                            onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2 md:col-span-2">
                                        <Label htmlFor="address">Address *</Label>
                                        <Input
                                            id="address"
                                            value={formData.address}
                                            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="state">State *</Label>
                                        <Input
                                            id="state"
                                            value={formData.state}
                                            onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="pincode">Pincode *</Label>
                                        <Input
                                            id="pincode"
                                            value={formData.pincode}
                                            onChange={(e) => setFormData({ ...formData, pincode: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="contact_phone">Contact Phone</Label>
                                        <Input
                                            id="contact_phone"
                                            value={formData.contact_phone}
                                            onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="contact_email">Contact Email</Label>
                                        <Input
                                            id="contact_email"
                                            type="email"
                                            value={formData.contact_email}
                                            onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                                        />
                                    </div>
                                    <div className="md:col-span-2 flex justify-end gap-2">
                                        <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                                            Cancel
                                        </Button>
                                        <Button type="submit">Create Property</Button>
                                    </div>
                                </form>
                            </CardContent>
                        </Card>
                    )}

                    <Card>
                        <CardHeader>
                            <CardTitle>PG Buildings</CardTitle>
                            <CardDescription>List of all registered PG buildings.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {loading ? (
                                <div className="flex justify-center py-12">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                                </div>
                            ) : properties.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground border-2 border-dashed rounded-lg">
                                    <Building className="h-12 w-12 mb-4 opacity-20" />
                                    <h3 className="text-lg font-medium">No PGs Found</h3>
                                    <p className="max-w-sm mt-2 mb-4">You haven't added any PG buildings yet. Start by adding your first property.</p>
                                    <Button variant="outline" onClick={() => setShowForm(true)}>Add Property</Button>
                                </div>
                            ) : (
                                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                    {properties.map((property) => (
                                        <Card key={property.id} className="border hover:shadow-md transition-shadow">
                                            <CardContent className="p-4">
                                                <h3 className="font-semibold text-lg mb-2">{property.name}</h3>
                                                <div className="space-y-1 text-sm text-muted-foreground">
                                                    <div className="flex items-center gap-2">
                                                        <MapPin className="h-4 w-4" />
                                                        <span>{property.address}, {property.city}</span>
                                                    </div>
                                                    {property.contact_phone && (
                                                        <div className="flex items-center gap-2">
                                                            <Phone className="h-4 w-4" />
                                                            <span>{property.contact_phone}</span>
                                                        </div>
                                                    )}
                                                    {property.contact_email && (
                                                        <div className="flex items-center gap-2">
                                                            <Mail className="h-4 w-4" />
                                                            <span>{property.contact_email}</span>
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="mt-3 flex gap-2">
                                                    <Button size="sm" variant="outline">View Rooms</Button>
                                                    <Button size="sm" variant="ghost">Edit</Button>
                                                </div>
                                            </CardContent>
                                        </Card>
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

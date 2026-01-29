import { useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import TenantNav from '@/components/nav/TenantNav';
import { useAuth, useUser } from '@/store/auth-store';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Building,
    MapPin,
    IndianRupee,
    Users,
    Calendar,
    RefreshCw,
    Search,
    ArrowRight,
    Bed,
    Check,
    Clock
} from 'lucide-react';
import { API_CONFIG, API_ENDPOINTS } from '@/config/api';
import toast from 'react-hot-toast';

interface Property {
    id: string;
    name: string;
    address: string;
    city: string;
    state: string;
    pincode: string;
    property_type: string;
    description?: string;
    is_active: boolean;
}

interface Room {
    id: string;
    property_id: string;
    room_number: string;
    floor: number;
    room_type: string;
    capacity: number;
    price_per_month: number;
    current_occupancy: number;
    status: string;
    amenities?: string[];
}

interface BookingRequest {
    id: string;
    tenant_id: string;
    room_id: string;
    check_in_date: string;
    check_out_date?: string;
    status: string;
    created_at: string;
}

const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    confirmed: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800',
};

export default function TenantBookingPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading } = useAuth();
    const { user } = useUser();

    const [properties, setProperties] = useState<Property[]>([]);
    const [rooms, setRooms] = useState<Room[]>([]);
    const [myBookings, setMyBookings] = useState<BookingRequest[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedProperty, setSelectedProperty] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');

    // Auth guard
    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.replace('/auth/login');
        }
    }, [isLoading, isAuthenticated, router]);

    // Fetch properties
    useEffect(() => {
        const fetchData = async () => {
            try {
                const token = localStorage.getItem('pgwallah_access_token');
                const headers = token ? { Authorization: `Bearer ${token}` } : {};

                // Fetch properties
                const propRes = await fetch(
                    `${API_CONFIG.BASE_URL}${API_ENDPOINTS.BOOKING.PROPERTIES}`,
                    { headers }
                );
                if (propRes.ok) {
                    const data = await propRes.json();
                    setProperties(data.items || []);
                }

                // Fetch my booking requests
                if (user?.id) {
                    const bookingRes = await fetch(
                        `${API_CONFIG.BASE_URL}${API_ENDPOINTS.BOOKING.REQUESTS}?tenant_id=${user.id}`,
                        { headers }
                    );
                    if (bookingRes.ok) {
                        const data = await bookingRes.json();
                        setMyBookings(data.items || []);
                    }
                }
            } catch (error) {
                console.error('Failed to fetch data:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [user?.id]);

    // Fetch rooms when property selected
    useEffect(() => {
        if (!selectedProperty) {
            setRooms([]);
            return;
        }

        const fetchRooms = async () => {
            try {
                const res = await fetch(
                    `${API_CONFIG.BASE_URL}${API_ENDPOINTS.BOOKING.ROOMS}?property_id=${selectedProperty}`
                );
                if (res.ok) {
                    const data = await res.json();
                    setRooms(data.items || []);
                }
            } catch (error) {
                console.error('Failed to fetch rooms:', error);
            }
        };
        fetchRooms();
    }, [selectedProperty]);

    const handleBookRoom = async (roomId: string) => {
        try {
            const token = localStorage.getItem('pgwallah_access_token');
            const res = await fetch(
                `${API_CONFIG.BASE_URL}${API_ENDPOINTS.BOOKING.REQUESTS}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(token ? { Authorization: `Bearer ${token}` } : {}),
                    },
                    body: JSON.stringify({
                        room_id: roomId,
                        tenant_id: user?.id,
                        check_in_date: new Date().toISOString().split('T')[0],
                    }),
                }
            );

            if (res.ok) {
                toast.success('Booking request submitted!');
                // Refresh bookings
                const bookingRes = await fetch(
                    `${API_CONFIG.BASE_URL}${API_ENDPOINTS.BOOKING.REQUESTS}?tenant_id=${user?.id}`,
                    { headers: token ? { Authorization: `Bearer ${token}` } : {} }
                );
                if (bookingRes.ok) {
                    const data = await bookingRes.json();
                    setMyBookings(data.items || []);
                }
            } else {
                const error = await res.json();
                toast.error(error.detail || 'Failed to submit booking request');
            }
        } catch (error) {
            toast.error('Failed to submit booking request');
        }
    };

    if (isLoading || !isAuthenticated) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    const filteredProperties = properties.filter(p =>
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.city.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const availableRooms = rooms.filter(r => r.status === 'available' && r.current_occupancy < r.capacity);

    return (
        <>
            <Head>
                <title>Room Booking • PGwallah</title>
            </Head>

            <TenantNav />

            <main className="mx-auto max-w-6xl px-4 py-8">
                <div className="mb-6">
                    <h1 className="text-3xl font-bold tracking-tight">Room Booking</h1>
                    <p className="mt-1 text-muted-foreground">
                        Browse available properties and request room bookings
                    </p>
                </div>

                {/* My Booking Requests */}
                {myBookings.length > 0 && (
                    <section className="mb-8">
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Clock className="h-5 w-5" />
                            My Booking Requests
                        </h2>
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                            {myBookings.map(booking => (
                                <Card key={booking.id}>
                                    <CardContent className="pt-4">
                                        <div className="flex justify-between items-start mb-2">
                                            <p className="text-sm text-muted-foreground">
                                                Requested: {new Date(booking.created_at).toLocaleDateString()}
                                            </p>
                                            <Badge className={statusColors[booking.status] || 'bg-gray-100'}>
                                                {booking.status}
                                            </Badge>
                                        </div>
                                        <p className="text-sm">
                                            Check-in: {new Date(booking.check_in_date).toLocaleDateString()}
                                        </p>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </section>
                )}

                {/* Search */}
                <div className="relative mb-6">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search properties by name or city..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                    />
                </div>

                {/* Properties Grid */}
                {loading ? (
                    <div className="text-center py-12">
                        <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2 text-muted-foreground" />
                        <p className="text-muted-foreground">Loading properties...</p>
                    </div>
                ) : filteredProperties.length > 0 ? (
                    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                        {filteredProperties.map(property => (
                            <Card
                                key={property.id}
                                className={`cursor-pointer transition-all ${selectedProperty === property.id
                                        ? 'ring-2 ring-primary'
                                        : 'hover:shadow-lg'
                                    }`}
                                onClick={() => setSelectedProperty(
                                    selectedProperty === property.id ? null : property.id
                                )}
                            >
                                <CardHeader className="pb-2">
                                    <div className="flex items-start justify-between">
                                        <div className="h-10 w-10 rounded-lg bg-primary/10 text-primary grid place-items-center">
                                            <Building className="h-5 w-5" />
                                        </div>
                                        <Badge variant="outline">{property.property_type}</Badge>
                                    </div>
                                    <CardTitle className="mt-2">{property.name}</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground flex items-center gap-1">
                                        <MapPin className="h-3 w-3" />
                                        {property.city}, {property.state}
                                    </p>
                                    {property.description && (
                                        <p className="text-sm mt-2 line-clamp-2">{property.description}</p>
                                    )}
                                    <Button
                                        variant="link"
                                        className="mt-2 px-0 text-primary"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setSelectedProperty(property.id);
                                        }}
                                    >
                                        View Rooms <ArrowRight className="ml-1 h-4 w-4" />
                                    </Button>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : (
                    <Card>
                        <CardContent className="py-12 text-center text-muted-foreground">
                            <Building className="h-12 w-12 mx-auto mb-4 opacity-50" />
                            <p className="text-lg font-medium">No properties available</p>
                            <p className="text-sm">Check back later or contact support</p>
                        </CardContent>
                    </Card>
                )}

                {/* Available Rooms for Selected Property */}
                {selectedProperty && (
                    <section className="mt-8">
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Bed className="h-5 w-5" />
                            Available Rooms
                        </h2>

                        {availableRooms.length > 0 ? (
                            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                                {availableRooms.map(room => (
                                    <Card key={room.id}>
                                        <CardHeader className="pb-2">
                                            <div className="flex justify-between items-start">
                                                <CardTitle className="text-lg">Room {room.room_number}</CardTitle>
                                                <Badge variant="secondary">{room.room_type}</Badge>
                                            </div>
                                            <CardDescription>Floor {room.floor}</CardDescription>
                                        </CardHeader>
                                        <CardContent>
                                            <div className="space-y-2 text-sm">
                                                <div className="flex justify-between">
                                                    <span className="text-muted-foreground">Capacity</span>
                                                    <span>{room.current_occupancy}/{room.capacity} occupied</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-muted-foreground">Monthly Rent</span>
                                                    <span className="font-semibold text-primary">
                                                        ₹{room.price_per_month.toLocaleString()}
                                                    </span>
                                                </div>
                                                {room.amenities && room.amenities.length > 0 && (
                                                    <div className="flex flex-wrap gap-1 mt-2">
                                                        {room.amenities.slice(0, 3).map((amenity, i) => (
                                                            <Badge key={i} variant="outline" className="text-xs">
                                                                {amenity}
                                                            </Badge>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                            <Button
                                                className="w-full mt-4"
                                                onClick={() => handleBookRoom(room.id)}
                                            >
                                                <Check className="mr-2 h-4 w-4" />
                                                Request Booking
                                            </Button>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        ) : rooms.length > 0 ? (
                            <Card>
                                <CardContent className="py-8 text-center text-muted-foreground">
                                    <Bed className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                    <p>No available rooms in this property</p>
                                </CardContent>
                            </Card>
                        ) : (
                            <Card>
                                <CardContent className="py-8 text-center text-muted-foreground">
                                    <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
                                    <p>Loading rooms...</p>
                                </CardContent>
                            </Card>
                        )}
                    </section>
                )}
            </main>
        </>
    );
}

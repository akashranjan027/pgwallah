import { useEffect, useState, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useAuth, useUser } from '@/store/auth-store';
import AdminNav from '@/components/nav/AdminNav';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CreditCard, Download, IndianRupee, Calendar, User } from 'lucide-react';
import { API_CONFIG } from '@/config/api';

interface RentPayment {
    id: string;
    tenant_id: string;
    tenant_name?: string;
    amount: number;
    month: string;
    year: number;
    status: string;
    payment_date?: string;
    created_at: string;
}

export default function AdminRentPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading, getProfile } = useAuth();
    const { user } = useUser();

    const [payments, setPayments] = useState<RentPayment[]>([]);
    const [loading, setLoading] = useState(true);
    const [totalCollected, setTotalCollected] = useState(0);

    const fetchRentPayments = useCallback(async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_CONFIG.BASE_URL}/api/payments/admin/rent`);
            if (res.ok) {
                const data = await res.json();
                setPayments(data.payments || []);
                const total = (data.payments || []).reduce((sum: number, p: RentPayment) =>
                    p.status === 'completed' ? sum + p.amount : sum, 0
                );
                setTotalCollected(total);
            }
        } catch (error) {
            console.error('Failed to fetch rent payments:', error);
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
            router.replace('/auth/login?redirect=/admin/rent');
        }
    }, [isAuthenticated, isLoading, router]);

    useEffect(() => {
        if (!isLoading && isAuthenticated && user?.role !== 'admin') {
            router.replace('/dashboard');
        }
    }, [isAuthenticated, isLoading, router, user?.role]);

    useEffect(() => {
        if (isAuthenticated && user?.role === 'admin') {
            fetchRentPayments();
        }
    }, [isAuthenticated, user?.role, fetchRentPayments]);

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
                <title>Admin • Rent Payments</title>
            </Head>

            <div className="min-h-screen bg-muted/50">
                <AdminNav />

                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight">Rent Payments</h1>
                            <p className="mt-1 text-muted-foreground">Track and manage monthly rent collections.</p>
                        </div>
                        <Button variant="outline">
                            <Download className="mr-2 h-4 w-4" />
                            Export Report
                        </Button>
                    </div>

                    {/* Summary Cards */}
                    <div className="grid gap-4 md:grid-cols-3 mb-6">
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-green-100 rounded-lg">
                                        <IndianRupee className="h-5 w-5 text-green-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Total Collected</p>
                                        <p className="text-xl font-bold">₹{totalCollected.toLocaleString()}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-blue-100 rounded-lg">
                                        <CreditCard className="h-5 w-5 text-blue-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Total Payments</p>
                                        <p className="text-xl font-bold">{payments.length}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-yellow-100 rounded-lg">
                                        <Calendar className="h-5 w-5 text-yellow-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Current Month</p>
                                        <p className="text-xl font-bold">{new Date().toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    <Card>
                        <CardHeader>
                            <CardTitle>Payment History</CardTitle>
                            <CardDescription>Recent rent payments received from tenants.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {loading ? (
                                <div className="flex justify-center py-12">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                                </div>
                            ) : payments.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground border-2 border-dashed rounded-lg">
                                    <CreditCard className="h-12 w-12 mb-4 opacity-20" />
                                    <h3 className="text-lg font-medium">No Payments Recorded</h3>
                                    <p className="max-w-sm mt-2 mb-4">No rent payments have been recorded for this month yet.</p>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {payments.map((payment) => (
                                        <div key={payment.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                                            <div className="flex items-center gap-3">
                                                <div className="p-2 bg-muted rounded-full">
                                                    <User className="h-4 w-4" />
                                                </div>
                                                <div>
                                                    <p className="font-medium">{payment.tenant_name || 'Unknown Tenant'}</p>
                                                    <p className="text-sm text-muted-foreground">
                                                        {payment.month} {payment.year}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className="font-semibold">₹{payment.amount.toLocaleString()}</p>
                                                <span className={`text-xs px-2 py-1 rounded-full ${payment.status === 'completed'
                                                        ? 'bg-green-100 text-green-700'
                                                        : 'bg-yellow-100 text-yellow-700'
                                                    }`}>
                                                    {payment.status}
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

import { useEffect, useState, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useAuth, useUser } from '@/store/auth-store';
import AdminNav from '@/components/nav/AdminNav';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Wallet, Plus, IndianRupee, User, Calendar } from 'lucide-react';
import { API_CONFIG } from '@/config/api';

interface AdvancePayment {
    id: string;
    tenant_id: string;
    tenant_name?: string;
    amount: number;
    purpose: string;
    status: string;
    created_at: string;
    refunded_at?: string;
}

export default function AdminAdvancePage() {
    const router = useRouter();
    const { isAuthenticated, isLoading, getProfile } = useAuth();
    const { user } = useUser();

    const [advances, setAdvances] = useState<AdvancePayment[]>([]);
    const [loading, setLoading] = useState(true);
    const [totalHeld, setTotalHeld] = useState(0);

    const fetchAdvances = useCallback(async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_CONFIG.BASE_URL}/api/payments/admin/advance`);
            if (res.ok) {
                const data = await res.json();
                setAdvances(data.payments || []);
                const total = (data.payments || []).reduce((sum: number, p: AdvancePayment) =>
                    p.status === 'held' ? sum + p.amount : sum, 0
                );
                setTotalHeld(total);
            }
        } catch (error) {
            console.error('Failed to fetch advance payments:', error);
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
            router.replace('/auth/login?redirect=/admin/advance');
        }
    }, [isAuthenticated, isLoading, router]);

    useEffect(() => {
        if (!isLoading && isAuthenticated && user?.role !== 'admin') {
            router.replace('/dashboard');
        }
    }, [isAuthenticated, isLoading, router, user?.role]);

    useEffect(() => {
        if (isAuthenticated && user?.role === 'admin') {
            fetchAdvances();
        }
    }, [isAuthenticated, user?.role, fetchAdvances]);

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
                <title>Admin • Advance Payments</title>
            </Head>

            <div className="min-h-screen bg-muted/50">
                <AdminNav />

                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight">Advance Payments</h1>
                            <p className="mt-1 text-muted-foreground">Manage security deposits and advance payments.</p>
                        </div>
                        <Button>
                            <Plus className="mr-2 h-4 w-4" />
                            Record Advance
                        </Button>
                    </div>

                    {/* Summary Cards */}
                    <div className="grid gap-4 md:grid-cols-2 mb-6">
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-blue-100 rounded-lg">
                                        <IndianRupee className="h-5 w-5 text-blue-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Total Deposits Held</p>
                                        <p className="text-xl font-bold">₹{totalHeld.toLocaleString()}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-green-100 rounded-lg">
                                        <Wallet className="h-5 w-5 text-green-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Total Records</p>
                                        <p className="text-xl font-bold">{advances.length}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    <Card>
                        <CardHeader>
                            <CardTitle>Deposits & Advances</CardTitle>
                            <CardDescription>List of all security deposits held.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {loading ? (
                                <div className="flex justify-center py-12">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                                </div>
                            ) : advances.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground border-2 border-dashed rounded-lg">
                                    <Wallet className="h-12 w-12 mb-4 opacity-20" />
                                    <h3 className="text-lg font-medium">No Records Found</h3>
                                    <p className="max-w-sm mt-2 mb-4">No advance payments or security deposits have been recorded yet.</p>
                                    <Button variant="outline">Record Payment</Button>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {advances.map((advance) => (
                                        <div key={advance.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                                            <div className="flex items-center gap-3">
                                                <div className="p-2 bg-muted rounded-full">
                                                    <User className="h-4 w-4" />
                                                </div>
                                                <div>
                                                    <p className="font-medium">{advance.tenant_name || 'Unknown Tenant'}</p>
                                                    <p className="text-sm text-muted-foreground flex items-center gap-2">
                                                        <span className="capitalize">{advance.purpose}</span>
                                                        <Calendar className="h-3 w-3 ml-2" />
                                                        {new Date(advance.created_at).toLocaleDateString()}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className="font-semibold">₹{advance.amount.toLocaleString()}</p>
                                                <span className={`text-xs px-2 py-1 rounded-full ${advance.status === 'held'
                                                        ? 'bg-blue-100 text-blue-700'
                                                        : 'bg-gray-100 text-gray-700'
                                                    }`}>
                                                    {advance.status}
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

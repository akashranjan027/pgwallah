import { useEffect, useState, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useAuth, useUser } from '@/store/auth-store';
import AdminNav from '@/components/nav/AdminNav';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Plus, Download, IndianRupee, Calendar, User, Eye } from 'lucide-react';
import { API_CONFIG } from '@/config/api';
import { toast } from 'react-hot-toast';

interface Invoice {
    id: string;
    invoice_number: string;
    tenant_id: string;
    tenant_name?: string;
    tenant_email?: string;
    amount: number;
    status: string;
    due_date: string;
    paid_at?: string;
    created_at: string;
    items?: { description: string; amount: number }[];
}

export default function AdminInvoicesPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading, getProfile } = useAuth();
    const { user } = useUser();

    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [loading, setLoading] = useState(true);
    const [totalPending, setTotalPending] = useState(0);

    const fetchInvoices = useCallback(async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_CONFIG.BASE_URL}/api/invoices`);
            if (res.ok) {
                const data = await res.json();
                setInvoices(data.invoices || data.items || []);
                const pending = (data.invoices || data.items || [])
                    .filter((inv: Invoice) => inv.status === 'pending' || inv.status === 'unpaid')
                    .reduce((sum: number, inv: Invoice) => sum + inv.amount, 0);
                setTotalPending(pending);
            }
        } catch (error) {
            console.error('Failed to fetch invoices:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    const downloadPDF = async (invoiceId: string) => {
        try {
            window.open(`${API_CONFIG.BASE_URL}/api/invoices/${invoiceId}/pdf`, '_blank');
        } catch {
            toast.error('Failed to download PDF');
        }
    };

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
            router.replace('/auth/login?redirect=/admin/invoices');
        }
    }, [isAuthenticated, isLoading, router]);

    useEffect(() => {
        if (!isLoading && isAuthenticated && user?.role !== 'admin') {
            router.replace('/dashboard');
        }
    }, [isAuthenticated, isLoading, router, user?.role]);

    useEffect(() => {
        if (isAuthenticated && user?.role === 'admin') {
            fetchInvoices();
        }
    }, [isAuthenticated, user?.role, fetchInvoices]);

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
                <title>Admin • Invoices</title>
            </Head>

            <div className="min-h-screen bg-muted/50">
                <AdminNav />

                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight">Invoices</h1>
                            <p className="mt-1 text-muted-foreground">Generate and manage tenant invoices.</p>
                        </div>
                        <Button>
                            <Plus className="mr-2 h-4 w-4" />
                            Generate Invoice
                        </Button>
                    </div>

                    {/* Summary Cards */}
                    <div className="grid gap-4 md:grid-cols-3 mb-6">
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-blue-100 rounded-lg">
                                        <FileText className="h-5 w-5 text-blue-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Total Invoices</p>
                                        <p className="text-xl font-bold">{invoices.length}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-yellow-100 rounded-lg">
                                        <IndianRupee className="h-5 w-5 text-yellow-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Pending Amount</p>
                                        <p className="text-xl font-bold">₹{totalPending.toLocaleString()}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-green-100 rounded-lg">
                                        <Calendar className="h-5 w-5 text-green-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">This Month</p>
                                        <p className="text-xl font-bold">{new Date().toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    <Card>
                        <CardHeader>
                            <CardTitle>All Invoices</CardTitle>
                            <CardDescription>History of all generated invoices.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {loading ? (
                                <div className="flex justify-center py-12">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                                </div>
                            ) : invoices.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground border-2 border-dashed rounded-lg">
                                    <FileText className="h-12 w-12 mb-4 opacity-20" />
                                    <h3 className="text-lg font-medium">No Invoices Generated</h3>
                                    <p className="max-w-sm mt-2 mb-4">You haven't generated any invoices yet.</p>
                                    <Button variant="outline">Create New Invoice</Button>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {invoices.map((invoice) => (
                                        <div key={invoice.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                                            <div className="flex items-center gap-3">
                                                <div className="p-2 bg-muted rounded-full">
                                                    <FileText className="h-4 w-4" />
                                                </div>
                                                <div>
                                                    <p className="font-medium">#{invoice.invoice_number}</p>
                                                    <p className="text-sm text-muted-foreground flex items-center gap-2">
                                                        <User className="h-3 w-3" />
                                                        {invoice.tenant_name || invoice.tenant_email || 'Unknown'}
                                                        <Calendar className="h-3 w-3 ml-2" />
                                                        Due: {new Date(invoice.due_date).toLocaleDateString()}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <div className="text-right">
                                                    <p className="font-semibold">₹{invoice.amount.toLocaleString()}</p>
                                                    <span className={`text-xs px-2 py-1 rounded-full ${invoice.status === 'paid'
                                                        ? 'bg-green-100 text-green-700'
                                                        : invoice.status === 'overdue'
                                                            ? 'bg-red-100 text-red-700'
                                                            : 'bg-yellow-100 text-yellow-700'
                                                        }`}>
                                                        {invoice.status}
                                                    </span>
                                                </div>
                                                <div className="flex gap-1">
                                                    <Button size="sm" variant="ghost" onClick={() => downloadPDF(invoice.id)}>
                                                        <Download className="h-4 w-4" />
                                                    </Button>
                                                    <Button size="sm" variant="ghost">
                                                        <Eye className="h-4 w-4" />
                                                    </Button>
                                                </div>
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

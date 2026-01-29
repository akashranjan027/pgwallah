import { useEffect, useState, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import TenantNav from '@/components/nav/TenantNav';
import { useAuth, useUser } from '@/store/auth-store';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { CreditCard, Calendar, Receipt, ArrowRight, IndianRupee, Clock, CheckCircle, X } from 'lucide-react';
import { API_CONFIG } from '@/config/api';
import { toast } from 'react-hot-toast';

interface PaymentIntent {
  id: string;
  amount: number;
  status: string;
  upi_link?: string;
  created_at: string;
}

interface PaymentReceipt {
  id: string;
  amount: number;
  payment_type: string;
  status: string;
  created_at: string;
}

export default function TenantPaymentsPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, getProfile } = useAuth();
  const { user } = useUser();

  const [activeTab, setActiveTab] = useState<'pay' | 'history' | 'receipts'>('pay');
  const [intents, setIntents] = useState<PaymentIntent[]>([]);
  const [receipts, setReceipts] = useState<PaymentReceipt[]>([]);
  const [loading, setLoading] = useState(false);

  // Pay rent form
  const [amount, setAmount] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const tenantId = user?.id;

  const fetchIntents = useCallback(async () => {
    if (!tenantId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_CONFIG.BASE_URL}/api/payments/intents?tenant_id=${tenantId}`);
      if (res.ok) {
        const data = await res.json();
        setIntents(data.intents || data.items || []);
      }
    } catch (error) {
      console.error('Failed to fetch intents:', error);
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  const fetchReceipts = useCallback(async () => {
    if (!tenantId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_CONFIG.BASE_URL}/api/payments/receipts?tenant_id=${tenantId}`);
      if (res.ok) {
        const data = await res.json();
        setReceipts(data.receipts || data.items || []);
      }
    } catch (error) {
      console.error('Failed to fetch receipts:', error);
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => {
    const init = async () => {
      try {
        await getProfile();
      } catch {
        // store handles auth errors
      }
    };
    init();
  }, [getProfile]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/auth/login');
    }
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated && tenantId) {
      if (activeTab === 'history') fetchIntents();
      if (activeTab === 'receipts') fetchReceipts();
    }
  }, [activeTab, isAuthenticated, tenantId, fetchIntents, fetchReceipts]);

  const handlePayRent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tenantId || !amount) return;

    setSubmitting(true);
    try {
      const res = await fetch(`${API_CONFIG.BASE_URL}/api/payments/dummy/rent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: tenantId,
          amount: parseFloat(amount),
          month: new Date().toLocaleDateString('en-US', { month: 'long' }),
          year: new Date().getFullYear(),
        }),
      });
      if (res.ok) {
        toast.success('Rent payment recorded successfully!');
        setAmount('');
        setActiveTab('receipts');
        fetchReceipts();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Payment failed');
      }
    } catch {
      toast.error('Failed to process payment');
    } finally {
      setSubmitting(false);
    }
  };

  const createUPIIntent = async () => {
    if (!tenantId || !amount) {
      toast.error('Enter an amount first');
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch(`${API_CONFIG.BASE_URL}/api/payments/intents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: tenantId,
          amount: parseFloat(amount),
          purpose: 'Rent Payment',
        }),
      });
      if (res.ok) {
        const data = await res.json();
        toast.success('UPI Intent created!');
        if (data.upi_link) {
          window.open(data.upi_link, '_blank');
        }
        setActiveTab('history');
        fetchIntents();
      } else {
        toast.error('Failed to create UPI intent');
      }
    } catch {
      toast.error('Failed to create intent');
    } finally {
      setSubmitting(false);
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
        <title>Tenant • Payments</title>
      </Head>

      <div className="min-h-screen bg-muted/50">
        <TenantNav />

        <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-6">
            <h1 className="text-3xl font-bold tracking-tight">Payments</h1>
            <p className="mt-1 text-muted-foreground">
              Pay rent, view payment history, and download receipts.
            </p>
          </div>

          <Tabs value={activeTab} onValueChange={(v: string) => setActiveTab(v as 'pay' | 'history' | 'receipts')}>
            <TabsList className="mb-6">
              <TabsTrigger value="pay">Pay Rent</TabsTrigger>
              <TabsTrigger value="history">Payment History</TabsTrigger>
              <TabsTrigger value="receipts">Receipts</TabsTrigger>
            </TabsList>

            {/* Pay Rent Tab */}
            <TabsContent value="pay">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <IndianRupee className="h-5 w-5 text-primary" />
                      Quick Pay
                    </CardTitle>
                    <CardDescription>
                      Record a rent payment directly.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handlePayRent} className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="amount">Amount (₹)</Label>
                        <Input
                          id="amount"
                          type="number"
                          min="1"
                          value={amount}
                          onChange={(e) => setAmount(e.target.value)}
                          placeholder="Enter amount"
                          required
                        />
                      </div>
                      <Button type="submit" className="w-full" disabled={submitting}>
                        {submitting ? 'Processing...' : 'Record Payment'}
                      </Button>
                    </form>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CreditCard className="h-5 w-5 text-primary" />
                      UPI Payment
                    </CardTitle>
                    <CardDescription>
                      Generate UPI link to pay via GPay, PhonePe, etc.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-muted-foreground">
                      Enter an amount above, then click below to generate a UPI payment link.
                    </p>
                    <Button
                      onClick={createUPIIntent}
                      variant="outline"
                      className="w-full"
                      disabled={submitting || !amount}
                    >
                      Create UPI Intent
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Payment History Tab */}
            <TabsContent value="history">
              <Card>
                <CardHeader>
                  <CardTitle>Payment Intents</CardTitle>
                  <CardDescription>Recent payment attempts and their status.</CardDescription>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="flex justify-center py-8">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                    </div>
                  ) : intents.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground border-2 border-dashed rounded-lg">
                      <Clock className="h-12 w-12 mb-4 opacity-20" />
                      <h3 className="text-lg font-medium">No Payment History</h3>
                      <p className="max-w-sm mt-2">Your payment intents will appear here.</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {intents.map((intent) => (
                        <div key={intent.id} className="flex items-center justify-between p-4 border rounded-lg">
                          <div>
                            <p className="font-medium">₹{intent.amount?.toLocaleString()}</p>
                            <p className="text-sm text-muted-foreground">
                              {new Date(intent.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <Badge variant={intent.status === 'completed' ? 'default' : 'secondary'}>
                            {intent.status}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Receipts Tab */}
            <TabsContent value="receipts">
              <Card>
                <CardHeader>
                  <CardTitle>Payment Receipts</CardTitle>
                  <CardDescription>Download receipts for your records.</CardDescription>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="flex justify-center py-8">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                    </div>
                  ) : receipts.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground border-2 border-dashed rounded-lg">
                      <Receipt className="h-12 w-12 mb-4 opacity-20" />
                      <h3 className="text-lg font-medium">No Receipts</h3>
                      <p className="max-w-sm mt-2">Completed payments will show receipts here.</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {receipts.map((receipt) => (
                        <div key={receipt.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-green-100 rounded-full">
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            </div>
                            <div>
                              <p className="font-medium">₹{receipt.amount?.toLocaleString()}</p>
                              <p className="text-sm text-muted-foreground">
                                {receipt.payment_type} • {new Date(receipt.created_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                          <Button size="sm" variant="outline">
                            Download
                          </Button>
                        </div>
                      ))}
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
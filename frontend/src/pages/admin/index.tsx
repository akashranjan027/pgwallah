import { useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth, useUser } from '@/store/auth-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Building, Users, CreditCard, Wallet, FileText, LogOut, ChefHat, UtensilsCrossed, UserCheck } from 'lucide-react';

import AdminNav from '@/components/nav/AdminNav';

export default function AdminHomePage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, getProfile } = useAuth();
  const { user } = useUser();

  // Load profile on first paint (client-only)
  useEffect(() => {
    const init = async () => {
      try {
        await getProfile();
      } catch {
        // errors handled in store
      }
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Guard: redirect non-authenticated users to login (and back to /admin after)
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/auth/login?redirect=/admin');
    }
  }, [isAuthenticated, isLoading, router]);

  // Guard: only admins may view admin UI
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      const role = user?.role;
      if (role !== 'admin') {
        // Send tenants/staff to their respective home
        router.replace(role === 'tenant' ? '/tenant' : '/dashboard');
      }
    }
  }, [isAuthenticated, isLoading, router, user?.role]);

  if (isLoading || !isAuthenticated || user?.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-muted/50">
      <AdminNav />

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold tracking-tight">Admin Console</h1>
        <p className="mt-1 text-muted-foreground">Manage PGs, tenants, payments, and operations.</p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
          {/* PG Management */}
          <Link href="/admin/pg">
            <Card className="hover:bg-muted/50 transition-colors cursor-pointer h-full">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-blue-100 text-blue-600 grid place-items-center">
                  <Building className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">PG Management</div>
                  <div className="text-sm text-muted-foreground">Create PGs, assign admins</div>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Tenants */}
          <Link href="/admin/tenants">
            <Card className="hover:bg-muted/50 transition-colors cursor-pointer h-full">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-cyan-100 text-cyan-600 grid place-items-center">
                  <UserCheck className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">Tenants</div>
                  <div className="text-sm text-muted-foreground">View and manage tenants</div>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Memberships */}
          <Link href="/admin/memberships">
            <Card className="hover:bg-muted/50 transition-colors cursor-pointer h-full">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-purple-100 text-purple-600 grid place-items-center">
                  <Users className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">Memberships</div>
                  <div className="text-sm text-muted-foreground">Assign tenants, rooms, rents</div>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Kitchen Orders */}
          <Link href="/admin/orders">
            <Card className="hover:bg-muted/50 transition-colors cursor-pointer h-full">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-orange-100 text-orange-600 grid place-items-center">
                  <ChefHat className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">Kitchen Orders</div>
                  <div className="text-sm text-muted-foreground">Manage food orders</div>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Mess Menu */}
          <Link href="/admin/mess">
            <Card className="hover:bg-muted/50 transition-colors cursor-pointer h-full">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-pink-100 text-pink-600 grid place-items-center">
                  <UtensilsCrossed className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">Mess Menu</div>
                  <div className="text-sm text-muted-foreground">Manage food items</div>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Rent Payments */}
          <Link href="/admin/rent">
            <Card className="hover:bg-muted/50 transition-colors cursor-pointer h-full">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-green-100 text-green-600 grid place-items-center">
                  <CreditCard className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">Rent Payments</div>
                  <div className="text-sm text-muted-foreground">View and record rent</div>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Advance Payments */}
          <Link href="/admin/advance">
            <Card className="hover:bg-muted/50 transition-colors cursor-pointer h-full">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-yellow-100 text-yellow-600 grid place-items-center">
                  <Wallet className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">Advance Payments</div>
                  <div className="text-sm text-muted-foreground">Record advances / deposits</div>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Invoices */}
          <Link href="/admin/invoices">
            <Card className="hover:bg-muted/50 transition-colors cursor-pointer h-full">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-indigo-100 text-indigo-600 grid place-items-center">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">Invoices</div>
                  <div className="text-sm text-muted-foreground">Generate and download</div>
                </div>
              </CardContent>
            </Card>
          </Link>
        </div>

        <div className="mt-8 p-4 bg-blue-50/50 border border-blue-100 rounded-lg">
          <p className="text-sm text-blue-700">
            Tip: Use the Admin menu cards above to navigate. All pages are connected to their respective backend APIs.
          </p>
        </div>
      </main>
    </div>
  );
}
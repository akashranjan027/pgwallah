import { useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth, useUser } from '@/store/auth-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LayoutDashboard, LogOut, User, Mail, Phone, Activity, Home, ArrowRight } from 'lucide-react';

function StatCard({ title, value, subtitle, icon: Icon }: { title: string; value: string | number; subtitle?: string; icon: any }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, getProfile, logout } = useAuth();
  const { user, tenantProfile } = useUser();

  // Ensure profile is loaded on first entry
  useEffect(() => {
    const init = async () => {
      try {
        await getProfile();
      } catch {
        // ignore here; hook level handles auth errors
      }
    };
    init();
  }, [getProfile]);

  // Redirect unauthenticated users to login
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/auth/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  const displayName = user?.full_name || user?.email || 'Guest';
  const role = user?.role || 'tenant';

  return (
    <>
      <Head>
        <title>Dashboard • PGwallah</title>
      </Head>

      <div className="min-h-screen bg-muted/50">
        {/* Top Bar */}
        <header className="sticky top-0 z-10 bg-background/80 backdrop-blur border-b">
          <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-9 w-9 rounded-lg bg-primary text-primary-foreground grid place-items-center font-bold">
                PG
              </div>
              <div className="text-lg font-semibold">PGwallah</div>
              <div className="ml-4 px-2 py-0.5 rounded bg-secondary text-secondary-foreground text-xs font-medium uppercase">
                {role}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Link href="/">
                <Button variant="outline" size="sm">
                  <Home className="mr-2 h-4 w-4" />
                  Home
                </Button>
              </Link>
              <Button variant="destructive" size="sm" onClick={logout}>
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </Button>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="mx-auto max-w-6xl px-4 py-8">
          {/* Greeting */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold tracking-tight">Welcome, {displayName} 👋</h1>
            <p className="mt-1 text-muted-foreground">
              This is your dashboard. Quick stats and shortcuts appear below.
            </p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard title="Role" value={role.toString().toUpperCase()} icon={User} />
            <StatCard title="Email" value={user?.email || '-'} icon={Mail} />
            <StatCard title="Phone" value={user?.phone || '-'} icon={Phone} />
            <StatCard title="Status" value={user?.is_active ? 'Active' : 'Inactive'} icon={Activity} />
          </div>

          {/* Quick Actions */}
          <section className="mt-8">
            <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Link href="/demo">
                <Card className="hover:bg-muted/50 transition-colors cursor-pointer h-full">
                  <CardHeader>
                    <CardTitle className="text-base">Demo Page</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      View the demo content and sample UI blocks.
                    </p>
                    <div className="flex items-center text-sm text-primary font-medium">
                      View Demo <ArrowRight className="ml-1 h-4 w-4" />
                    </div>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/auth/login">
                <Card className="hover:bg-muted/50 transition-colors cursor-pointer h-full">
                  <CardHeader>
                    <CardTitle className="text-base">Go to Login</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      Return to login screen to test authentication flow.
                    </p>
                    <div className="flex items-center text-sm text-primary font-medium">
                      Login <ArrowRight className="ml-1 h-4 w-4" />
                    </div>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/">
                <Card className="hover:bg-muted/50 transition-colors cursor-pointer h-full">
                  <CardHeader>
                    <CardTitle className="text-base">Explore Home</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      Go back to the landing page.
                    </p>
                    <div className="flex items-center text-sm text-primary font-medium">
                      Home <ArrowRight className="ml-1 h-4 w-4" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </div>
          </section>

          {/* Tenant Info (if available) */}
          {user?.role === 'tenant' && (
            <section className="mt-8">
              <h2 className="text-lg font-semibold mb-4">Tenant Profile</h2>
              <Card>
                <CardContent className="pt-6">
                  <dl className="grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2">
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">Occupation</dt>
                      <dd className="mt-1 text-sm">{tenantProfile?.occupation || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">Company</dt>
                      <dd className="mt-1 text-sm">{tenantProfile?.company || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">Emergency Contact</dt>
                      <dd className="mt-1 text-sm">
                        {tenantProfile?.emergency_contact_name || '-'}{' '}
                        {tenantProfile?.emergency_contact_phone
                          ? `(${tenantProfile.emergency_contact_phone})`
                          : ''}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">Address</dt>
                      <dd className="mt-1 text-sm">
                        {[tenantProfile?.address_line1, tenantProfile?.address_line2]
                          .filter(Boolean)
                          .join(', ') || '-'}
                        <br />
                        {[tenantProfile?.city, tenantProfile?.state, tenantProfile?.pincode]
                          .filter(Boolean)
                          .join(', ')}
                      </dd>
                    </div>
                  </dl>
                </CardContent>
              </Card>
            </section>
          )}

          {/* Help */}
          <section className="mt-8">
            <Card>
              <CardContent className="pt-6">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div>
                    <h3 className="text-base font-medium">Need help?</h3>
                    <p className="mt-1 text-sm text-muted-foreground">
                      This is a starter dashboard. We can add role-based widgets (bookings, invoices,
                      mess coupons, orders) next.
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Link href="/demo">
                      <Button>Explore Demo</Button>
                    </Link>
                    <Button variant="outline" onClick={logout}>Logout</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>
        </main>

        <footer className="mt-12 border-t bg-background">
          <div className="mx-auto max-w-6xl px-4 py-6 text-sm text-muted-foreground">
            PGwallah • {new Date().getFullYear()}
          </div>
        </footer>
      </div>
    </>
  );
}
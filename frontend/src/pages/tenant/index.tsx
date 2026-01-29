import { useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import TenantNav from '@/components/nav/TenantNav';
import { useAuth, useUser } from '@/store/auth-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowRight } from 'lucide-react';

function ServiceCard(props: { title: string; description: string; href: string; badge?: string }) {
  const { title, description, href, badge } = props;
  return (
    <Link href={href}>
      <Card className="hover:bg-muted/50 transition-colors cursor-pointer h-full">
        <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
          <CardTitle className="text-lg font-semibold">{title}</CardTitle>
          {badge && (
            <span className="px-2 py-0.5 rounded text-xs bg-secondary text-secondary-foreground font-medium">
              {badge}
            </span>
          )}
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">{description}</p>
          <div className="flex items-center text-sm text-primary font-medium">
            Open <ArrowRight className="ml-1 h-4 w-4" />
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

export default function TenantHomePage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, getProfile } = useAuth();
  const { user } = useUser();

  // Guard + ensure profile is loaded
  useEffect(() => {
    const init = async () => {
      try {
        await getProfile();
      } catch {
        // ignore, store handles auth errors
      }
    };
    init();
  }, [getProfile]);

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

  return (
    <>
      <Head>
        <title>Tenant Home • PGwallah</title>
      </Head>

      <TenantNav />

      <main className="mx-auto max-w-6xl px-4 py-8">
        {/* Greeting */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight">
            Hello, {user?.full_name || user?.email || 'Tenant'} 👋
          </h1>
          <p className="mt-1 text-muted-foreground">
            Choose a service below or go to your{' '}
            <Link href="/dashboard" className="text-primary font-medium hover:underline">
              Dashboard
            </Link>
            .
          </p>
        </div>

        {/* Services available now */}
        <section>
          <h2 className="text-lg font-semibold mb-4">Available Services</h2>
          <p className="text-sm text-muted-foreground mb-4">
            These services are live through the API gateway and ready to use.
          </p>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <ServiceCard
              title="Payments"
              href="/tenant/payments"
              description="Create UPI payment intents, manage subscriptions, and view receipts."
              badge="Live"
            />
            <ServiceCard
              title="Invoices"
              href="/tenant/invoices"
              description="View and download your invoices. Send copies to your email."
              badge="Live"
            />
            <ServiceCard
              title="Food Orders"
              href="/tenant/orders"
              description="Place and track food orders from the mess kitchen."
              badge="Live"
            />
            <ServiceCard
              title="Profile"
              href="/tenant/profile"
              description="View and update your personal and tenant profile details."
              badge="Live"
            />
          </div>
        </section>

        {/* Additional Services */}
        <section className="mt-10">
          <h2 className="text-lg font-semibold mb-4">More Services</h2>
          <p className="text-sm text-muted-foreground mb-4">Additional features for your stay.</p>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <ServiceCard
              title="Room Booking"
              href="/tenant/booking"
              description="Browse properties, check availability, and request bookings."
              badge="Live"
            />
            <ServiceCard
              title="Mess & Menu"
              href="/tenant/mess"
              description="Daily mess menu, meal coupons, and attendance."
              badge="Live"
            />
            <ServiceCard
              title="Notifications"
              href="/tenant/notifications"
              description="SMS and email alerts for invoices, payments, and updates."
              badge="Live"
            />
          </div>
        </section>
      </main>
    </>
  );
}
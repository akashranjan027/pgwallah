import { useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import TenantNav from '@/components/nav/TenantNav';
import { useAuth, useUser } from '@/store/auth-store';

function ServiceCard(props: { title: string; description: string; href: string; badge?: string }) {
  const { title, description, href, badge } = props;
  return (
    <Link
      href={href}
      className="rounded-xl border border-gray-200 bg-white p-5 hover:shadow-md transition group"
    >
      <div className="flex items-start justify-between">
        <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-700">{title}</h3>
        {badge ? (
          <span className="px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600">{badge}</span>
        ) : null}
      </div>
      <p className="mt-2 text-sm text-gray-600">{description}</p>
      <div className="mt-3 text-sm text-primary-700 font-medium">Open →</div>
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
      <div className="min-h-screen grid place-items-center bg-gray-50">
        <div className="flex items-center space-x-3 text-gray-600">
          <div className="spinner-lg" />
          <span>Loading your tenant home…</span>
        </div>
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
          <h1 className="text-2xl font-bold text-gray-900">
            Hello, {user?.full_name || user?.email || 'Tenant'} 👋
          </h1>
          <p className="mt-1 text-gray-600">
            Choose a service below or go to your{' '}
            <Link href="/dashboard" className="text-primary-700 font-medium hover:underline">
              Dashboard
            </Link>
            .
          </p>
        </div>

        {/* Services available now */}
        <section>
          <h2 className="text-lg font-semibold text-gray-900">Available Services</h2>
          <p className="text-sm text-gray-600">
            These services are live through the API gateway and ready to use.
          </p>

          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
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

        {/* Coming soon */}
        <section className="mt-10">
          <h2 className="text-lg font-semibold text-gray-900">Coming Soon</h2>
          <p className="text-sm text-gray-600">These will appear here when enabled.</p>

          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <ServiceCard
              title="Room Booking"
              href="#"
              description="Browse properties, check availability, and request bookings."
              badge="Soon"
            />
            <ServiceCard
              title="Mess & Attendance"
              href="#"
              description="Daily mess menu, attendance via QR, and meal coupons."
              badge="Soon"
            />
            <ServiceCard
              title="Notifications"
              href="#"
              description="SMS and email alerts for invoices, payments, and updates."
              badge="Soon"
            />
          </div>
        </section>
      </main>
    </>
  );
}
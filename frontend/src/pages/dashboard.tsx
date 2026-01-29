import { useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth, useUser } from '@/store/auth-store';

function StatCard(props: { title: string; value: string | number; subtitle?: string }) {
  const { title, value, subtitle } = props;
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="text-sm text-gray-500">{title}</div>
      <div className="mt-2 text-2xl font-semibold text-gray-900">{value}</div>
      {subtitle ? <div className="mt-1 text-xs text-gray-400">{subtitle}</div> : null}
    </div>
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
      <div className="min-h-screen grid place-items-center bg-gray-50">
        <div className="flex items-center space-x-3 text-gray-600">
          <div className="spinner-lg" />
          <span>Loading dashboard…</span>
        </div>
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

      <div className="min-h-screen bg-gray-50">
        {/* Top Bar */}
        <header className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-gray-200">
          <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-9 w-9 rounded-lg bg-primary-600 text-white grid place-items-center font-bold">
                PG
              </div>
              <div className="text-lg font-semibold text-gray-900">PGwallah</div>
              <div className="ml-4 px-2 py-0.5 rounded bg-gray-100 text-xs text-gray-600">
                {role.toString().toUpperCase()}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Link
                href="/"
                className="inline-flex items-center rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
              >
                Home
              </Link>
              <button
                onClick={logout}
                className="inline-flex items-center rounded-lg bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="mx-auto max-w-6xl px-4 py-8">
          {/* Greeting */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Welcome, {displayName} 👋</h1>
            <p className="mt-1 text-gray-600">
              This is your dashboard. Quick stats and shortcuts appear below.
            </p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard title="Role" value={role} />
            <StatCard title="Email" value={user?.email || '-'} />
            <StatCard title="Phone" value={user?.phone || '-'} />
            <StatCard title="Status" value={user?.is_active ? 'Active' : 'Inactive'} />
          </div>

          {/* Quick Actions */}
          <section className="mt-8">
            <h2 className="text-lg font-semibold text-gray-900">Quick Actions</h2>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Link
                href="/demo"
                className="rounded-xl border border-gray-200 bg-white p-4 hover:shadow-md transition"
              >
                <div className="text-gray-900 font-medium">Demo Page</div>
                <div className="text-sm text-gray-500">
                  View the demo content and sample UI blocks.
                </div>
              </Link>

              <Link
                href="/auth/login"
                className="rounded-xl border border-gray-200 bg-white p-4 hover:shadow-md transition"
              >
                <div className="text-gray-900 font-medium">Go to Login</div>
                <div className="text-sm text-gray-500">
                  Return to login screen to test authentication flow.
                </div>
              </Link>

              <Link
                href="/"
                className="rounded-xl border border-gray-200 bg-white p-4 hover:shadow-md transition"
              >
                <div className="text-gray-900 font-medium">Explore Home</div>
                <div className="text-sm text-gray-500">
                  Go back to the landing page.
                </div>
              </Link>
            </div>
          </section>

          {/* Tenant Info (if available) */}
          {user?.role === 'tenant' && (
            <section className="mt-8">
              <h2 className="text-lg font-semibold text-gray-900">Tenant Profile</h2>
              <div className="mt-4 rounded-xl border border-gray-200 bg-white p-4">
                <dl className="grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2">
                  <div>
                    <dt className="text-sm text-gray-500">Occupation</dt>
                    <dd className="mt-1 text-gray-900">{tenantProfile?.occupation || '-'}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Company</dt>
                    <dd className="mt-1 text-gray-900">{tenantProfile?.company || '-'}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Emergency Contact</dt>
                    <dd className="mt-1 text-gray-900">
                      {tenantProfile?.emergency_contact_name || '-'}{' '}
                      {tenantProfile?.emergency_contact_phone
                        ? `(${tenantProfile.emergency_contact_phone})`
                        : ''}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Address</dt>
                    <dd className="mt-1 text-gray-900">
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
              </div>
            </section>
          )}

          {/* Help */}
          <section className="mt-8">
            <div className="rounded-xl border border-gray-200 bg-white p-4">
              <h3 className="text-base font-medium text-gray-900">Need help?</h3>
              <p className="mt-1 text-sm text-gray-600">
                This is a starter dashboard. We can add role-based widgets (bookings, invoices,
                mess coupons, orders) next.
              </p>
              <div className="mt-3 flex gap-2">
                <Link
                  href="/demo"
                  className="inline-flex items-center rounded-lg bg-primary-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-700"
                >
                  Explore Demo
                </Link>
                <button
                  onClick={logout}
                  className="inline-flex items-center rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
                >
                  Logout
                </button>
              </div>
            </div>
          </section>
        </main>

        <footer className="mt-12 border-t border-gray-200 bg-white">
          <div className="mx-auto max-w-6xl px-4 py-6 text-sm text-gray-500">
            PGwallah • {new Date().getFullYear()}
          </div>
        </footer>
      </div>
    </>
  );
}
import { useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth, useUser } from '@/store/auth-store';

export default function AdminHomePage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, getProfile, logout } = useAuth();
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
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner-lg"></div>
      </div>
    );
  }

  const displayName = user?.full_name || user?.email || 'Admin';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Nav */ }
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-primary-600 text-white grid place-items-center font-bold">PG</div>
            <div>
              <div className="text-base font-semibold text-gray-900">PGwallah Admin</div>
              <div className="text-xs text-gray-500">Signed in as {displayName}</div>
            </div>
            <div className="ml-2 px-2 py-0.5 rounded bg-gray-100 text-xs text-gray-600">ADMIN</div>
          </div>

          <div className="flex items-center gap-2">
            <Link href="/dashboard" className="btn btn-secondary btn-sm">User Dashboard</Link>
            <button onClick={logout} className="btn btn-danger btn-sm">Sign out</button>
          </div>
        </div>
      </nav>

      {/* Content */ }
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-bold text-gray-900">Admin Console</h1>
        <p className="mt-1 text-gray-600">Manage PGs, admins, memberships, and payments.</p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
          {/* PG Management */ }
          <Link href="/admin/pg" className="card p-6 hover:shadow-lg transition block">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-primary-100 text-primary-600 grid place-items-center">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0h6" />
                </svg>
              </div>
              <div>
                <div className="font-semibold">PG Management</div>
                <div className="text-sm text-gray-500">Create PGs, assign admins</div>
              </div>
            </div>
          </Link>

          {/* Memberships */ }
          <Link href="/admin/memberships" className="card p-6 hover:shadow-lg transition block">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-secondary-100 text-secondary-600 grid place-items-center">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5V4H2v16h5m10 0v-6a2 2 0 10-4 0v6m4 0H7" />
                </svg>
              </div>
              <div>
                <div className="font-semibold">Memberships</div>
                <div className="text-sm text-gray-500">Assign tenants, rooms, rents</div>
              </div>
            </div>
          </Link>

          {/* Rent Payments */ }
          <Link href="/admin/rent" className="card p-6 hover:shadow-lg transition block">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-success-100 text-success-600 grid place-items-center">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8V7m0 1v8m0 0v1" />
                </svg>
              </div>
              <div>
                <div className="font-semibold">Rent Payments</div>
                <div className="text-sm text-gray-500">View and record rent</div>
              </div>
            </div>
          </Link>

          {/* Advance Payments */ }
          <Link href="/admin/advance" className="card p-6 hover:shadow-lg transition block">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-warning-100 text-warning-600 grid place-items-center">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v8m0 0l-3-3m3 3l3-3" />
                </svg>
              </div>
              <div>
                <div className="font-semibold">Advance Payments</div>
                <div className="text-sm text-gray-500">Record advances / deposits</div>
              </div>
            </div>
          </Link>

          {/* Invoices */ }
          <Link href="/admin/invoices" className="card p-6 hover:shadow-lg transition block">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-indigo-100 text-indigo-600 grid place-items-center">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6M7 4h7l4 4v12a2 2 0 01-2 2H7a2 2 0 01-2-2V6a2 2 0 012-2z" />
                </svg>
              </div>
              <div>
                <div className="font-semibold">Invoices</div>
                <div className="text-sm text-gray-500">Generate and download</div>
              </div>
            </div>
          </Link>
        </div>

        <div className="mt-8 p-4 bg-blue-50 border border-blue-100 rounded">
          <p className="text-sm text-blue-700">
            Tip: Use the Admin menu cards above to navigate. API routes for PGs, memberships, and payments are wired via the gateway.
          </p>
        </div>
      </main>
    </div>
  );
}
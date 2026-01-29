import { useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import TenantNav from '@/components/nav/TenantNav';
import { useAuth } from '@/store/auth-store';
import Link from 'next/link';

export default function TenantPaymentsPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, getProfile } = useAuth();

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

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen grid place-items-center bg-gray-50">
        <div className="flex items-center space-x-3 text-gray-600">
          <div className="spinner-lg" />
          <span>Loading payments…</span>
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Tenant • Payments</title>
      </Head>

      <TenantNav />

      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Payments</h1>
          <p className="mt-1 text-gray-600">
            Create UPI intents, manage subscriptions, and view receipts.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <section className="rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-gray-900">UPI Intents</h2>
            <p className="mt-1 text-sm text-gray-600">
              Generate a payment intent to pay your rent or other charges.
            </p>

            <div className="mt-4 flex items-center gap-2">
              <Link
                href="#"
                className="inline-flex items-center rounded-md bg-primary-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-700"
              >
                Create Intent
              </Link>
              <Link
                href="#"
                className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
              >
                View Intents
              </Link>
            </div>

            <div className="mt-3 text-xs text-gray-400">
              API: /api/payments/intents (via gateway)
            </div>
          </section>

          <section className="rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-gray-900">Subscriptions</h2>
            <p className="mt-1 text-sm text-gray-600">
              Manage recurring rent subscriptions and billing cycles.
            </p>

            <div className="mt-4 flex items-center gap-2">
              <Link
                href="#"
                className="inline-flex items-center rounded-md bg-primary-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-700"
              >
                New Subscription
              </Link>
              <Link
                href="#"
                className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
              >
                My Subscriptions
              </Link>
            </div>

            <div className="mt-3 text-xs text-gray-400">
              API: /api/payments/subscriptions (via gateway)
            </div>
          </section>

          <section className="rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-gray-900">Receipts</h2>
            <p className="mt-1 text-sm text-gray-600">
              Access payment receipts and download them for your records.
            </p>

            <div className="mt-4 flex items-center gap-2">
              <Link
                href="#"
                className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
              >
                View Receipts
              </Link>
            </div>

            <div className="mt-3 text-xs text-gray-400">
              API: /api/payments/receipts (via gateway)
            </div>
          </section>
        </div>

        <section className="mt-8">
          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <h3 className="text-base font-medium text-gray-900">Notes</h3>
            <p className="mt-1 text-sm text-gray-600">
              This page is a functional placeholder. Next steps are to wire these buttons to forms
              and tables using the existing API client and backend endpoints.
            </p>
          </div>
        </section>
      </main>
    </>
  );
}
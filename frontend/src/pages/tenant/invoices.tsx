import { useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import TenantNav from '@/components/nav/TenantNav';
import { useAuth } from '@/store/auth-store';
import Link from 'next/link';

export default function TenantInvoicesPage() {
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
          <span>Loading invoices…</span>
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Tenant • Invoices</title>
      </Head>

      <TenantNav />

      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Invoices</h1>
          <p className="mt-1 text-gray-600">
            View your invoices, download PDFs, and request email copies.
          </p>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">My Invoices</h2>
            <div className="flex items-center gap-2">
              <Link
                href="#"
                className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
              >
                Refresh
              </Link>
            </div>
          </div>
          <p className="mt-2 text-sm text-gray-600">
            This is a placeholder. Next step is to list invoices from the API.
          </p>
          <div className="mt-3 text-xs text-gray-400">
            API: /api/invoices (via gateway), PDF: /api/invoices/:id/pdf, Send: /api/invoices/:id/send
          </div>

          <div className="mt-4 rounded-lg border border-dashed border-gray-300 p-6 text-sm text-gray-500">
            No invoices loaded yet. Connect table to the invoicing service to display data.
          </div>
        </div>
      </main>
    </>
  );
}
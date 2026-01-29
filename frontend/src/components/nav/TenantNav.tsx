import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '@/store/auth-store';

function NavLink({
  href,
  label,
  current,
}: {
  href: string;
  label: string;
  current: boolean;
}) {
  return (
    <Link
      href={href}
      className={[
        'inline-flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
        current
          ? 'bg-primary-50 text-primary-700'
          : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900',
      ].join(' ')}
    >
      {label}
    </Link>
  );
}

export default function TenantNav() {
  const router = useRouter();
  const { user, logout } = useAuth();

  const items = [
    { href: '/tenant', label: 'Home' },
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/tenant/payments', label: 'Payments' },
    { href: '/tenant/invoices', label: 'Invoices' },
    { href: '/tenant/orders', label: 'Orders' },
    { href: '/tenant/profile', label: 'Profile' },
  ];

  return (
    <header className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-gray-200">
      <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/tenant" className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-lg bg-primary-600 text-white grid place-items-center font-bold">
              PG
            </div>
            <div className="text-lg font-semibold text-gray-900">PGwallah</div>
          </Link>
          <div className="ml-2 px-2 py-0.5 rounded bg-gray-100 text-xs text-gray-600">
            {(user?.role || 'tenant').toString().toUpperCase()}
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-1">
          {items.map((item) => (
            <NavLink
              key={item.href}
              href={item.href}
              label={item.label}
              current={router.pathname === item.href}
            />
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <button
            onClick={logout}
            className="inline-flex items-center rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Mobile nav */}
      <div className="md:hidden border-t border-gray-200 bg-white px-2 py-2">
        <div className="flex flex-wrap gap-2">
          {items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={[
                'inline-flex items-center rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                router.pathname === item.href
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900',
              ].join(' ')}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </div>
    </header>
  );
}
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import { cn } from '@/utils/cn';
import { LogOut } from 'lucide-react';

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
      className={cn(
        'inline-flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
        current
          ? 'bg-primary/10 text-primary'
          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
      )}
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
    { href: '/tenant/mess', label: 'Mess' },
    { href: '/tenant/booking', label: 'Booking' },
    { href: '/tenant/notifications', label: 'Alerts' },
    { href: '/tenant/profile', label: 'Profile' },
  ];

  return (
    <header className="sticky top-0 z-10 bg-background/80 backdrop-blur border-b">
      <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/tenant" className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-lg bg-primary text-primary-foreground grid place-items-center font-bold">
              PG
            </div>
            <div className="text-lg font-semibold">PGwallah</div>
          </Link>
          <div className="ml-2 px-2 py-0.5 rounded bg-secondary text-secondary-foreground text-xs font-medium uppercase">
            {(user?.role || 'tenant')}
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
          <Button variant="destructive" size="sm" onClick={logout}>
            <LogOut className="mr-2 h-4 w-4" />
            Logout
          </Button>
        </div>
      </div>

      {/* Mobile nav */}
      <div className="md:hidden border-t bg-background px-2 py-2">
        <div className="flex flex-wrap gap-2">
          {items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'inline-flex items-center rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                router.pathname === item.href
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </div>
    </header>
  );
}
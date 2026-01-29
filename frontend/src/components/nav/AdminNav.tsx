import Link from 'next/link';
import { useAuth, useUser } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import { LogOut } from 'lucide-react';

export default function AdminNav() {
    const { logout } = useAuth();
    const { user } = useUser();
    const displayName = user?.full_name || user?.email || 'Admin';

    return (
        <nav className="bg-background/80 backdrop-blur border-b sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Link href="/admin" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                        <div className="h-9 w-9 rounded-lg bg-primary text-primary-foreground grid place-items-center font-bold">PG</div>
                        <div>
                            <div className="text-base font-semibold">PGwallah Admin</div>
                            <div className="text-xs text-muted-foreground">Signed in as {displayName}</div>
                        </div>
                    </Link>
                    <div className="ml-2 px-2 py-0.5 rounded bg-secondary text-secondary-foreground text-xs font-medium uppercase">ADMIN</div>
                </div>

                <div className="flex items-center gap-2">
                    <Link href="/dashboard">
                        <Button variant="outline" size="sm">User Dashboard</Button>
                    </Link>
                    <Button variant="destructive" size="sm" onClick={logout}>
                        <LogOut className="mr-2 h-4 w-4" />
                        Sign out
                    </Button>
                </div>
            </div>
        </nav>
    );
}

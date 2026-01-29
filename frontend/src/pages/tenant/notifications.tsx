import { useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import TenantNav from '@/components/nav/TenantNav';
import { useAuth, useUser } from '@/store/auth-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
    Bell,
    Mail,
    MessageSquare,
    Clock,
    CheckCircle,
    RefreshCw,
    BellOff,
    Filter
} from 'lucide-react';
import { API_CONFIG, API_ENDPOINTS } from '@/config/api';
import toast from 'react-hot-toast';

interface Notification {
    id: string;
    user_id: string;
    notification_type: string;
    recipient?: string;
    subject?: string;
    message: string;
    status: string;
    created_at: string;
    sent_at?: string;
}

const typeIcons: Record<string, React.ReactNode> = {
    email: <Mail className="h-4 w-4" />,
    sms: <MessageSquare className="h-4 w-4" />,
    push: <Bell className="h-4 w-4" />,
};

const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    sent: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    read: 'bg-blue-100 text-blue-800',
};

export default function TenantNotificationsPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading } = useAuth();
    const { user } = useUser();

    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('all');

    // Auth guard
    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.replace('/auth/login');
        }
    }, [isLoading, isAuthenticated, router]);

    // Fetch notifications
    useEffect(() => {
        const fetchNotifications = async () => {
            if (!user?.id) return;
            try {
                const token = localStorage.getItem('pgwallah_access_token');
                const res = await fetch(
                    `${API_CONFIG.BASE_URL}${API_ENDPOINTS.NOTIFICATION.NOTIFICATIONS}?user_id=${user.id}`,
                    { headers: token ? { Authorization: `Bearer ${token}` } : {} }
                );
                if (res.ok) {
                    const data = await res.json();
                    setNotifications(data.items || []);
                }
            } catch (error) {
                console.error('Failed to fetch notifications:', error);
            } finally {
                setLoading(false);
            }
        };
        if (user?.id) fetchNotifications();
    }, [user?.id]);

    if (isLoading || !isAuthenticated) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    const filteredNotifications = filter === 'all'
        ? notifications
        : notifications.filter(n => n.notification_type === filter);

    const unreadCount = notifications.filter(n => n.status !== 'read').length;

    return (
        <>
            <Head>
                <title>Notifications • PGwallah</title>
            </Head>

            <TenantNav />

            <main className="mx-auto max-w-4xl px-4 py-8">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                            <Bell className="h-8 w-8" />
                            Notifications
                        </h1>
                        <p className="mt-1 text-muted-foreground">
                            {unreadCount > 0
                                ? `You have ${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}`
                                : 'All caught up!'}
                        </p>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Refresh
                    </Button>
                </div>

                {/* Filters */}
                <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
                    {['all', 'email', 'sms', 'push'].map(type => (
                        <Button
                            key={type}
                            variant={filter === type ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setFilter(type)}
                        >
                            {type === 'all' ? (
                                <Filter className="mr-2 h-4 w-4" />
                            ) : (
                                <span className="mr-2">{typeIcons[type]}</span>
                            )}
                            <span className="capitalize">{type}</span>
                        </Button>
                    ))}
                </div>

                {/* Notifications List */}
                {loading ? (
                    <div className="text-center py-12">
                        <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2 text-muted-foreground" />
                        <p className="text-muted-foreground">Loading notifications...</p>
                    </div>
                ) : filteredNotifications.length > 0 ? (
                    <div className="space-y-4">
                        {filteredNotifications.map(notification => (
                            <Card key={notification.id} className="hover:bg-muted/50 transition-colors">
                                <CardContent className="py-4">
                                    <div className="flex items-start gap-4">
                                        <div className={`h-10 w-10 rounded-full grid place-items-center ${notification.status === 'read'
                                                ? 'bg-muted text-muted-foreground'
                                                : 'bg-primary/10 text-primary'
                                            }`}>
                                            {typeIcons[notification.notification_type] || <Bell className="h-5 w-5" />}
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            {notification.subject && (
                                                <h3 className="font-semibold text-sm">{notification.subject}</h3>
                                            )}
                                            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                                                {notification.message}
                                            </p>
                                            <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                                                <span className="flex items-center gap-1">
                                                    <Clock className="h-3 w-3" />
                                                    {new Date(notification.created_at).toLocaleString()}
                                                </span>
                                                {notification.sent_at && (
                                                    <span className="flex items-center gap-1">
                                                        <CheckCircle className="h-3 w-3 text-green-500" />
                                                        Sent
                                                    </span>
                                                )}
                                            </div>
                                        </div>

                                        <div className="flex flex-col items-end gap-2">
                                            <Badge className={statusColors[notification.status] || 'bg-gray-100'}>
                                                {notification.status}
                                            </Badge>
                                            <Badge variant="outline" className="text-xs">
                                                {notification.notification_type}
                                            </Badge>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : (
                    <Card>
                        <CardContent className="py-12 text-center">
                            <BellOff className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                            <h3 className="text-lg font-medium mb-2">No notifications</h3>
                            <p className="text-muted-foreground text-sm">
                                {filter === 'all'
                                    ? "You don't have any notifications yet"
                                    : `No ${filter} notifications found`}
                            </p>
                        </CardContent>
                    </Card>
                )}

                {/* Info Card */}
                <Card className="mt-8 bg-blue-50/50 border-blue-100">
                    <CardContent className="py-4">
                        <div className="flex items-start gap-3">
                            <Mail className="h-5 w-5 text-blue-600 mt-0.5" />
                            <div>
                                <h4 className="font-medium text-blue-900">Stay Updated</h4>
                                <p className="text-sm text-blue-700 mt-1">
                                    Important notifications about payments, invoices, and updates will appear here.
                                    Make sure your email and phone are up to date in your profile.
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </main>
        </>
    );
}

import { useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useAuth, useUser } from '@/store/auth-store';
import TenantNav from '@/components/nav/TenantNav';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { User, Mail, Phone, MapPin, Briefcase } from 'lucide-react';

export default function TenantProfilePage() {
    const router = useRouter();
    const { isAuthenticated, isLoading, getProfile } = useAuth();
    const { user } = useUser();

    useEffect(() => {
        const init = async () => {
            try {
                await getProfile();
            } catch {
                // handled by store
            }
        };
        init();
    }, [getProfile]);

    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.replace('/auth/login?redirect=/tenant/profile');
        }
    }, [isAuthenticated, isLoading, router]);

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
                <title>Tenant • Profile</title>
            </Head>

            <div className="min-h-screen bg-muted/50">
                <TenantNav />

                <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="mb-6">
                        <h1 className="text-3xl font-bold tracking-tight">My Profile</h1>
                        <p className="mt-1 text-muted-foreground">Manage your personal information and preferences.</p>
                    </div>

                    <div className="grid gap-6">
                        {/* Personal Info */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Personal Information</CardTitle>
                                <CardDescription>Your basic contact details.</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex items-center gap-4">
                                    <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                        <User className="h-8 w-8" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-medium">{user?.full_name}</h3>
                                        <p className="text-sm text-muted-foreground">Tenant</p>
                                    </div>
                                </div>

                                <div className="grid gap-4 md:grid-cols-2 mt-4">
                                    <div className="space-y-1">
                                        <label className="text-sm font-medium text-muted-foreground">Email</label>
                                        <div className="flex items-center gap-2">
                                            <Mail className="h-4 w-4 text-muted-foreground" />
                                            <span>{user?.email}</span>
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-sm font-medium text-muted-foreground">Phone</label>
                                        <div className="flex items-center gap-2">
                                            <Phone className="h-4 w-4 text-muted-foreground" />
                                            <span>{user?.phone || 'Not provided'}</span>
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Additional Details (Placeholder) */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Additional Details</CardTitle>
                                <CardDescription>Employment and emergency contact info.</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="grid gap-4 md:grid-cols-2">
                                    <div className="space-y-1">
                                        <label className="text-sm font-medium text-muted-foreground">Occupation</label>
                                        <div className="flex items-center gap-2">
                                            <Briefcase className="h-4 w-4 text-muted-foreground" />
                                            <span>Software Engineer</span>
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-sm font-medium text-muted-foreground">Address</label>
                                        <div className="flex items-center gap-2">
                                            <MapPin className="h-4 w-4 text-muted-foreground" />
                                            <span>Bangalore, Karnataka</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="mt-6">
                                    <Button variant="outline">Edit Profile</Button>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </main>
            </div>
        </>
    );
}

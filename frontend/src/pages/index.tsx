import { useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useAuth } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Building2, CreditCard, Utensils, FileText, BarChart3, Bell } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuth();

  const defaultPathByRole = (role?: string) => {
    if (role === 'admin') return '/admin';
    if (role === 'staff') return '/dashboard';
    return '/tenant';
  };

  useEffect(() => {
    if (isAuthenticated) {
      router.replace(defaultPathByRole(user?.role));
    }
  }, [isAuthenticated, router, user?.role]);

  return (
    <div className="min-h-screen bg-background font-sans antialiased">
      {/* Navigation */}
      <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-2">
              <div className="bg-primary/10 p-2 rounded-lg">
                <Building2 className="h-6 w-6 text-primary" />
              </div>
              <span className="text-xl font-bold tracking-tight">PGwallah</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/auth/login">
                <Button variant="ghost">Sign In</Button>
              </Link>
              <Link href="/auth/register">
                <Button>Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-20 lg:py-32 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-4xl font-extrabold tracking-tight lg:text-6xl mb-6">
              Manage Your PG <br />
              <span className="text-primary">Like a Pro</span>
            </h1>
            <p className="text-xl text-muted-foreground mb-10 leading-relaxed">
              The all-in-one platform for modern PG operations. Streamline bookings,
              automate rent collection, and manage your mess efficiently.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/auth/register">
                <Button size="lg" className="h-12 px-8 text-lg">
                  Start Free Trial
                </Button>
              </Link>
              <Link href="/demo">
                <Button variant="outline" size="lg" className="h-12 px-8 text-lg">
                  View Demo
                </Button>
              </Link>
            </div>
            <div className="mt-12 flex items-center justify-center gap-8 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>No credit card required</span>
              </div>
              <div className="flex items-center gap-2">
                <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>14-day free trial</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-24 bg-muted/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight mb-4">Everything You Need</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Powerful features designed specifically for the Indian PG market.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <FeatureCard
              icon={<Building2 className="h-6 w-6" />}
              title="Room Booking"
              description="Easy room discovery, booking requests, and real-time availability management."
            />
            <FeatureCard
              icon={<CreditCard className="h-6 w-6" />}
              title="UPI Payments"
              description="Seamless Razorpay integration with UPI intents and automated rent collection."
            />
            <FeatureCard
              icon={<Utensils className="h-6 w-6" />}
              title="Mess Management"
              description="Digital attendance tracking, meal coupons, and kitchen inventory management."
            />
            <FeatureCard
              icon={<FileText className="h-6 w-6" />}
              title="Smart Invoicing"
              description="GST-ready invoices with automated monthly billing and PDF generation."
            />
            <FeatureCard
              icon={<BarChart3 className="h-6 w-6" />}
              title="Analytics"
              description="Comprehensive dashboards to track revenue, occupancy, and expenses."
            />
            <FeatureCard
              icon={<Bell className="h-6 w-6" />}
              title="Notifications"
              description="Automated SMS and email alerts for rent reminders and announcements."
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center gap-2 mb-4 md:mb-0">
              <Building2 className="h-5 w-5 text-muted-foreground" />
              <span className="text-sm font-semibold text-muted-foreground">PGwallah</span>
            </div>
            <p className="text-sm text-muted-foreground">
              &copy; 2024 PGwallah. Built for the Indian PG market.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <Card className="border-none shadow-md hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4 text-primary">
          {icon}
        </div>
        <CardTitle className="text-xl">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <CardDescription className="text-base">
          {description}
        </CardDescription>
      </CardContent>
    </Card>
  );
}
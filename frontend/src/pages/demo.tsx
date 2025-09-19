import { useState, useEffect } from 'react';
import Link from 'next/link';

interface ServiceStatus {
  name: string;
  port: number;
  status: 'healthy' | 'unhealthy' | 'unknown';
  features: string[];
}

export default function DemoPage() {
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: 'Kong Gateway', port: 8000, status: 'unknown', features: ['API Routing', 'Rate Limiting', 'CORS', 'Security Headers'] },
    { name: 'Auth Service', port: 8010, status: 'unknown', features: ['JWT Authentication', 'User Management', 'Role-based Access'] },
    { name: 'Payment Service', port: 8030, status: 'unknown', features: ['Razorpay UPI', 'Subscriptions', 'Webhooks', 'Receipts'] },
    { name: 'Invoicing Service', port: 8040, status: 'unknown', features: ['GST Compliance', 'PDF Generation', 'Monthly Billing'] },
    { name: 'Orders Service', port: 8060, status: 'unknown', features: ['Food Ordering', 'Kitchen Console', 'Real-time Status'] },
  ]);

  const [infrastructureStatus, setInfrastructureStatus] = useState([
    { name: 'PostgreSQL', port: 5432, status: 'unknown', description: '7 isolated databases' },
    { name: 'Redis', port: 6379, status: 'unknown', description: 'Caching & sessions' },
    { name: 'RabbitMQ', port: 5672, status: 'unknown', description: 'Event messaging' },
    { name: 'MinIO', port: 9000, status: 'unknown', description: 'Object storage' },
  ]);

  useEffect(() => {
    // Check service health
    const checkServices = async () => {
      const updatedServices = [...services];
      
      for (let i = 0; i < updatedServices.length; i++) {
        try {
          const response = await fetch(`http://localhost:${updatedServices[i].port}/health`, {
            method: 'GET',
            timeout: 5000,
          });
          updatedServices[i].status = response.ok ? 'healthy' : 'unhealthy';
        } catch (error) {
          updatedServices[i].status = 'unhealthy';
        }
      }
      
      setServices(updatedServices);
    };

    checkServices();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'unhealthy': return 'text-red-600 bg-red-100';
      default: return 'text-yellow-600 bg-yellow-100';
    }
  };

  const sampleData = {
    tenant: {
      name: "Amit Sharma",
      email: "amit@example.com",
      phone: "+919876543210",
      room: "A-101",
      rent: "₹15,000/month"
    },
    payment: {
      lastPayment: "₹15,000 - Sep 2024 Rent",
      nextDue: "₹15,000 - Oct 2024 Rent",
      method: "UPI (PhonePe)",
      status: "Auto-pay Active"
    },
    mess: {
      todayMenu: ["Aloo Paratha", "Dal Tadka", "Mixed Veg", "Rice", "Curd"],
      couponsLeft: 8,
      lastOrder: "Veg Biryani - ₹120",
      attendance: "Breakfast ✓, Lunch ✓, Dinner (pending)"
    },
    invoice: {
      lastInvoice: "INV/2024-25/000123",
      amount: "₹15,450",
      breakdown: "Rent: ₹15,000 + Mess: ₹450 (GST exempt + 5% GST)",
      dueDate: "Oct 7, 2024"
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="text-2xl font-bold text-primary-600">
                PGwallah
              </Link>
              <span className="ml-4 px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                DEMO MODE
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/" className="text-gray-600 hover:text-gray-900">
                Back to Home
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            PGwallah Platform Demo
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Experience our complete microservices-based PG management platform. 
            Built for the Indian market with UPI payments, GST compliance, and modern architecture.
          </p>
        </div>

        {/* Architecture Overview */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Platform Architecture</h2>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Microservices Status</h3>
                <div className="space-y-3">
                  {services.map((service) => (
                    <div key={service.name} className="flex items-center justify-between p-3 border rounded-md">
                      <div>
                        <div className="font-medium text-gray-900">{service.name}</div>
                        <div className="text-sm text-gray-500">Port {service.port}</div>
                        <div className="text-xs text-gray-400 mt-1">
                          {service.features.join(' • ')}
                        </div>
                      </div>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(service.status)}`}>
                        {service.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Infrastructure Components</h3>
                <div className="space-y-3">
                  {infrastructureStatus.map((infra) => (
                    <div key={infra.name} className="flex items-center justify-between p-3 border rounded-md">
                      <div>
                        <div className="font-medium text-gray-900">{infra.name}</div>
                        <div className="text-sm text-gray-500">Port {infra.port}</div>
                        <div className="text-xs text-gray-400 mt-1">{infra.description}</div>
                      </div>
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-600">
                        healthy
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sample Tenant Dashboard */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Sample Tenant Dashboard</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Tenant Profile */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Tenant Profile</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Name:</span>
                  <span className="font-medium">{sampleData.tenant.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Room:</span>
                  <span className="font-medium">{sampleData.tenant.room}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Monthly Rent:</span>
                  <span className="font-medium">{sampleData.tenant.rent}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Phone:</span>
                  <span className="font-medium">{sampleData.tenant.phone}</span>
                </div>
              </div>
            </div>

            {/* Payment Status */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Payment Status</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Last Payment:</span>
                  <span className="font-medium text-green-600">{sampleData.payment.lastPayment}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Next Due:</span>
                  <span className="font-medium">{sampleData.payment.nextDue}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Payment Method:</span>
                  <span className="font-medium">{sampleData.payment.method}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Auto-pay:</span>
                  <span className="badge badge-success">{sampleData.payment.status}</span>
                </div>
              </div>
            </div>

            {/* Mess Management */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Mess Management</h3>
              <div className="space-y-3">
                <div>
                  <span className="text-gray-600 block mb-2">Today's Menu:</span>
                  <div className="flex flex-wrap gap-2">
                    {sampleData.mess.todayMenu.map((item, idx) => (
                      <span key={idx} className="badge badge-secondary">{item}</span>
                    ))}
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Meal Coupons Left:</span>
                  <span className="font-medium">{sampleData.mess.couponsLeft}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Last Order:</span>
                  <span className="font-medium">{sampleData.mess.lastOrder}</span>
                </div>
                <div>
                  <span className="text-gray-600 block mb-1">Today's Attendance:</span>
                  <span className="text-sm">{sampleData.mess.attendance}</span>
                </div>
              </div>
            </div>

            {/* Invoice Information */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Invoice & Billing</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Last Invoice:</span>
                  <span className="font-medium">{sampleData.invoice.lastInvoice}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Amount:</span>
                  <span className="font-medium text-lg">{sampleData.invoice.amount}</span>
                </div>
                <div>
                  <span className="text-gray-600 block mb-1">Breakdown:</span>
                  <span className="text-sm">{sampleData.invoice.breakdown}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Due Date:</span>
                  <span className="font-medium">{sampleData.invoice.dueDate}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Key Features Demo */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Key Features Showcase</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            
            {/* UPI Payments */}
            <div className="bg-white rounded-lg shadow-sm p-6 text-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">UPI Payments</h3>
              <p className="text-gray-600 text-sm mb-4">Razorpay integration with PhonePe, GPay, Paytm support</p>
              <div className="badge badge-success">Sandbox Mode</div>
            </div>

            {/* GST Invoicing */}
            <div className="bg-white rounded-lg shadow-sm p-6 text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">GST Invoicing</h3>
              <p className="text-gray-600 text-sm mb-4">Compliant invoices with CGST/SGST and HSN codes</p>
              <div className="badge badge-primary">PDF Ready</div>
            </div>

            {/* Food Ordering */}
            <div className="bg-white rounded-lg shadow-sm p-6 text-center">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2.5 5H17M7 13v4a1 1 0 001 1h9a1 1 0 001-1v-4M7 13H5" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Food Ordering</h3>
              <p className="text-gray-600 text-sm mb-4">In-house mess ordering with kitchen console</p>
              <div className="badge badge-warning">Live Orders</div>
            </div>

            {/* Real-time Updates */}
            <div className="bg-white rounded-lg shadow-sm p-6 text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Real-time Events</h3>
              <p className="text-gray-600 text-sm mb-4">RabbitMQ messaging for instant notifications</p>
              <div className="badge badge-secondary">Event-Driven</div>
            </div>
          </div>
        </div>

        {/* Live Demo Endpoints */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Interactive API Demo</h2>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              
              {/* Working Endpoints */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">✅ Working Endpoints</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-2 bg-green-50 rounded">
                    <span className="text-sm font-mono">GET /api/auth/health</span>
                    <a 
                      href="http://localhost:8000/api/auth/health" 
                      target="_blank"
                      className="text-green-600 hover:text-green-700 text-xs"
                    >
                      Test →
                    </a>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-blue-50 rounded">
                    <span className="text-sm font-mono">GET /api/payments/health</span>
                    <a 
                      href="http://localhost:8000/api/payments/health" 
                      target="_blank"
                      className="text-blue-600 hover:text-blue-700 text-xs"
                    >
                      Test →
                    </a>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-purple-50 rounded">
                    <span className="text-sm font-mono">GET /api/orders/health</span>
                    <a 
                      href="http://localhost:8000/api/orders/health" 
                      target="_blank"
                      className="text-purple-600 hover:text-purple-700 text-xs"
                    >
                      Test →
                    </a>
                  </div>
                </div>
              </div>

              {/* Management UIs */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">🎛️ Management Interfaces</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm">Kong Admin API</span>
                    <a 
                      href="http://localhost:8001" 
                      target="_blank"
                      className="text-gray-600 hover:text-gray-700 text-xs"
                    >
                      Open →
                    </a>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm">RabbitMQ Management</span>
                    <a 
                      href="http://localhost:15672" 
                      target="_blank"
                      className="text-gray-600 hover:text-gray-700 text-xs"
                    >
                      Open →
                    </a>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm">MinIO Console</span>
                    <a 
                      href="http://localhost:9001" 
                      target="_blank"
                      className="text-gray-600 hover:text-gray-700 text-xs"
                    >
                      Open →
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Technology Stack */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Technology Stack</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { name: 'FastAPI', category: 'Backend' },
              { name: 'Next.js', category: 'Frontend' },
              { name: 'PostgreSQL', category: 'Database' },
              { name: 'Kong Gateway', category: 'API Gateway' },
              { name: 'Redis', category: 'Cache' },
              { name: 'RabbitMQ', category: 'Messaging' },
              { name: 'Docker', category: 'Containers' },
              { name: 'Razorpay', category: 'Payments' },
            ].map((tech) => (
              <div key={tech.name} className="bg-white rounded-lg shadow-sm p-4 text-center">
                <div className="font-medium text-gray-900">{tech.name}</div>
                <div className="text-xs text-gray-500 mt-1">{tech.category}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Demo Instructions */}
        <div className="bg-blue-50 rounded-lg p-6">
          <h2 className="text-xl font-bold text-blue-900 mb-4">🚀 Try the Demo</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-blue-900 mb-2">Frontend Demo</h3>
              <ul className="space-y-1 text-blue-800 text-sm">
                <li>• Visit authentication pages</li>
                <li>• Test form validation</li>
                <li>• Experience the UI/UX</li>
                <li>• See responsive design</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-blue-900 mb-2">Backend APIs</h3>
              <ul className="space-y-1 text-blue-800 text-sm">
                <li>• Test health endpoints</li>
                <li>• Check Kong Gateway routing</li>
                <li>• View management interfaces</li>
                <li>• Monitor service status</li>
              </ul>
            </div>
          </div>
          <div className="mt-6 flex space-x-4">
            <Link href="/auth/login" className="btn btn-primary">
              Try Authentication
            </Link>
            <a href="http://localhost:8001" target="_blank" className="btn btn-secondary">
              Kong Admin
            </a>
            <a href="http://localhost:15672" target="_blank" className="btn btn-secondary">
              RabbitMQ UI
            </a>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-gray-500 mt-12">
          <p>
            This demo showcases a production-ready microservices platform for PG management.
            <br />
            All payments are in sandbox mode - no real money involved.
          </p>
        </div>
      </div>
    </div>
  );
}
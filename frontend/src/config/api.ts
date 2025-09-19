export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
} as const;

export const API_ENDPOINTS = {
  // Auth endpoints
  AUTH: {
    REGISTER: '/api/auth/register',
    LOGIN: '/api/auth/login',
    REFRESH: '/api/auth/refresh',
    PROFILE: '/api/auth/me',
    CHANGE_PASSWORD: '/api/auth/change-password',
    JWKS: '/api/auth/.well-known/jwks.json',
    HEALTH: '/api/auth/health',
  },
  // Booking endpoints (for future use)
  BOOKING: {
    PROPERTIES: '/api/booking/properties',
    ROOMS: '/api/booking/rooms',
    AVAILABILITY: '/api/booking/availability',
    REQUESTS: '/api/booking/requests',
    HEALTH: '/api/booking/health',
  },
  // Payment endpoints (for future use)
  PAYMENT: {
    INTENTS: '/api/payments/intents',
    WEBHOOKS: '/api/payments/webhooks/razorpay',
    SUBSCRIPTIONS: '/api/payments/subscriptions',
    RECEIPTS: '/api/payments/receipts',
    // Dummy rent payment (no gateway)
    DUMMY_RENT: '/api/payments/dummy/rent',
    // Admin listing of rent payments
    ADMIN_RENT: '/api/payments/admin/rent',
    HEALTH: '/api/payments/health',
  },
  // Invoicing endpoints (for future use)
  INVOICING: {
    INVOICES: '/api/invoices',
    PDF: (id: string) => `/api/invoices/${id}/pdf`,
    SEND: (id: string) => `/api/invoices/${id}/send`,
    HEALTH: '/api/invoices/health',
  },
  // Mess endpoints (for future use)
  MESS: {
    MENU: '/api/mess/menu',
    COUPONS: '/api/mess/coupons',
    ATTENDANCE: '/api/mess/attendance',
    MARK_ATTENDANCE: '/api/mess/attendance/mark',
    HEALTH: '/api/mess/health',
  },
  // Orders endpoints (for future use)
  ORDERS: {
    ORDERS: '/api/orders',
    KITCHEN: '/api/orders/kitchen',
    CANCEL: (id: string) => `/api/orders/${id}/cancel`,
    UPDATE_STATUS: (id: string) => `/api/orders/${id}/kitchen`,
    HEALTH: '/api/orders/health',
  },
  // Notification endpoints (for future use)
  NOTIFICATION: {
    NOTIFICATIONS: '/api/notify',
    TEMPLATES: '/api/notify/templates',
    HEALTH: '/api/notify/health',
  },
} as const;

// HTTP status codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,
} as const;

// Error codes
export const ERROR_CODES = {
  // Authentication errors
  INVALID_CREDENTIALS: 'AUTH_001',
  TOKEN_EXPIRED: 'AUTH_002',
  TOKEN_INVALID: 'AUTH_003',
  USER_NOT_FOUND: 'AUTH_004',
  USER_INACTIVE: 'AUTH_005',
  USER_LOCKED: 'AUTH_006',
  
  // Validation errors
  VALIDATION_ERROR: 'VAL_001',
  MISSING_REQUIRED_FIELD: 'VAL_002',
  INVALID_FORMAT: 'VAL_003',
  
  // Network errors
  NETWORK_ERROR: 'NET_001',
  TIMEOUT_ERROR: 'NET_002',
  CONNECTION_ERROR: 'NET_003',
  
  // Server errors
  INTERNAL_ERROR: 'SRV_001',
  SERVICE_UNAVAILABLE: 'SRV_002',
  RATE_LIMITED: 'SRV_003',
} as const;

// Request headers
export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
} as const;

// Storage keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'pgwallah_access_token',
  REFRESH_TOKEN: 'pgwallah_refresh_token',
  USER: 'pgwallah_user',
  TENANT_PROFILE: 'pgwallah_tenant_profile',
  PREFERENCES: 'pgwallah_preferences',
} as const;

// Cookie configuration
export const COOKIE_CONFIG = {
  ACCESS_TOKEN: {
    name: 'access_token',
    maxAge: 60 * 60, // 1 hour
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax' as const,
    httpOnly: false, // Need to access via JavaScript
  },
  REFRESH_TOKEN: {
    name: 'refresh_token',
    maxAge: 30 * 24 * 60 * 60, // 30 days
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax' as const,
    httpOnly: false, // Need to access via JavaScript
  },
  USER_ROLE: {
    name: 'user_role',
    maxAge: 24 * 60 * 60, // 24 hours
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax' as const,
    httpOnly: false,
  },
} as const;
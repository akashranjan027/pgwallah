export interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

export enum UserRole {
  TENANT = 'tenant',
  ADMIN = 'admin',
  STAFF = 'staff',
}

export interface TenantProfile {
  id: string;
  user_id: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  occupation?: string;
  company?: string;
  id_proof_type?: IDProofType;
  id_proof_number?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  pincode?: string;
  created_at: string;
  updated_at: string;
}

export enum IDProofType {
  AADHAAR = 'aadhaar',
  PAN = 'pan',
  PASSPORT = 'passport',
  DRIVING_LICENSE = 'driving_license',
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
  role?: UserRole;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface ProfileResponse {
  user: User;
  tenant_profile?: TenantProfile;
}

export interface UpdateProfileRequest {
  full_name?: string;
  phone?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  occupation?: string;
  company?: string;
  id_proof_type?: IDProofType;
  id_proof_number?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  pincode?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ApiError {
  error: string;
  message: string;
  code?: string;
  timestamp: string;
}

export interface MessageResponse {
  message: string;
  timestamp: string;
}

export interface JWKSResponse {
  keys: Array<{
    kty: string;
    use: string;
    kid: string;
    n: string;
    e: string;
    alg: string;
  }>;
}

// Form validation types
export interface LoginFormData {
  email: string;
  password: string;
}

export interface RegisterFormData {
  email: string;
  password: string;
  confirmPassword: string;
  full_name: string;
  phone?: string;
  role?: UserRole;
}

export interface ProfileFormData {
  full_name: string;
  phone?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  occupation?: string;
  company?: string;
  id_proof_type?: IDProofType;
  id_proof_number?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  pincode?: string;
}

export interface ChangePasswordFormData {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

// Auth state interface
export interface AuthState {
  user: User | null;
  tenantProfile: TenantProfile | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

// Auth store actions
export interface AuthActions {
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshTokens: () => Promise<void>;
  updateProfile: (data: UpdateProfileRequest) => Promise<void>;
  changePassword: (data: ChangePasswordRequest) => Promise<void>;
  getProfile: () => Promise<void>;
  setTokens: (tokens: { access_token: string; refresh_token: string; user: User }) => void;
  clearTokens: () => void;
}

export type AuthStore = AuthState & AuthActions;
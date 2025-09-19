import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { apiClient } from '@/lib/api-client';
import {
  AuthStore,
  User,
  TenantProfile,
  LoginRequest,
  RegisterRequest,
  UpdateProfileRequest,
  ChangePasswordRequest,
  TokenResponse,
  ProfileResponse,
} from '@/types/auth';

interface AuthState {
  user: User | null;
  tenantProfile: TenantProfile | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthActions {
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshTokens: () => Promise<void>;
  updateProfile: (data: UpdateProfileRequest) => Promise<void>;
  changePassword: (data: ChangePasswordRequest) => Promise<void>;
  getProfile: () => Promise<void>;
  setTokens: (tokens: { access_token: string; refresh_token: string; user: User }) => void;
  clearTokens: () => void;
  initialize: () => Promise<void>;
}

const initialState: AuthState = {
  user: null,
  tenantProfile: null,
  accessToken: null,
  refreshToken: null,
  isLoading: false,
  isAuthenticated: false,
};

export const useAuthStore = create<AuthState & AuthActions>()(
  persist(
    (set, get) => ({
      ...initialState,

      login: async (credentials: LoginRequest) => {
        set({ isLoading: true });
        try {
          const response: TokenResponse = await apiClient.login(
            credentials.email,
            credentials.password
          );

          const { access_token, refresh_token, user } = response;

          // Set tokens in API client
          apiClient.setTokens(access_token, refresh_token);

          // Update store state
          set({
            user,
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });

          // Get full profile if user is a tenant
          if (user.role === 'tenant') {
            await get().getProfile();
          }
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (data: RegisterRequest) => {
        set({ isLoading: true });
        try {
          const response: TokenResponse = await apiClient.register(data);

          const { access_token, refresh_token, user } = response;

          // Set tokens in API client
          apiClient.setTokens(access_token, refresh_token);

          // Update store state
          set({
            user,
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });

          // Get full profile if user is a tenant
          if (user.role === 'tenant') {
            await get().getProfile();
          }
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        // Clear API client tokens
        apiClient.clearTokens();

        // Reset store state
        set({
          ...initialState,
        });

        // Clear any additional local storage items
        if (typeof window !== 'undefined') {
          localStorage.removeItem('user_preferences');
        }

        // Redirect to login page
        if (typeof window !== 'undefined') {
          window.location.href = '/auth/login';
        }
      },

      refreshTokens: async () => {
        const { refreshToken } = get();
        
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        try {
          const response: TokenResponse = await apiClient.refreshTokens(refreshToken);
          
          const { access_token, refresh_token, user } = response;

          // Set tokens in API client
          apiClient.setTokens(access_token, refresh_token);

          // Update store state
          set({
            user,
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
          });
        } catch (error) {
          // Refresh failed, logout user
          get().logout();
          throw error;
        }
      },

      updateProfile: async (data: UpdateProfileRequest) => {
        set({ isLoading: true });
        try {
          const updatedUser: User = await apiClient.updateProfile(data);

          set({
            user: updatedUser,
            isLoading: false,
          });

          // Refresh full profile to get updated tenant profile
          await get().getProfile();
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      changePassword: async (data: ChangePasswordRequest) => {
        set({ isLoading: true });
        try {
          await apiClient.changePassword(data.current_password, data.new_password);
          
          set({ isLoading: false });

          // Note: The backend revokes all refresh tokens on password change
          // So we need to re-login or handle this gracefully
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      getProfile: async () => {
        try {
          const profileResponse: ProfileResponse = await apiClient.getProfile();
          
          set({
            user: profileResponse.user,
            tenantProfile: profileResponse.tenant_profile || null,
          });
        } catch (error) {
          // If profile fetch fails, user might need to re-authenticate
          if (error.code === 'AUTH_002' || error.code === 'AUTH_003') {
            get().logout();
          }
          throw error;
        }
      },

      setTokens: (tokens: { access_token: string; refresh_token: string; user: User }) => {
        const { access_token, refresh_token, user } = tokens;

        // Set tokens in API client
        apiClient.setTokens(access_token, refresh_token);

        // Update store state
        set({
          user,
          accessToken: access_token,
          refreshToken: refresh_token,
          isAuthenticated: true,
        });
      },

      clearTokens: () => {
        // Clear API client tokens
        apiClient.clearTokens();

        // Reset store state
        set({
          ...initialState,
        });
      },

      initialize: async () => {
        const { accessToken, refreshToken, user } = get();

        if (accessToken && refreshToken && user) {
          // Set tokens in API client
          apiClient.setTokens(accessToken, refreshToken);

          try {
            // Verify tokens are still valid by fetching profile
            await get().getProfile();
            
            set({ isAuthenticated: true });
          } catch (error) {
            // Tokens are invalid, try to refresh
            try {
              await get().refreshTokens();
            } catch (refreshError) {
              // Refresh failed, clear everything
              get().clearTokens();
            }
          }
        }
      },
    }),
    {
      name: 'auth-storage',
      // Avoid touching localStorage during SSR. Persist only in the browser.
      storage: typeof window !== 'undefined' ? createJSONStorage(() => localStorage) : undefined,
      partialize: (state) => ({
        user: state.user,
        tenantProfile: state.tenantProfile,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Helper hooks for specific auth state
export const useAuth = () => {
  const store = useAuthStore();
  return {
    user: store.user,
    tenantProfile: store.tenantProfile,
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    login: store.login,
    register: store.register,
    logout: store.logout,
    updateProfile: store.updateProfile,
    changePassword: store.changePassword,
    getProfile: store.getProfile,
    initialize: store.initialize,
  };
};

export const useUser = () => {
  const user = useAuthStore((state) => state.user);
  const tenantProfile = useAuthStore((state) => state.tenantProfile);
  return { user, tenantProfile };
};

export const useIsAuthenticated = () => {
  return useAuthStore((state) => state.isAuthenticated);
};

export const useIsLoading = () => {
  return useAuthStore((state) => state.isLoading);
};

// Role-based hooks
export const useIsTenant = () => {
  const user = useAuthStore((state) => state.user);
  return user?.role === 'tenant';
};

export const useIsAdmin = () => {
  const user = useAuthStore((state) => state.user);
  return user?.role === 'admin';
};

export const useIsStaff = () => {
  const user = useAuthStore((state) => state.user);
  return user?.role === 'staff';
};
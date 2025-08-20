import { apiClient } from './apiClient';
import {
  AuthToken,
  LoginRequest,
  User,
  ApiResponse,
} from '../types';

export class AuthService {
  async login(credentials: LoginRequest): Promise<AuthToken> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await apiClient.post<AuthToken>('/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    // Salvar token
    apiClient.setToken(response.access_token);
    
    return response;
  }

  async logout(): Promise<void> {
    apiClient.clearToken();
  }

  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/auth/me');
  }

  async refreshToken(): Promise<AuthToken> {
    return apiClient.post<AuthToken>('/auth/refresh');
  }

  isAuthenticated(): boolean {
    return apiClient.isAuthenticated();
  }
}

export const authService = new AuthService();

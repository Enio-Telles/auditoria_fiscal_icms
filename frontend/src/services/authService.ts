import { apiClient } from './apiClient';
import {
  AuthToken,
  LoginRequest,
  User,
  ApiResponse,
} from '../types';

// Modo demo para desenvolvimento
const DEMO_MODE = true;

export class AuthService {
  async login(credentials: LoginRequest): Promise<AuthToken> {
    // Modo demo para desenvolvimento
    if (DEMO_MODE) {
      return this.demoLogin(credentials);
    }

    // Código de autenticação real
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

  private async demoLogin(credentials: LoginRequest): Promise<AuthToken> {
    // Credenciais demo válidas
    const demoCredentials = [
      { username: 'admin@demo.com', password: 'admin123', role: 'admin', name: 'Admin Demo' },
      { username: 'user@demo.com', password: 'user123', role: 'user', name: 'User Demo' },
      { username: 'demo@demo.com', password: 'demo123', role: 'user', name: 'Demo User' },
      { username: 'auditor@demo.com', password: 'auditor123', role: 'auditor', name: 'Auditor Demo' }
    ];

    await new Promise(resolve => setTimeout(resolve, 500)); // Simular delay de rede

    const validUser = demoCredentials.find(
      cred => cred.username === credentials.username && cred.password === credentials.password
    );

    if (validUser) {
      const mockToken = `demo_token_${Date.now()}_${validUser.role}`;

      // Salvar dados do usuário demo
      const userData: User = {
        id: Date.now(),
        username: validUser.username,
        email: validUser.username,
        full_name: validUser.name,
        is_active: true,
        created_at: new Date().toISOString()
      };

      localStorage.setItem('demo_user', JSON.stringify(userData));
      apiClient.setToken(mockToken);

      return {
        access_token: mockToken,
        token_type: 'bearer',
        expires_in: 3600
      };
    } else {
      throw new Error('Credenciais inválidas');
    }
  }

  async logout(): Promise<void> {
    if (DEMO_MODE) {
      localStorage.removeItem('demo_user');
    }
    apiClient.clearToken();
  }

  async getCurrentUser(): Promise<User> {
    if (DEMO_MODE) {
      const userData = localStorage.getItem('demo_user');
      if (userData) {
        return JSON.parse(userData);
      }
      throw new Error('Usuário não encontrado');
    }

    return apiClient.get<User>('/auth/me');
  }

  async refreshToken(): Promise<AuthToken> {
    if (DEMO_MODE) {
      // Simular refresh de token no modo demo
      const currentToken = localStorage.getItem('auth_token');
      if (currentToken && currentToken.startsWith('demo_token_')) {
        return {
          access_token: currentToken,
          token_type: 'bearer',
          expires_in: 3600
        };
      }
      throw new Error('Token inválido');
    }

    return apiClient.post<AuthToken>('/auth/refresh');
  }

  isAuthenticated(): boolean {
    if (DEMO_MODE) {
      const token = localStorage.getItem('auth_token');
      const userData = localStorage.getItem('demo_user');
      return !!(token && userData && token.startsWith('demo_token_'));
    }

    return apiClient.isAuthenticated();
  }
}

export const authService = new AuthService();

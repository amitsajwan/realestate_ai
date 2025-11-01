export interface User {
  id: string;
  email: string;
  username?: string;
  firstName?: string;
  lastName?: string;
  isActive: boolean;
  isVerified: boolean;
  createdAt: string;
  updatedAt: string;
  roles: string[];
  lastLogin?: string;
  preferences?: {
    theme?: 'light' | 'dark';
    notifications?: {
      email?: boolean;
      push?: boolean;
    };
    dashboardLayout?: string[];
  };
}

export interface UserUpdate {
  email?: string;
  username?: string;
  firstName?: string;
  lastName?: string;
  preferences?: User['preferences'];
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface UserRegister extends UserLogin {
  username?: string;
  firstName?: string;
  lastName?: string;
}
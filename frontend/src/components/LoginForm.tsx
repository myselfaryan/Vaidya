import React, { useState } from 'react';
import Button from './Button';
import LoadingSpinner from './LoadingSpinner';

interface LoginFormProps {
  onLogin: (credentials: { username: string; password: string }) => Promise<void>;
  isLoading?: boolean;
}

const LoginForm: React.FC<LoginFormProps> = ({ onLogin, isLoading = false }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!username || !password) {
      setError('Please fill in all fields');
      return;
    }

    try {
      await onLogin({ username, password });
    } catch (error) {
      setError('Invalid username or password');
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8 p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold text-center mb-6">Login to Vaidya</h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
            Username or Email
          </label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter your username or email"
            disabled={isLoading}
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
            Password
          </label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter your password"
            disabled={isLoading}
          />
        </div>

        <Button
          type="submit"
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? <LoadingSpinner size="small" /> : 'Login'}
        </Button>
      </form>

      <div className="mt-4 text-center text-sm text-gray-600">
        Don't have an account?{' '}
        <a href="#" className="text-blue-600 hover:text-blue-500">
          Sign up
        </a>
      </div>
    </div>
  );
};

export default LoginForm;

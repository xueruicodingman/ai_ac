import { ArrowLeft, Mail, Lock, User, Eye, EyeOff } from 'lucide-react';
import { useState } from 'react';
import { register, login } from '../api';

interface LoginProps {
  onBack: () => void;
  onLogin: () => void;
}

export default function Login({ onBack, onLogin }: LoginProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError('');
    
    if (!email || !password) {
      setError('请填写邮箱和密码');
      return;
    }

    if (!isLogin && password !== confirmPassword) {
      setError('两次输入的密码不一致');
      return;
    }

    setLoading(true);
    console.log('Starting login, email:', email);

    try {
      if (isLogin) {
        console.log('Calling login API...');
        await login(email, password);
        console.log('Login successful');
      } else {
        console.log('Calling register API...');
        await register(email, password);
        console.log('Register successful, logging in...');
        await login(email, password);
        console.log('Auto-login successful');
      }
      console.log('Calling onLogin callback');
      onLogin();
    } catch (err: any) {
      console.error('Login/Register error:', err);
      const errorMsg = err?.message || err?.detail || JSON.stringify(err) || '操作失败，请重试';
      setError(errorMsg);
    } finally {
      console.log('Setting loading to false');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white rounded-lg border border-gray-200 p-8">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors mb-6"
          >
            <ArrowLeft size={20} />
            <span>返回</span>
          </button>

          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            {isLogin ? '登录账号' : '注册账号'}
          </h2>
          <p className="text-gray-500 mb-6">
            {isLogin ? '欢迎回来，请登录您的账号' : '创建新账号，开始使用'}
          </p>

          <div className="space-y-4">
            {error && (
              <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                邮箱
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="请输入邮箱"
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                密码
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="请输入密码"
                  className="w-full pl-10 pr-10 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  确认密码
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="请再次输入密码"
                    className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            )}

            {isLogin && (
              <div className="flex justify-end">
                <button className="text-sm text-blue-600 hover:text-blue-700">
                  忘记密码？
                </button>
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? '处理中...' : (isLogin ? '登录' : '注册')}
            </button>
          </div>

          <div className="mt-6 text-center">
            <p className="text-gray-500 text-sm">
              {isLogin ? '还没有账号？' : '已有账号？'}
              <button
                onClick={() => setIsLogin(!isLogin)}
                className="text-blue-600 hover:text-blue-700 font-medium ml-1"
              >
                {isLogin ? '立即注册' : '去登录'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

import { ArrowLeft, Lock, Key, User, LogOut, Eye, EyeOff, Globe, UserCog } from 'lucide-react';
import { useState, useEffect } from 'react';
import { getUserSettings, updateUserSettings, logout, getCurrentUser, updateCurrentUser } from '../api';
import { toast } from 'sonner';

interface UserSettingsProps {
  onBack: () => void;
  onLogout: () => void;
}

interface UserSettingsData {
  api_key: string;
  api_url: string;
  default_model: string;
  default_api_url: string;
  default_model_name: string;
}

// 根据API URL自动识别模型选项
const MODEL_OPTIONS: Record<string, { label: string; value: string }[]> = {
  'openai': [
    { label: 'GPT-4o', value: 'gpt-4o' },
    { label: 'GPT-4o-mini', value: 'gpt-4o-mini' },
    { label: 'GPT-4 Turbo', value: 'gpt-4-turbo' },
    { label: 'GPT-4', value: 'gpt-4' },
    { label: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' },
  ],
  'anthropic': [
    { label: 'Claude 3.5 Sonnet', value: 'claude-3-5-sonnet-20241022' },
    { label: 'Claude 3 Opus', value: 'claude-3-opus-20240229' },
    { label: 'Claude 3 Sonnet', value: 'claude-3-sonnet-20240229' },
    { label: 'Claude 3 Haiku', value: 'claude-3-haiku-20240307' },
  ],
  'google': [
    { label: 'Gemini 1.5 Pro', value: 'gemini-1.5-pro' },
    { label: 'Gemini 1.5 Flash', value: 'gemini-1.5-flash' },
    { label: 'Gemini 1.0 Pro', value: 'gemini-1.0-pro' },
  ],
  'azure': [
    { label: 'Azure OpenAI GPT-4', value: 'gpt-4' },
    { label: 'Azure OpenAI GPT-3.5', value: 'gpt-35-turbo' },
  ],
  'default': [
    { label: 'GPT-4', value: 'gpt-4' },
    { label: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' },
    { label: 'Claude 3.5 Sonnet', value: 'claude-3-5-sonnet-20241022' },
  ]
};

function getModelsByApiUrl(apiUrl: string): { label: string; value: string }[] {
  const url = apiUrl.toLowerCase();
  
  if (url.includes('openai') || url.includes('azure')) {
    return url.includes('azure') ? MODEL_OPTIONS['azure'] : MODEL_OPTIONS['openai'];
  } else if (url.includes('anthropic') || url.includes('claude')) {
    return MODEL_OPTIONS['anthropic'];
  } else if (url.includes('google') || url.includes('gemini')) {
    return MODEL_OPTIONS['google'];
  } else if (url.includes('volcengine') || url.includes('火山引擎')) {
    return MODEL_OPTIONS['openai']; // 火山引擎兼容OpenAI
  }
  
  return MODEL_OPTIONS['default'];
}

export default function UserSettings({ onBack, onLogout }: UserSettingsProps) {
  const [activeTab, setActiveTab] = useState<'password' | 'profile' | 'account'>('account');
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  
  // Account Settings
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  
  // API Settings
  const [apiKey, setApiKey] = useState('');
  const [apiUrl, setApiUrl] = useState('');
  const [model, setModel] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    loadSettings();
    loadUser();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await getUserSettings();
      setApiKey(data.api_key || '');
      setApiUrl(data.api_url || data.default_api_url || '');
      setModel(data.default_model || data.default_model_name || 'gpt-4');
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  };

  const loadUser = async () => {
    try {
      const user = await getCurrentUser();
      setUsername(user.username || '');
      setEmail(user.email || '');
    } catch (err) {
      console.error('Failed to load user:', err);
    }
  };

  const handleSaveAccount = async () => {
    if (!username.trim()) {
      toast.error('用户名不能为空');
      return;
    }
    setSaving(true);
    try {
      await updateCurrentUser({ username });
      toast.success('用户名更新成功');
    } catch (err: any) {
      toast.error(err.message || '更新失败');
    } finally {
      setSaving(false);
    }
  };

  const handleSavePassword = async () => {
    if (!oldPassword || !newPassword || !confirmPassword) {
      setMessage({ type: 'error', text: '请填写所有密码字段' });
      return;
    }
    if (newPassword !== confirmPassword) {
      setMessage({ type: 'error', text: '新密码与确认密码不一致' });
      return;
    }
    if (newPassword.length < 6) {
      setMessage({ type: 'error', text: '密码至少6位' });
      return;
    }
    setSaving(true);
    try {
      await updateCurrentUser({ password: newPassword });
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
      toast.success('密码修改成功');
    } catch (err: any) {
      toast.error(err.message || '修改失败');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveApiSettings = async () => {
    setSaving(true);
    setMessage({ type: '', text: '' });
    
    try {
      await updateUserSettings({
        api_key: apiKey,
        api_url: apiUrl,
        default_model: model,
      });
      setMessage({ type: 'success', text: '设置保存成功！' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || '保存失败' });
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    logout();
    onLogout();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft size={20} />
              <span>返回</span>
            </button>
            <div className="h-6 w-px bg-gray-300" />
            <h1 className="font-semibold text-gray-900">账号设置</h1>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex gap-8">
          <div className="w-48">
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <button
                onClick={() => setActiveTab('account')}
                className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                  activeTab === 'account'
                    ? 'bg-blue-50 text-blue-600 border-l-2 border-blue-600'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <UserCog size={18} />
                <span className="text-sm font-medium">账号信息</span>
              </button>
              <button
                onClick={() => setActiveTab('password')}
                className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                  activeTab === 'password'
                    ? 'bg-blue-50 text-blue-600 border-l-2 border-blue-600'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Lock size={18} />
                <span className="text-sm font-medium">修改密码</span>
              </button>
              <button
                onClick={() => setActiveTab('profile')}
                className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                  activeTab === 'profile'
                    ? 'bg-blue-50 text-blue-600 border-l-2 border-blue-600'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Key size={18} />
                <span className="text-sm font-medium">API设置</span>
              </button>
            </div>

            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-lg border border-red-200 mt-4 transition-colors"
            >
              <LogOut size={18} />
              <span className="text-sm font-medium">退出登录</span>
            </button>
          </div>

          <div className="flex-1">
            {activeTab === 'account' && (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-6">账号信息</h3>

                <div className="space-y-4 max-w-md">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      用户名
                    </label>
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="请输入用户名"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      邮箱
                    </label>
                    <input
                      type="email"
                      value={email}
                      disabled
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">邮箱不可修改</p>
                  </div>

                  <button
                    onClick={handleSaveAccount}
                    disabled={saving}
                    className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {saving ? '保存中...' : '保存用户名'}
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'profile' && (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-6">API 设置</h3>

                {message.text && (
                  <div className={`mb-4 p-3 rounded-lg text-sm ${
                    message.type === 'success' 
                      ? 'bg-green-50 border border-green-200 text-green-700'
                      : 'bg-red-50 border border-red-200 text-red-700'
                  }`}>
                    {message.text}
                  </div>
                )}

                <div className="space-y-4 max-w-md">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      API Key
                    </label>
                    <div className="relative">
                      <input
                        type={showApiKey ? 'text' : 'password'}
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="请输入您的API Key"
                        className="w-full px-4 py-2.5 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <button
                        type="button"
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showApiKey ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      用于调用AI服务，可在OpenAI或其他AI平台获取
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Globe size={14} className="inline mr-1" />
                      API URL（可选）
                    </label>
                    <input
                      type="text"
                      value={apiUrl}
                      onChange={(e) => setApiUrl(e.target.value)}
                      placeholder="留空使用默认: https://api.openai.com/v1"
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      自定义API端点，默认: https://api.openai.com/v1
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      默认AI模型
                    </label>
                    <input
                      type="text"
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      placeholder="请输入模型名称，如: gpt-4, claude-3-5-sonnet-20241022"
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      输入模型名称，如：gpt-4、gpt-4o、gpt-3.5-turbo、claude-3-5-sonnet-20241022
                    </p>
                  </div>

                  <button
                    onClick={handleSaveApiSettings}
                    disabled={saving}
                    className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {saving ? '保存中...' : '保存设置'}
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'password' && (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-6">修改密码</h3>

                {showSuccess && (
                  <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                    密码修改成功！
                  </div>
                )}

                <div className="space-y-4 max-w-md">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      当前密码
                    </label>
                    <input
                      type="password"
                      value={oldPassword}
                      onChange={(e) => setOldPassword(e.target.value)}
                      placeholder="请输入当前密码"
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      新密码
                    </label>
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="请输入新密码"
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      确认新密码
                    </label>
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="请再次输入新密码"
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <button
                    onClick={handleChangePassword}
                    className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                  >
                    保存修改
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function handleChangePassword() {
  alert('修改密码功能待开发');
}
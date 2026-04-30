import { Lightbulb, Grid3x3, FileQuestion, FileBarChart, User, LogIn, FileText } from 'lucide-react';

interface ModuleCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  onClick: () => void;
}

function ModuleCard({ icon, title, description, onClick }: ModuleCardProps) {
  return (
    <button
      onClick={onClick}
      className="group relative bg-white rounded-lg border border-gray-200 p-6 hover:border-blue-500 hover:shadow-lg transition-all duration-200 text-left"
    >
      <div className="flex flex-col gap-4">
        <div className="w-12 h-12 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
          {icon}
        </div>
        <div>
          <h3 className="font-medium text-gray-900 mb-2">{title}</h3>
          <p className="text-sm text-gray-500">{description}</p>
        </div>
      </div>
      <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
        <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </button>
  );
}

interface DashboardProps {
  onNavigate: (page: string) => void;
  onUserClick: () => void;
  isLoggedIn: boolean;
}

export default function Dashboard({ onNavigate, onUserClick, isLoggedIn }: DashboardProps) {
  const modules = [
    {
      icon: <Lightbulb size={24} />,
      title: '胜任力模型',
      description: '上传背景材料，AI智能生成胜任力模型',
      page: 'competency',
    },
    {
      icon: <Grid3x3 size={24} />,
      title: '评估矩阵',
      description: '选择能力与工具，生成科学评估矩阵',
      page: 'matrix',
    },
    {
      icon: <FileQuestion size={24} />,
      title: '题本生成',
      description: '快速生成多种测评题本，支持在线编辑',
      page: 'question',
    },
    {
      icon: <FileBarChart size={24} />,
      title: '测评报告',
      description: '生成个人版、反馈版、组织版测评报告',
      page: 'report',
    },
  ];

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center">
                <Lightbulb className="text-white" size={20} />
              </div>
              <div>
                <h1 className="font-semibold text-gray-900">能力研究中心</h1>
                <p className="text-xs text-gray-500">AI Talent Research Center</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {isLoggedIn ? (
                <button
                  onClick={onUserClick}
                  className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center hover:bg-blue-200 transition-colors"
                >
                  <User size={18} className="text-blue-600" />
                </button>
              ) : (
                <button
                  onClick={onUserClick}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                >
                  <LogIn size={16} />
                  登录
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto px-6 py-12 w-full">
        <div className="mb-8">
          <h2 className="text-xl font-bold text-gray-900 text-center">让每份天赋皆被看见</h2>
          <p className="text-sm text-gray-500 text-center mt-1">Let every talent be seen.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {modules.map((module) => (
            <ModuleCard
              key={module.page}
              icon={module.icon}
              title={module.title}
              description={module.description}
              onClick={() => onNavigate(module.page)}
            />
          ))}
        </div>
      </main>

      <footer className="border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div>
              <span>能力研究中心 v1.0.0</span>
              <span className="mx-2">·</span>
              <span>© 2026 All rights reserved</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { ArrowLeft, Clock, FileText, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { getQuestionnaires, getEvaluationMatrix, getQuestionnaire } from '../api';

interface PracticeItem {
  id: string;
  name: string;
  description: string;
  duration: number;
  status: 'not_started' | 'in_progress' | 'completed';
  bookStatus?: 'editing' | 'ready' | 'not_created';
  enabled: boolean;
}

interface PracticeListProps {
  onBack: () => void;
  onNavigate?: (page: string) => void;
  onNavigateVisionPractice?: (questionnaire: string) => void;
}

export default function PracticeList({ onBack, onNavigate, onNavigateVisionPractice }: PracticeListProps) {
  const [practiceItems, setPracticeItems] = useState<PracticeItem[]>([
    {
      id: 'beh',
      name: 'BEI行为事件访谈',
      description: '通过行为面试问题考察候选人',
      duration: 60,
      status: 'not_started',
      bookStatus: 'not_created',
      enabled: false,
    },
    {
      id: 'lgd',
      name: '无领导小组讨论',
      description: '小组讨论考察团队协作能力',
      duration: 90,
      status: 'not_started',
      bookStatus: 'not_created',
      enabled: false,
    },
    {
      id: 'roleplay',
      name: '角色扮演',
      description: '模拟上下级沟通场景',
      duration: 30,
      status: 'not_started',
      bookStatus: 'not_created',
      enabled: false,
    },
    {
      id: 'case',
      name: '案例分析',
      description: '商业案例分析与决策',
      duration: 90,
      status: 'not_started',
      bookStatus: 'not_created',
      enabled: false,
    },
    {
      id: 'vision',
      name: '个人愿景',
      description: '职业规划与发展思考',
      duration: 30,
      status: 'not_started',
      bookStatus: 'not_created',
      enabled: false,
    },
  ]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 获取评估矩阵
        const matrixData = await getEvaluationMatrix();
        let enabledTools: string[] = [];
        if (matrixData && matrixData.matrix) {
          for (const [ability, toolsObj] of Object.entries(matrixData.matrix)) {
            for (const [toolId, enabled] of Object.entries(toolsObj as Record<string, boolean>)) {
              if (enabled && !enabledTools.includes(toolId)) {
                enabledTools.push(toolId);
              }
            }
          }
        }
        
        // 获取题本
        const questionnaires = await getQuestionnaires();
        
        setPracticeItems(prev => 
          prev.map(item => {
            const isEnabled = enabledTools.includes(item.id);
            const savedBook = questionnaires?.find((b: any) => b.tool_id === item.id);
            return {
              ...item,
              enabled: isEnabled,
              bookStatus: savedBook ? 'ready' : (isEnabled ? 'not_created' : 'not_created'),
            };
          })
        );
      } catch (error) {
        console.log('Failed to fetch data');
      }
    };

    fetchData();
  }, []);

  const getStatusBadge = (status: PracticeItem['status']) => {
    switch (status) {
      case 'not_started':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
            <XCircle size={12} />
            未开始
          </span>
        );
      case 'in_progress':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">
            <Clock size={12} />
            进行中
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
            <CheckCircle size={12} />
            已完成
          </span>
        );
    }
  };

  const getBookStatusBadge = (bookStatus?: PracticeItem['bookStatus']) => {
    switch (bookStatus) {
      case 'editing':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">
            <AlertCircle size={12} />
            编辑中
          </span>
        );
      case 'ready':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
            <CheckCircle size={12} />
            已就绪
          </span>
        );
      case 'not_created':
      default:
        return null;
    }
  };

  const handleStartPractice = async (id: string) => {
    if (id === "beh" && onNavigate) {
      onNavigate("practice-session");
    } else if (id === "vision" && onNavigateVisionPractice) {
      // Fetch questionnaire for vision practice
      try {
        const questionnaire = await getQuestionnaire(id);
        onNavigateVisionPractice(questionnaire.content || '');
      } catch (error) {
        console.error('获取题本失败:', error);
        alert('获取题本失败，请稍后重试');
      }
    } else {
      alert(`开始练习: ${id}（暂未支持）`);
    }
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
            <h1 className="font-semibold text-gray-900">模拟练习</h1>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
          <h2 className="font-medium text-gray-900 mb-2">练习说明</h2>
          <p className="text-sm text-gray-600">
            选择下方练习工具进行模拟测试。每个练习模拟真实测评场景，帮助您熟悉考试流程和题型。
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {practiceItems.map((item) => {
            return (
              <div
                key={item.id}
                className={`rounded-lg border p-6 transition-shadow ${
                  item.enabled
                    ? 'bg-white border-gray-200 hover:shadow-lg cursor-pointer' 
                    : 'bg-gray-100 border-gray-300 cursor-not-allowed'
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${item.enabled ? 'bg-blue-50 text-blue-600' : 'bg-gray-200 text-gray-500'}`}>
                        <FileText size={20} />
                      </div>
                      <div>
                        <h3 className={`font-medium ${item.enabled ? 'text-gray-900' : 'text-gray-600'}`}>{item.name}</h3>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <Clock size={16} />
                          <span>{item.duration}分钟</span>
                        </div>
                      </div>
                    </div>
                    <p className={`text-sm ${item.enabled ? 'text-gray-500' : 'text-gray-500'}`}>{item.description}</p>
                  </div>
                </div>
                
                <div className="flex items-center justify-between mt-4">
                  <div className="flex items-center gap-2">
                    {!item.enabled && (
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-400 text-xs rounded-full">
                        未在评估矩阵中选择
                      </span>
                    )}
                    {item.enabled && getBookStatusBadge(item.bookStatus)}
                    {item.enabled && getStatusBadge(item.status)}
                  </div>
                  {item.enabled ? (
                    <button
                      onClick={() => handleStartPractice(item.id)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                    >
                      开始练习
                    </button>
                  ) : (
                    <button
                      disabled
                      className="px-4 py-2 bg-gray-200 text-gray-400 rounded-lg text-sm font-medium cursor-not-allowed"
                    >
                      未启用
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}
import { useState, useEffect } from 'react';
import { ArrowLeft, Loader2, FileText, User } from 'lucide-react';
import { getToolsWithCompetencies, getPracticeSessionsByTool, getSessionEvaluationData, getCurrentUser } from '../api';

interface BehaviorEvaluationProps {
  onBack: () => void;
}

interface Tool {
  tool_id: string;
  tool_name: string;
  competencies: {
    name: string;
    meaning: string;
    behavior_criteria: { title: string; description: string }[];
  }[];
}

interface Session {
  session_id: number;
  tool_id: string;
  created_at: string;
  status: string;
}

interface ExtractedBehavior {
  situation: string;
  target: string;
  role: string;
  challenge: string;
  thinking: string;
  action: string;
  result: string;
  reflection: string;
}

export default function BehaviorEvaluation({ onBack }: BehaviorEvaluationProps) {
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState<{ id: number; email: string } | null>(null);
  const [tools, setTools] = useState<Tool[]>([]);
  const [selectedTool, setSelectedTool] = useState<string>('');
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSession, setSelectedSession] = useState<number | null>(null);
  const [evaluationData, setEvaluationData] = useState<any>(null);
  const [selectedCompetency, setSelectedCompetency] = useState<number>(0);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const userData = await getCurrentUser();
      setCurrentUser(userData);
      
      const toolsResult = await getToolsWithCompetencies();
      console.log('Tools result:', toolsResult);
      console.log('Tools count:', toolsResult.tools?.length || 0);
      setTools(toolsResult.tools || []);
      
      if (toolsResult.tools && toolsResult.tools.length > 0) {
        setSelectedTool(toolsResult.tools[0].tool_id);
      } else {
        console.warn('No tools available - please generate matrix in Assessment Matrix first');
      }
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedTool) {
      loadSessions(selectedTool);
    }
  }, [selectedTool]);

  useEffect(() => {
    if (selectedSession) {
      loadEvaluationData(selectedSession);
    }
  }, [selectedSession]);

  const loadSessions = async (toolId: string) => {
    try {
      const result = await getPracticeSessionsByTool(toolId);
      setSessions(result.sessions || []);
      if (result.sessions && result.sessions.length > 0) {
        setSelectedSession(result.sessions[0].session_id);
      } else {
        setSelectedSession(null);
        setEvaluationData(null);
      }
    } catch (error) {
      console.error('加载练习记录失败:', error);
    }
  };

  const loadEvaluationData = async (sessionId: number) => {
    try {
      const result = await getSessionEvaluationData(sessionId);
      setEvaluationData(result);
    } catch (error) {
      console.error('加载评价数据失败:', error);
    }
  };

  const handleToolChange = (toolId: string) => {
    setSelectedTool(toolId);
    setSelectedSession(null);
    setEvaluationData(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (tools.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
          <div className="max-w-5xl mx-auto px-6 py-4">
            <div className="flex items-center gap-4">
              <button
                onClick={onBack}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft size={20} className="text-gray-600" />
              </button>
              <h1 className="text-xl font-semibold text-gray-900">行为评价</h1>
            </div>
          </div>
        </header>
        <main className="max-w-5xl mx-auto px-6 py-8">
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-6 text-center">
            <p className="text-orange-700 mb-4">请先在「评估矩阵」中选择测评工具并生成矩阵</p>
            <button
              onClick={onBack}
              className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
            >
              前往评估矩阵
            </button>
          </div>
        </main>
      </div>
    );
  }

  const selectedToolInfo = tools.find(t => t.tool_id === selectedTool);
  const competencies = selectedToolInfo?.competencies || [];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft size={20} className="text-gray-600" />
            </button>
            <h1 className="text-xl font-semibold text-gray-900">行为评价</h1>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8 space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <User size={20} className="text-gray-500" />
              <span className="text-gray-600">考生：</span>
              <span className="font-medium text-gray-900">{currentUser?.email || '用户'}</span>
            </div>
            <div className="flex items-center gap-2">
              <FileText size={20} className="text-gray-500" />
              <span className="text-gray-600">测评工具：</span>
              <select
                value={selectedTool}
                onChange={(e) => handleToolChange(e.target.value)}
                className="px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {tools.map(tool => (
                  <option key={tool.tool_id} value={tool.tool_id}>{tool.tool_name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {selectedToolInfo && (
          <>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">胜任力与行为提取</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-medium text-gray-700 w-28">胜任力</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700 w-40">行为标准</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700">行为提取</th>
                    </tr>
                  </thead>
                  <tbody>
                    {competencies.map((comp, compIdx) => {
                      const compData = evaluationData?.competencies?.find((c: any) => c.name === comp.name);
                      const behaviors = compData?.extracted_behaviors || [];
                      const behaviorCriteria = comp.behavior_criteria || [];
                      
                      return (
                        <tr key={compIdx} className="border-b border-gray-100">
                          <td className="py-3 px-4 font-medium text-gray-900 align-top">{comp.name}</td>
                          <td className="py-3 px-4 align-top">
                            {behaviorCriteria.length === 0 ? (
                              <span className="text-gray-400 text-xs">暂无行为标准</span>
                            ) : (
                              <div className="space-y-2">
                                {behaviorCriteria.map((criteria: any, criIdx: number) => (
                                  <div key={criIdx} className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                                    <div className="font-medium">{criteria.title}</div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            {behaviors.length === 0 ? (
                              <span className="text-gray-400">暂无提取的行为</span>
                            ) : (
                              <div className="space-y-3">
                                {behaviors.map((behavior: ExtractedBehavior, bhIdx: number) => (
                                  <div key={bhIdx} className="p-3 bg-gray-50 rounded-lg">
                                    <div className="grid grid-cols-2 gap-2 text-sm">
                                      <div>
                                        <span className="text-gray-500">情境：</span>
                                        <span className="text-gray-700">{behavior.situation || '-'}</span>
                                      </div>
                                      <div>
                                        <span className="text-gray-500">任务：</span>
                                        <span className="text-gray-700">{behavior.target || '-'}</span>
                                      </div>
                                      <div>
                                        <span className="text-gray-500">行动：</span>
                                        <span className="text-gray-700">{behavior.action || '-'}</span>
                                      </div>
                                      <div>
                                        <span className="text-gray-500">结果：</span>
                                        <span className="text-gray-700">{behavior.result || '-'}</span>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
</div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">评价结果</h2>
              
              {evaluationData?.judges && evaluationData.judges.length > 0 ? (
                <>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {competencies.map((comp, compIdx) => (
                      <button
                        key={compIdx}
                        onClick={() => setSelectedCompetency(compIdx)}
                        className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                          selectedCompetency === compIdx
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {comp.name}
                      </button>
                    ))}
                  </div>

                  <div className="border border-gray-200 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-4">{competencies[selectedCompetency]?.name}</h3>
                    
                    <div className="space-y-3 mb-4">
                      {evaluationData.judges.map((judge: any, judgeIdx: number) => {
                        const judgeResult = evaluationData.evaluation_results?.[judge.role]?.[competencies[selectedCompetency]?.name] || {};
                        const score = judgeResult.score ?? '-';
                        return (
                          <div key={judgeIdx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <span className="text-sm font-medium text-gray-700">{judge.role}</span>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-600">得分：</span>
                              <span className={`font-bold ${score === '-' ? 'text-gray-400' : score >= 8 ? 'text-green-600' : score >= 5 ? 'text-orange-500' : 'text-red-500'}`}>
                                {score}
                              </span>
                              <span className="text-xs text-gray-400">/10</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    <div className="p-3 bg-blue-50 rounded-lg">
                      <div className="text-sm text-gray-600 mb-1">评价语</div>
                      <p className="text-gray-800 text-sm">
                        {(() => {
                          const comments = evaluationData.judges.map((judge: any) => 
                            evaluationData.evaluation_results?.[judge.role]?.[competencies[selectedCompetency]?.name]?.comment
                          ).filter(Boolean);
                          return comments.length > 0 ? comments.join(' ') : '暂无评价语';
                        })()}
                      </p>
                    </div>
                  </div>

                  {evaluationData.total_score && (
                    <div className="flex items-center justify-center p-4 bg-purple-50 rounded-lg mt-4">
                      <span className="text-lg font-semibold text-purple-700">
                        综合得分：{evaluationData.total_score}（平均分）
                      </span>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-4 text-gray-400">暂无评价结果</div>
              )}
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">原始记录</h2>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {evaluationData?.original_records?.length > 0 ? (
                  evaluationData.original_records.map((record: string, idx: number) => (
                    <div key={idx} className={`p-4 rounded-lg ${record.startsWith('面试官') ? 'bg-blue-50' : 'bg-gray-50'}`}>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{record}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-center py-4">暂无原始记录</p>
                )}
              </div>
            </div>
          </>
        )}

        {tools.length === 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="text-center py-8 text-gray-500">
              请先在评估矩阵中选择并保存测评工具
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
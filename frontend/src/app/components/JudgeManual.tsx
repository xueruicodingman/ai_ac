import { ArrowLeft, FileText, Copy, Check, RefreshCw, Edit2, Save, ChevronDown, ChevronRight, Download, BookOpen } from 'lucide-react';
import { useState, useEffect } from 'react';
import { generateJudgeHandbook, generateJudgeHandbookByTool, getQuestionnaires, getCompetencyModel, getEvaluationMatrix, saveJudgeHandbook, getJudgeHandbook, getHeaders } from '../api';

interface JudgeManualProps {
  onBack: () => void;
  onNavigate?: (page: string, params?: any) => void;
}

interface HandbookItem {
  tool: string;
  tool_name: string;
  judge_content: string;
  actor_content?: string;
}

const TOOL_CONFIG = [
  { id: 'vision', name: '个人愿景', icon: '📋' },
  { id: 'beh', name: 'BEI行为事件访谈', icon: '🎯' },
  { id: 'roleplay', name: '角色扮演', icon: '🎭' },
  { id: 'lgd', name: '无领导小组讨论', icon: '👥' },
  { id: 'case', name: '案例分析', icon: '📊' },
];

const TOOL_MAP: Record<string, string> = {
  vision: '个人愿景',
  beh: 'BEI行为事件访谈',
  roleplay: '角色扮演',
  lgd: '无领导小组讨论',
  case: '案例分析',
};

export default function JudgeManual({ onBack, onNavigate }: JudgeManualProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isGenerated, setIsGenerated] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [handbooks, setHandbooks] = useState<Record<string, HandbookItem>>({});
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});
  const [competencyModel, setCompetencyModel] = useState<any>(null);
  const [evaluationMatrix, setEvaluationMatrix] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('roleplay');
  const [editingTool, setEditingTool] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [questionnairesData, setQuestionnairesData] = useState<any[]>([]);

  useEffect(() => {
    loadHandbooksFromDB();
  }, []);

  const loadHandbooksFromDB = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/judge-handbooks', {
        headers: getHeaders(),
      });

      if (response.status === 404) {
        return;
      }

      if (!response.ok) {
        console.error('加载评委手册失败:', response.status);
        return;
      }

      const data = await response.json();

      let handbooksList: any[] = [];

      if (data.content) {
        try {
          handbooksList = JSON.parse(data.content);
        } catch (e) {
          console.error('解析content失败:', e);
          return;
        }
      }

      if (handbooksList && handbooksList.length > 0) {
        const handbookMap: Record<string, HandbookItem> = {};
        handbooksList.forEach((hb: any) => {
          handbookMap[hb.tool] = {
            tool: hb.tool,
            tool_name: TOOL_MAP[hb.tool] || hb.tool,
            judge_content: hb.judge_content || '',
            actor_content: hb.actor_content,
          };
        });
        setHandbooks(handbookMap);
        setIsGenerated(true);
      }
    } catch (err) {
      console.error('Load handbook error:', err);
    }
  };

  const hasContent = (toolId: string) => {
    return handbooks[toolId] && handbooks[toolId].judge_content;
  };

  const toggleToolExpanded = (toolId: string) => {
    setExpandedTools(prev => ({ ...prev, [toolId]: !prev[toolId] }));
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError('');
    try {
      const [model, matrix, questionnaires] = await Promise.all([
        getCompetencyModel(),
        getEvaluationMatrix(),
        getQuestionnaires()
      ]);

      if (!model || !questionnaires || questionnaires.length === 0) {
        throw new Error('请先完成胜任力模型和题本生成');
      }

      const competencyModelData = {
        dimensions: model.dimensions || [],
        name: model.name || ''
      };
      const evaluationMatrixData = matrix?.matrix || {};
      const questionnaireList = questionnaires.map((q: any) => ({
        tool_id: q.tool_id,
        tool_name: q.tool_id,
        content: q.content
      }));

      setCompetencyModel({ id: model.id, ...competencyModelData });
      setEvaluationMatrix({ id: matrix.id, ...evaluationMatrixData });
      setQuestionnairesData(questionnaires);

      const response = await generateJudgeHandbook({
        competency_model: competencyModelData,
        evaluation_matrix: evaluationMatrixData,
        questionnaires: questionnaireList
      });

      if (response.success && response.data) {
        const handbookMap: Record<string, HandbookItem> = {};
        Object.keys(response.data).forEach(toolId => {
          handbookMap[toolId] = {
            tool: toolId,
            tool_name: TOOL_MAP[toolId] || toolId,
            judge_content: response.data[toolId] || '',
          };
        });
        setHandbooks(handbookMap);
        setIsGenerated(true);
        setActiveTab('roleplay');
        localStorage.setItem('judge_handbook_content', JSON.stringify(Object.values(handbookMap)));
      } else {
        throw new Error('生成失败，请重试');
      }
    } catch (err: any) {
      console.error('Generate handbook error:', err);
      const errorMessage = err?.message || err?.detail || JSON.stringify(err) || '生成评委手册失败，请重试';
      setError(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRegenerateTool = async (toolId: string) => {
    if (isGenerating) return;
    if (!competencyModel || !evaluationMatrix) {
      await handleGenerate();
      return;
    }
    
    const targetQ = Object.values(handbooks).find((h: any) => h.tool === toolId);
    if (!targetQ?.judge_content) {
      alert(`未找到 ${TOOL_MAP[toolId]} 的题本内容`);
      return;
    }

    try {
      setIsGenerating(true);
      setEditingTool(toolId);

      const response = await generateJudgeHandbookByTool(
        toolId,
        targetQ.judge_content,
        competencyModel,
        evaluationMatrix
      );

      if (response.success && response.data && response.data[toolId]) {
        setHandbooks(prev => ({
          ...prev,
          [toolId]: {
            ...prev[toolId],
            tool: toolId,
            tool_name: TOOL_MAP[toolId] || toolId,
            judge_content: response.data[toolId],
          }
        }));
        localStorage.setItem('judge_handbook_content', JSON.stringify(Object.values(handbooks)));
      } else {
        throw new Error('生成失败');
      }
    } catch (err: any) {
      console.error('Regenerate error:', err);
      alert(err.message || '重新生成失败');
    } finally {
      setIsGenerating(false);
      setEditingTool(null);
    }
  };

  const handleCopyContent = async (content: string) => {
    if (!content) return;
    try {
      await navigator.clipboard.writeText(content);
      alert('内容已复制到剪贴板！');
    } catch (err) {
      console.error('复制失败:', err);
    }
  };

  const handleEditTool = (toolId: string) => {
    const tool = handbooks[toolId];
    if (tool) {
      setEditingTool(toolId);
      setEditContent(tool.judge_content);
    }
  };

  const handleSaveToolEdit = async () => {
    if (editingTool) {
      const updatedHandbook = {
        ...handbooks[editingTool],
        judge_content: editContent,
      };

      const allHandbooks = {
        ...handbooks,
        [editingTool]: updatedHandbook,
      };

      setHandbooks(allHandbooks);
      setEditingTool(null);
      setEditContent('');

      if (competencyModel && evaluationMatrix) {
        try {
          const handbookData = Object.values(allHandbooks).map(hb => ({
            tool: hb.tool,
            judge_content: hb.judge_content,
            actor_content: hb.actor_content || undefined,
          }));

          const modelId = competencyModel?.id || 1;
          const matrixId = evaluationMatrix?.id || 1;
          const questionnaireIds = questionnairesData.map((q: any) => q.id).filter(Boolean);

          await saveJudgeHandbook({
            model_id: modelId,
            matrix_id: matrixId,
            questionnaire_ids: questionnaireIds,
            content: JSON.stringify(handbookData),
          });
        } catch (err) {
          console.error('保存单个手册失败:', err);
        }
      }

      localStorage.setItem('judge_handbook_content', JSON.stringify(Object.values(allHandbooks)));
      alert('已保存');
    }
  };

  const handleSaveAll = async () => {
    if (!competencyModel || !evaluationMatrix) {
      alert('请先生成评委手册');
      return;
    }
    
    setIsSaving(true);
    try {
      const handbookData = Object.values(handbooks).map(hb => ({
        tool: hb.tool,
        judge_content: hb.judge_content,
        actor_content: hb.actor_content || undefined,
      }));

      const modelId = competencyModel?.id || 1;
      const matrixId = evaluationMatrix?.id || 1;
      
      const questionnaireIds = questionnairesData.map((q: any) => q.id).filter(Boolean);
      
      await saveJudgeHandbook({
        model_id: modelId,
        matrix_id: matrixId,
        questionnaire_ids: questionnaireIds,
        content: JSON.stringify(handbookData),
      });
      
      localStorage.setItem('judge_handbook_content', JSON.stringify(Object.values(handbooks)));
      alert('评委手册已提交定稿并保存到数据库！');
    } catch (err: any) {
      console.error('Save error:', err);
      alert(err.message || '保存失败');
    } finally {
      setIsSaving(false);
    }
  };

  const currentContent = activeTab && handbooks[activeTab] ? handbooks[activeTab].judge_content : '';

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
            <h1 className="font-semibold text-gray-900">评委手册</h1>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <FileText className="text-green-600 flex-shrink-0 mt-0.5" size={20} />
            <div>
              <h3 className="font-medium text-green-900 mb-1">评委手册</h3>
              <p className="text-sm text-green-700">
                根据您已提交的题本自动生成，按题本类型分模块展示，支持单独生成和在线编辑。
              </p>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {(!isGenerated || Object.keys(handbooks).length === 0) && (
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed mb-6"
          >
            {isGenerating ? '正在生成中，请稍候...' : '生成全部评委手册'}
          </button>
        )}

        {isGenerated && Object.keys(handbooks).length > 0 && (
          <>
            <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
              {TOOL_CONFIG.map(tool => (
                <button
                  key={tool.id}
                  onClick={() => setActiveTab(tool.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                    activeTab === tool.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
                  }`}
                >
                  <span>{tool.icon}</span>
                  <span>{tool.name}</span>
                  {hasContent(tool.id) ? (
                    <span className="ml-1 px-1.5 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">已</span>
                  ) : (
                    <span className="ml-1 px-1.5 py-0.5 text-xs bg-gray-100 text-gray-500 rounded-full">未</span>
                  )}
                </button>
              ))}
            </div>

            <div className="bg-white rounded-lg border border-gray-200 mb-6">
              <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
                <h3 className="font-medium text-gray-900">{TOOL_MAP[activeTab] || activeTab} 评委手册</h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleRegenerateTool(activeTab)}
                    disabled={isGenerating || !hasContent(activeTab)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-blue-50 text-blue-700 hover:bg-blue-100 disabled:bg-gray-100 disabled:text-gray-400"
                  >
                    <RefreshCw size={16} className={isGenerating && editingTool === activeTab ? "animate-spin" : ""} />
                    重新生成
                  </button>
                  <button
                    onClick={() => handleCopyContent(currentContent)}
                    disabled={!currentContent}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50"
                  >
                    <Copy size={16} />
                    复制
                  </button>
                  <button
                    onClick={() => handleEditTool(activeTab)}
                    disabled={!currentContent}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50"
                  >
                    <Edit2 size={16} />
                    编辑
                  </button>
                </div>
              </div>

              <div className="p-4">
                {editingTool === activeTab ? (
                  <div className="space-y-4">
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="w-full h-[400px] p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none font-mono text-sm"
                    />
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => {
                          setEditingTool(null);
                          setEditContent('');
                        }}
                        className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                      >
                        取消
                      </button>
                      <button
                        onClick={handleSaveToolEdit}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                      >
                        保存
                      </button>
                    </div>
                  </div>
                ) : currentContent ? (
                  <div className="max-h-[400px] overflow-y-auto">
                    <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700">{currentContent}</pre>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    该工具的评委手册尚未生成
                  </div>
                )}
              </div>
            </div>

            <button
              onClick={isGenerated ? handleGenerate : handleSaveAll}
              disabled={isSaving || isGenerating}
              className="w-full mt-6 bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isGenerating ? '处理中...' : (isGenerated ? '重新生成全部内容' : '保存全部到数据库')}
            </button>
          </>
        )}
      </main>
    </div>
  );
}
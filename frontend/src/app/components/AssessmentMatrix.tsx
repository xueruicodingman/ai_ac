import { ArrowLeft, Check, RotateCcw } from 'lucide-react';
import { useState, useEffect } from 'react';
import { getCompetencyModel, generateEvaluationMatrix, getEvaluationMatrix, saveEvaluationMatrix } from '../api';
import { toast } from 'sonner';

interface AssessmentMatrixProps {
  onBack: () => void;
}

interface Dimension {
  id: string;
  name: string;
  meaning: string;
  behavior_criteria: Array<{ id: string; title: string; description: string }>;
}

interface CompetencyModelData {
  id: number;
  name: string;
  dimensions: Dimension[];
  created_at: string;
  updated_at: string;
}

export default function AssessmentMatrix({ onBack }: AssessmentMatrixProps) {
  const [selectedAbilities, setSelectedAbilities] = useState<string[]>([]);
  const [selectedTools, setSelectedTools] = useState<string[]>(['beh', 'lgd']);
  const [matrixGenerated, setMatrixGenerated] = useState(false);
  const [matrix, setMatrix] = useState<{ [key: string]: string[] }>({});
  const [abilities, setAbilities] = useState<string[]>([]);
  const [competencyModelData, setCompetencyModelData] = useState<CompetencyModelData | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const tools = [
    { id: 'beh', name: 'BEI行为事件访谈' },
    { id: 'lgd', name: '无领导小组讨论' },
    { id: 'roleplay', name: '角色扮演' },
    { id: 'case', name: '案例分析' },
    { id: 'vision', name: '个人愿景' },
  ];

  useEffect(() => {
    loadSavedData();
  }, []);

  const loadSavedData = async () => {
    try {
      // 加载胜任力模型
      const modelData = await getCompetencyModel();
      setCompetencyModelData(modelData);
      const dimensionNames = modelData.dimensions.map((d: Dimension) => d.name);
      setAbilities(dimensionNames);
      
      // 加载已保存的矩阵
      try {
        const matrixData = await getEvaluationMatrix();
        console.log('Loaded matrix data from API:', matrixData);
        if (matrixData && matrixData.matrix) {
          const savedMatrix: { [key: string]: string[] } = {};
          const savedAbilities: string[] = [];
          for (const [ability, toolsObj] of Object.entries(matrixData.matrix)) {
            savedMatrix[ability] = Object.keys(toolsObj).filter(k => toolsObj[k]);
            savedAbilities.push(ability);
          }
          console.log('Parsed savedMatrix:', savedMatrix);
          console.log('Parsed savedAbilities:', savedAbilities);
          setMatrix(savedMatrix);
          setSelectedAbilities(savedAbilities);
          if (Object.keys(savedMatrix).length > 0) {
            setMatrixGenerated(true);
            setHasSubmitted(true);
          }
        }
      } catch (err) {
        console.log('No saved matrix found');
      }
    } catch (err) {
      console.log('No saved data found');
    }
  };

  const generateMatrix = async () => {
    if (!competencyModelData || selectedAbilities.length === 0) {
      setError('请先提交胜任力模型并选择能力');
      return;
    }

    setError('');
    setIsGenerating(true);

    try {
      // 过滤出选中能力的维度数据
      const selectedDimensions = competencyModelData.dimensions.filter(
        (d: Dimension) => selectedAbilities.includes(d.name)
      );

      console.log('Selected dimensions:', selectedDimensions);
      console.log('Selected abilities:', selectedAbilities);

      const requestData = {
        competency_model: {
          dimensions: selectedDimensions
        },
        selected_tools: selectedTools
      };
      console.log('Request data:', JSON.stringify(requestData));

      const response = await generateEvaluationMatrix(requestData);

      console.log('Matrix API response:', response);
      
      const matrixData = response.data || {};
      console.log('Matrix data:', matrixData);
      
      // 转换格式: {能力名: [工具1, 工具2]} → {能力名: {工具1: true, 工具2: true}}
      const newMatrix: { [key: string]: string[] } = {};
      for (const [ability, tools] of Object.entries(matrixData)) {
        newMatrix[ability] = tools as string[];
      }

      setMatrix(newMatrix);
      setMatrixGenerated(true);
    } catch (err: any) {
      setError(err.message || '生成矩阵失败');
    } finally {
      setIsGenerating(false);
    }
  };

  const toggleAbility = (ability: string) => {
    setSelectedAbilities(prev =>
      prev.includes(ability) ? prev.filter(a => a !== ability) : [...prev, ability]
    );
  };

  const toggleTool = (toolId: string) => {
    setSelectedTools(prev =>
      prev.includes(toolId) ? prev.filter(t => t !== toolId) : [...prev, toolId]
    );
  };

  const selectAllAbilities = () => {
    setSelectedAbilities([...abilities]);
  };

  const toggleMatrixCell = (ability: string, toolId: string) => {
    console.log('Toggle:', ability, toolId);
    setMatrix(prev => {
      const current = prev[ability] || [];
      console.log('Current tools for', ability, ':', current);
      const updated = current.includes(toolId)
        ? current.filter(t => t !== toolId)
        : [...current, toolId];
      console.log('Updated tools for', ability, ':', updated);
      return { ...prev, [ability]: updated };
    });
  };

  const handleSubmit = async () => {
    if (!competencyModelData || Object.keys(matrix).length === 0) {
      return;
    }

    try {
      // 转换矩阵格式: {能力名: [工具1, 工具2]} → {能力名: {工具1: true, 工具2: true}}
      const matrixData: Record<string, Record<string, boolean>> = {};
      for (const [ability, tools] of Object.entries(matrix)) {
        matrixData[ability] = {};
        for (const tool of tools) {
          matrixData[ability][tool] = true;
        }
      }

      console.log('=== Submit Info ===');
      console.log('matrix state:', JSON.stringify(matrix));
      console.log('matrixData to save:', JSON.stringify(matrixData));
      console.log('selectedTools:', JSON.stringify(selectedTools));

      await saveEvaluationMatrix({
        model_id: competencyModelData.id,
        tools: tools.map(t => ({ id: t.id, name: t.name, weight: 20, enabled: true })),
        matrix: matrixData
      });
      setHasSubmitted(true);
      toast.success('矩阵已保存！', {
        action: {
          label: '前往题本生成',
          onClick: () => window.location.hash = 'question',
        },
        duration: 5000,
      });
    } catch (err: any) {
      toast.error(err.message || '保存失败');
    }
  };

  const handleReset = () => {
    setMatrixGenerated(false);
    setMatrix({});
    setSelectedAbilities([]);
    setHasSubmitted(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft size={20} />
              <span>返回首页</span>
            </button>
            <div className="h-6 w-px bg-gray-300" />
            <h1 className="font-semibold text-gray-900">评估矩阵</h1>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-blue-900">
            <span className="font-medium">胜任力模型（已提交）：</span>
            {abilities.length > 0 ? abilities.join('、') : '暂无提交数据'}
          </p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-gray-900">选择要测评的能力</h3>
            <button
              onClick={selectAllAbilities}
              className="text-sm text-blue-600 hover:text-blue-700 transition-colors"
            >
              一键全选
            </button>
          </div>
          <div className="flex flex-wrap gap-3">
            {abilities.map((ability) => (
              <button
                key={ability}
                onClick={() => toggleAbility(ability)}
                className={`px-4 py-2 rounded-lg border transition-all ${
                  selectedAbilities.includes(ability)
                    ? 'bg-blue-50 border-blue-500 text-blue-700'
                    : 'bg-white border-gray-300 text-gray-700 hover:border-gray-400'
                }`}
              >
                {selectedAbilities.includes(ability) && (
                  <Check size={16} className="inline mr-1" />
                )}
                {ability}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h3 className="font-medium text-gray-900 mb-4">选择测评工具</h3>
          <div className="space-y-3">
            {tools.map((tool) => (
              <label
                key={tool.id}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <input
                  type="checkbox"
                  checked={selectedTools.includes(tool.id)}
                  onChange={() => toggleTool(tool.id)}
                  className="w-5 h-5 text-blue-600 rounded border-gray-300 focus:ring-2 focus:ring-blue-500"
                />
                <span className="text-gray-700">{tool.name}</span>
              </label>
            ))}
          </div>
        </div>

        {!matrixGenerated && (
          <>
            <button
              onClick={generateMatrix}
              disabled={selectedAbilities.length === 0 || selectedTools.length === 0 || isGenerating}
              className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed mb-2"
            >
              {isGenerating ? '生成中...' : '生成矩阵'}
            </button>

            {error && (
              <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg text-sm mb-4">
                {error}
              </div>
            )}
          </>
        )}

        {matrixGenerated && (
          <>
            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6 overflow-x-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-gray-900">评估矩阵预览</h3>
                <button
                  onClick={handleReset}
                  className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                >
                  <RotateCcw size={16} />
                  重新配置
                </button>
              </div>
              <table className="w-full border-collapse min-w-[600px]">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-medium text-gray-700 bg-gray-50">能力</th>
                    {tools
                      .filter(t => selectedTools.includes(t.id))
                      .map((tool) => (
                        <th key={tool.id} className="text-center py-3 px-4 font-medium text-gray-700 bg-gray-50 min-w-[120px]">
                          {tool.name}
                        </th>
                      ))}
                  </tr>
                </thead>
                <tbody>
                  {selectedAbilities.map((ability) => {
                    console.log('Rendering row for:', ability, 'matrix[ability]:', matrix[ability]);
                    return (
                    <tr key={ability} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-900">{ability}</td>
                      {tools
                        .filter(t => selectedTools.includes(t.id))
                        .map((tool) => (
                          <td key={tool.id} className="text-center py-3 px-4">
                            <button
                              onClick={() => toggleMatrixCell(ability, tool.id)}
                              className={`w-8 h-8 rounded flex items-center justify-center mx-auto transition-colors ${
                                matrix[ability]?.includes(tool.id)
                                  ? 'bg-green-100 text-green-600 hover:bg-green-200'
                                  : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                              }`}
                            >
                              {matrix[ability]?.includes(tool.id) && <Check size={18} />}
                            </button>
                          </td>
                        ))}
                    </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="flex gap-4">
              <button
                onClick={generateMatrix}
                disabled={isGenerating}
                className="flex-1 bg-white border border-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
              >
                {isGenerating ? '生成中...' : '重新生成'}
              </button>
              <button
                onClick={handleSubmit}
                disabled={isGenerating}
                className="flex-1 bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                提交矩阵
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

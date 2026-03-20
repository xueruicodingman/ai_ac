import { ArrowLeft, Check, RotateCcw } from 'lucide-react';
import { useState } from 'react';

interface AssessmentMatrixProps {
  onBack: () => void;
}

export default function AssessmentMatrix({ onBack }: AssessmentMatrixProps) {
  const [selectedAbilities, setSelectedAbilities] = useState<string[]>([]);
  const [selectedTools, setSelectedTools] = useState<string[]>(['bei', 'lgd']);
  const [matrixGenerated, setMatrixGenerated] = useState(false);
  const [matrix, setMatrix] = useState<{ [key: string]: string[] }>({});

  const abilities = ['领导力', '沟通协作', '创新能力', '分析思维', '执行力'];
  const tools = [
    { id: 'bei', name: 'BEI行为事件访谈' },
    { id: 'lgd', name: '无领导小组讨论' },
    { id: 'role', name: '角色扮演' },
    { id: 'case', name: '案例分析' },
    { id: 'vision', name: '个人愿景' },
  ];

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

  const generateMatrix = () => {
    const newMatrix: { [key: string]: string[] } = {};
    selectedAbilities.forEach((ability) => {
      const randomTools = selectedTools
        .sort(() => Math.random() - 0.5)
        .slice(0, Math.floor(Math.random() * 3) + 2);
      newMatrix[ability] = randomTools;
    });
    setMatrix(newMatrix);
    setMatrixGenerated(true);
  };

  const toggleMatrixCell = (ability: string, toolId: string) => {
    setMatrix(prev => {
      const current = prev[ability] || [];
      const updated = current.includes(toolId)
        ? current.filter(t => t !== toolId)
        : [...current, toolId];
      return { ...prev, [ability]: updated };
    });
  };

  const handleSubmit = () => {
    alert('矩阵已保存！');
  };

  const handleReset = () => {
    setMatrixGenerated(false);
    setMatrix({});
    setSelectedAbilities([]);
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
            领导力、沟通协作、创新能力、分析思维、执行力
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
          <button
            onClick={generateMatrix}
            disabled={selectedAbilities.length === 0 || selectedTools.length === 0}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed mb-6"
          >
            生成矩阵
          </button>
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
                  {selectedAbilities.map((ability) => (
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
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex gap-4">
              <button
                onClick={generateMatrix}
                className="flex-1 bg-white border border-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              >
                重新生成
              </button>
              <button
                onClick={handleSubmit}
                className="flex-1 bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition-colors font-medium"
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

import { ArrowLeft, Upload, X, Plus, Trash2, Edit2, Check } from 'lucide-react';
import { useState, useEffect } from 'react';
import { generateCompetencyModel, saveCompetencyModel, getCompetencyModel } from '../api';

interface CompetencyModelProps {
  onBack: () => void;
}

interface Behavior {
  id: string;
  title: string;
  description: string;
}

interface Competency {
  id: string;
  name: string;
  meaning: string;
  behaviors: Behavior[];
}

export default function CompetencyModel({ onBack }: CompetencyModelProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [abilityNames, setAbilityNames] = useState('');
  const [abilityCount, setAbilityCount] = useState('');
  const [generatedModel, setGeneratedModel] = useState<Competency[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  useEffect(() => {
    loadSavedModel();
  }, []);

  const loadSavedModel = async () => {
    try {
      const data = await getCompetencyModel();
      if (data && data.dimensions && data.dimensions.length > 0) {
        const converted: Competency[] = data.dimensions.map((dim: any) => ({
          id: dim.id,
          name: dim.name,
          meaning: dim.meaning,
          behaviors: (dim.behavior_criteria || []).map((bc: any) => ({
            id: bc.id,
            title: bc.title,
            description: bc.description,
          })),
        }));
        setGeneratedModel(converted);
        setHasSubmitted(true);
      }
    } catch (err) {
      // 没有保存的模型，忽略错误
      console.log('No saved model found');
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles([...files, ...Array.from(e.target.files)]);
    }
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleGenerate = async () => {
    // 验证参数
    const hasBackground = abilityNames.trim().length > 0;
    const numCount = abilityCount ? parseInt(abilityCount) : 5;
    
    if (!numCount || numCount < 1) {
      setError('请填写能力数量');
      return;
    }
    
    if (!hasBackground) {
      setError('能力名称和背景材料至少填写一个');
      return;
    }

    setError('');
    setIsGenerating(true);

    try {
      // 解析能力名称
      const specifiedAbilities = abilityNames 
        ? abilityNames.split(/[,，]/).map(n => n.trim()).filter(n => n)
        : [];
      
      const response = await generateCompetencyModel({
        background: abilityNames, // 暂时用能力名称作为背景
        specified_abilities: specifiedAbilities,
        num_competencies: numCount,
      });

      // 转换API返回的数据格式
      const dimensions = response.data?.dimensions || [];
      const converted: Competency[] = dimensions.map((dim: any) => ({
        id: dim.id || `competency-${Math.random()}`,
        name: dim.name || '',
        meaning: dim.meaning || '',
        behaviors: (dim.behavior_criteria || []).map((bc: any) => ({
          id: bc.id || `b-${Math.random()}`,
          title: bc.title || '',
          description: bc.description || '',
        })),
      }));

      setGeneratedModel(converted);
    } catch (err: any) {
      setError(err.message || '生成失败');
    } finally {
      setIsGenerating(false);
    }
  };

  const updateCompetency = (id: string, field: keyof Competency, value: string) => {
    setGeneratedModel(models => 
      models.map(m => m.id === id ? { ...m, [field]: value } : m)
    );
  };

  const updateBehavior = (compId: string, behaviorId: string, field: keyof Behavior, value: string) => {
    setGeneratedModel(models =>
      models.map(m => {
        if (m.id !== compId) return m;
        return {
          ...m,
          behaviors: m.behaviors.map(b => 
            b.id === behaviorId ? { ...b, [field]: value } : b
          ),
        };
      })
    );
  };

  const addBehavior = (compId: string) => {
    setGeneratedModel(models =>
      models.map(m => {
        if (m.id !== compId) return m;
        return {
          ...m,
          behaviors: [...m.behaviors, { id: `b-${Date.now()}`, title: '新行为', description: '' }],
        };
      })
    );
  };

  const removeBehavior = (compId: string, behaviorId: string) => {
    setGeneratedModel(models =>
      models.map(m => {
        if (m.id !== compId) return m;
        return { ...m, behaviors: m.behaviors.filter(b => b.id !== behaviorId) };
      })
    );
  };

  const removeCompetency = (id: string) => {
    setGeneratedModel(models => models.filter(m => m.id !== id));
  };

  const addCompetency = () => {
    setGeneratedModel(models => [
      ...models,
      { id: `c-${Date.now()}`, name: '新能力', meaning: '', behaviors: [{ id: `b-${Date.now()}`, title: '行为标准', description: '' }] },
    ]);
  };

  const handleSubmit = async () => {
    if (generatedModel.length === 0) {
      return;
    }

    setSubmitting(true);
    try {
      const modelData = {
        name: '胜任力模型',
        dimensions: generatedModel.map(c => ({
          id: c.id,
          name: c.name,
          meaning: c.meaning,
          behavior_criteria: c.behaviors.map(b => ({
            id: b.id,
            title: b.title,
            description: b.description,
          })),
        })),
      };

      await saveCompetencyModel(modelData);
      setHasSubmitted(true);
      alert('模型已保存！');
    } catch (err: any) {
      alert(err.message || '保存失败');
    } finally {
      setSubmitting(false);
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
              <span>返回首页</span>
            </button>
            <div className="h-6 w-px bg-gray-300" />
            <h1 className="font-semibold text-gray-900">胜任力模型</h1>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h3 className="font-medium text-gray-900 mb-4">背景材料（可选）</h3>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
            <Upload className="mx-auto mb-3 text-gray-400" size={32} />
            <p className="text-sm text-gray-600 mb-2">点击或拖拽文件上传</p>
            <p className="text-xs text-gray-400 mb-4">支持 图片、Word、Excel、PDF 格式</p>
            <input
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"
              onChange={handleFileUpload}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="inline-block px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors cursor-pointer text-sm font-medium"
            >
              选择文件
            </label>
          </div>

          {files.length > 0 && (
            <div className="mt-4 space-y-2">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between bg-gray-50 rounded-lg px-4 py-3"
                >
                  <span className="text-sm text-gray-700">{file.name}</span>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <X size={18} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                能力名称（可选，多个用逗号分隔）
              </label>
              <input
                type="text"
                value={abilityNames}
                onChange={(e) => setAbilityNames(e.target.value)}
                placeholder="例如：领导力，沟通协作，创新能力"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                能力数量（可选）
              </label>
              <input
                type="number"
                value={abilityCount}
                onChange={(e) => setAbilityCount(e.target.value)}
                placeholder="例如：5"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>

        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed mb-2"
        >
          {isGenerating ? '正在生成中...' : '生成模型'}
        </button>

        {error && (
          <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg text-sm mb-4">
            {error}
          </div>
        )}

        {generatedModel.length > 0 && (
          <>
            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="font-medium text-gray-900">生成的胜任力模型</h3>
                <span className="text-sm text-gray-500">可编辑</span>
              </div>

              <div className="space-y-6">
                {generatedModel.map((competency) => (
                  <div key={competency.id} className="border border-gray-200 rounded-lg p-5">
                    <div className="flex items-start justify-between mb-4">
                      <input
                        type="text"
                        value={competency.name}
                        onChange={(e) => updateCompetency(competency.id, 'name', e.target.value)}
                        className="text-lg font-medium text-gray-900 border border-gray-200 rounded px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => removeCompetency(competency.id)}
                          className="text-gray-400 hover:text-red-500 transition-colors"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </div>

                    <div className="mb-4">
                      <label className="block text-xs font-medium text-gray-500 mb-2">
                        能力含义
                      </label>
                      <textarea
                        value={competency.meaning}
                        onChange={(e) => updateCompetency(competency.id, 'meaning', e.target.value)}
                        className="w-full px-3 py-2 text-sm text-gray-700 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                        rows={2}
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-2">
                        行为标准
                      </label>
                      <div className="space-y-3">
                        {competency.behaviors.map((behavior) => (
                          <div key={behavior.id} className="bg-gray-50 rounded-lg p-4">
                            <div className="flex items-start gap-2">
                              <div className="flex-1 space-y-2">
                                <input
                                  type="text"
                                  value={behavior.title}
                                  onChange={(e) => updateBehavior(competency.id, behavior.id, 'title', e.target.value)}
                                  className="w-full px-3 py-1.5 text-sm font-medium text-gray-900 border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  placeholder="行为标题"
                                />
                                <textarea
                                  value={behavior.description}
                                  onChange={(e) => updateBehavior(competency.id, behavior.id, 'description', e.target.value)}
                                  className="w-full px-3 py-1.5 text-sm text-gray-700 border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                                  rows={2}
                                  placeholder="行为描述"
                                />
                              </div>
                              <button
                                onClick={() => removeBehavior(competency.id, behavior.id)}
                                className="text-gray-400 hover:text-red-500 transition-colors mt-1"
                              >
                                <X size={16} />
                              </button>
                            </div>
                          </div>
                        ))}
                        <button 
                          onClick={() => addBehavior(competency.id)}
                          className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 transition-colors mt-2"
                        >
                          <Plus size={16} />
                          添加行为标准
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <button 
                onClick={addCompetency}
                className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 transition-colors mt-6"
              >
                <Plus size={18} />
                添加能力
              </button>
            </div>

            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {submitting ? '保存中...' : '提交定稿（覆盖存储）'}
            </button>
          </>
        )}
      </main>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { ArrowLeft, Save, Loader2, Edit3, X } from 'lucide-react';
import { getEvaluationCriteria, saveEvaluationCriteria } from '../api';

interface EvaluationCriteriaProps {
  onBack: () => void;
}

interface Level {
  name: string;
  score_min: number;
  score_max: number;
  description: string;
}

interface Quantity {
  name: string;
  count: number;
  description: string;
}

interface CriteriaData {
  levels: Level[];
  quantity: Quantity[];
  quality: string[];
  rules: { name: string; description: string }[];
}

const defaultData: CriteriaData = {
  levels: [
    { name: "优", score_min: 9, score_max: 10, description: "【完全体现】且其中2条行为标准的行为质量为【高】" },
    { name: "良", score_min: 7, score_max: 8, description: "【完全体现】且仅有1条行为标准的行为质量为【高】或【部分体现】且其中2条行为标准的行为质量为【高】" },
    { name: "合格", score_min: 5, score_max: 6, description: "【完全体现】且其中0条行为标准的行为质量为【高】或【部分体现】且其中1条行为标准的行为质量为【高】或【部分体现】且其中0条行为标准的行为质量为【高】或【稍微体现】且其中1条行为标准的行为质量为【高】" },
    { name: "不合格", score_min: 0, score_max: 4, description: "【稍微体现】且其中0条行为标准的行为质量为【高】或【未体现】" }
  ],
  quantity: [
    { name: "未体现", count: 0, description: "学员在练习中行为体现出其中0条行为标准" },
    { name: "稍微体现", count: 1, description: "学员在练习中行为体现出其中1条行为标准" },
    { name: "部分体现", count: 2, description: "学员在练习中行为体现出其中2条行为标准" },
    { name: "完全体现", count: 3, description: "学员在练习中行为体现出其中3条行为标准" }
  ],
  quality: [
    "学员在练习中，反复、频繁地出现反映胜任力某条行为标准的行为，均以正向的行为为主",
    "在某个压力场景下，依然能够展现反映胜任力某条行为标准的行为",
    "学员在练习中，体现出反映胜任力某条行为标准非常规的行为，例如在某个场景下，很少有人能够体现出这样的行为"
  ],
  rules: [
    { name: "评委打分", description: "只允许取整数打分" },
    { name: "分差限制", description: "两位评委之间的分差不允许超过1分" }
  ]
};

export default function EvaluationCriteria({ onBack }: EvaluationCriteriaProps) {
  const [data, setData] = useState<CriteriaData>(defaultData);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState<'levels' | 'quantity' | 'quality' | 'rules'>('levels');

  useEffect(() => {
    loadCriteria();
  }, []);

  const loadCriteria = async () => {
    try {
      const result = await getEvaluationCriteria();
      setData(result.criteria_content || defaultData);
    } catch (error) {
      console.error('加载评价标准失败:', error);
      setData(defaultData);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveEvaluationCriteria(data);
      setIsEditing(false);
      alert('保存成功！');
    } catch (error) {
      console.error('保存失败:', error);
      alert('保存失败，请重试');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setData(defaultData);
    setIsEditing(false);
  };

  const updateLevel = (index: number, field: keyof Level, value: any) => {
    const newLevels = [...data.levels];
    newLevels[index] = { ...newLevels[index], [field]: value };
    setData({ ...data, levels: newLevels });
  };

  const updateQuantity = (index: number, field: keyof Quantity, value: any) => {
    const newQuantity = [...data.quantity];
    newQuantity[index] = { ...newQuantity[index], [field]: value };
    setData({ ...data, quantity: newQuantity });
  };

  const updateQuality = (index: number, value: string) => {
    const newQuality = [...data.quality];
    newQuality[index] = value;
    setData({ ...data, quality: newQuality });
  };

  const updateRule = (index: number, field: 'name' | 'description', value: string) => {
    const newRules = [...data.rules];
    newRules[index] = { ...newRules[index], [field]: value };
    setData({ ...data, rules: newRules });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft size={20} className="text-gray-600" />
            </button>
            <h1 className="text-xl font-semibold text-gray-900">评价标准</h1>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex gap-2 mb-6 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('levels')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'levels'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            评价等级
          </button>
          <button
            onClick={() => setActiveTab('quantity')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'quantity'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            行为数量
          </button>
          <button
            onClick={() => setActiveTab('quality')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'quality'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            行为质量
          </button>
          <button
            onClick={() => setActiveTab('rules')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'rules'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            打分要求
          </button>
        </div>

        {activeTab === 'levels' && (
          <div className="space-y-4">
            <div className="flex justify-end">
              {isEditing ? (
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCancel}
                    className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <X size={18} />
                    取消
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save size={18} />}
                    保存
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center gap-2 px-4 py-2 border border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  <Edit3 size={18} />
                  编辑
                </button>
              )}
            </div>
            {isEditing ? (
              <div className="bg-white rounded-lg border border-blue-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">评价等级与分数区间</h2>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[600px] text-sm table-fixed">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 font-medium text-gray-700 w-24">等级</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-700 w-24">分数区间</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-700">行为标准</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.levels.map((level, index) => (
                        <tr key={index} className="border-b border-gray-100">
                          <td className="py-3 px-4">
                            <input
                              type="text"
                              value={level.name}
                              onChange={(e) => updateLevel(index, 'name', e.target.value)}
                              className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-1">
                              <input
                                type="number"
                                value={level.score_min}
                                onChange={(e) => updateLevel(index, 'score_min', parseInt(e.target.value))}
                                className="w-10 px-1 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center"
                              />
                              <span className="text-gray-400">-</span>
                              <input
                                type="number"
                                value={level.score_max}
                                onChange={(e) => updateLevel(index, 'score_max', parseInt(e.target.value))}
                                className="w-10 px-1 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center"
                              />
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <textarea
                              value={level.description}
                              onChange={(e) => updateLevel(index, 'description', e.target.value)}
                              rows={2}
                              className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">评价等级与分数区间</h2>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[600px] text-sm table-fixed">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 font-medium text-gray-700 w-24">评价等级</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-700 w-24">分数区间</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-700">行为数量&质量标准</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.levels.map((level, index) => (
                        <tr key={index} className="border-b border-gray-100">
                          <td className={`py-3 px-4 font-medium ${
                            level.name === '优' ? 'text-green-600' :
                            level.name === '良' ? 'text-blue-600' :
                            level.name === '合格' ? 'text-yellow-600' : 'text-red-600'
                          }`}>{level.name}</td>
                          <td className="py-3 px-4 text-gray-900">{level.score_min}-{level.score_max}分</td>
                          <td className="py-3 px-4 text-gray-600 whitespace-pre-line">{level.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'quantity' && (
          <div className="space-y-4">
            <div className="flex justify-end">
              {isEditing ? (
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCancel}
                    className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <X size={18} />
                    取消
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save size={18} />}
                    保存
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center gap-2 px-4 py-2 border border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  <Edit3 size={18} />
                  编辑
                </button>
              )}
            </div>
            {isEditing ? (
              <div className="bg-white rounded-lg border border-blue-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">行为数量评价说明</h2>
                <p className="text-gray-600 mb-4">每个胜任力有3条行为标准，根据学员在练习中体现的行为标准数量进行判定：</p>
                <div className="space-y-4">
                  {data.quantity.map((item, index) => (
                    <div key={index} className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 mb-1">名称</label>
                        <input
                          type="text"
                          value={item.name}
                          onChange={(e) => updateQuantity(index, 'name', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      <div className="w-24">
                        <label className="block text-sm font-medium text-gray-700 mb-1">数量</label>
                        <input
                          type="number"
                          value={item.count}
                          onChange={(e) => updateQuantity(index, 'count', parseInt(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 mb-1">说明</label>
                        <input
                          type="text"
                          value={item.description}
                          onChange={(e) => updateQuantity(index, 'description', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">行为数量评价说明</h2>
                <p className="text-gray-600 mb-4">每个胜任力有3条行为标准，根据学员在练习中体现的行为标准数量进行判定：</p>
                <div className="space-y-3">
                  {data.quantity.map((item, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <span className={`font-medium min-w-[80px] ${
                        item.count === 0 ? 'text-red-600' :
                        item.count === 1 ? 'text-orange-600' :
                        item.count === 2 ? 'text-yellow-600' : 'text-green-600'
                      }`}>{item.name}</span>
                      <span className="text-gray-600">{item.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'quality' && (
          <div className="space-y-4">
            <div className="flex justify-end">
              {isEditing ? (
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCancel}
                    className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <X size={18} />
                    取消
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save size={18} />}
                    保存
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center gap-2 px-4 py-2 border border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  <Edit3 size={18} />
                  编辑
                </button>
              )}
            </div>
            {isEditing ? (
              <div className="bg-white rounded-lg border border-blue-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">行为质量评价说明</h2>
                <p className="text-gray-600 mb-4">当练习中学员行为呈现出以下任意一个特征时，即表示行为质量为【高】：</p>
                <div className="space-y-4">
                  {data.quality.map((item, index) => (
                    <div key={index} className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                      <label className="block text-sm font-medium text-gray-700 mb-2">特征 {index + 1}</label>
                      <textarea
                        value={item}
                        onChange={(e) => updateQuality(index, e.target.value)}
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">行为质量评价说明</h2>
                <p className="text-gray-600 mb-4">当练习中学员行为呈现出以下任意一个特征时，即表示行为质量为【高】：</p>
                <div className="space-y-3">
                  {data.quality.map((item, index) => (
                    <div key={index} className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                      <p className="text-gray-700">{item}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'rules' && (
          <div className="space-y-4">
            <div className="flex justify-end">
              {isEditing ? (
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCancel}
                    className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <X size={18} />
                    取消
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save size={18} />}
                    保存
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center gap-2 px-4 py-2 border border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  <Edit3 size={18} />
                  编辑
                </button>
              )}
            </div>
            {isEditing ? (
              <div className="bg-white rounded-lg border border-blue-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">打分要求</h2>
                <div className="space-y-4">
                  {data.rules.map((rule, index) => (
                    <div key={index} className="flex items-start gap-4 p-4 bg-yellow-50 rounded-lg border border-yellow-100">
                      <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 mb-1">规则名称</label>
                        <input
                          type="text"
                          value={rule.name}
                          onChange={(e) => updateRule(index, 'name', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 mb-1">规则说明</label>
                        <input
                          type="text"
                          value={rule.description}
                          onChange={(e) => updateRule(index, 'description', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">打分要求</h2>
                <div className="space-y-3">
                  {data.rules.map((rule, index) => (
                    <div key={index} className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg border border-yellow-100">
                      <span className="text-yellow-700 font-medium">{rule.name}</span>
                      <span className="text-gray-600">{rule.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
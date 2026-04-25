import { useState, useEffect } from 'react';
import { ArrowLeft, RefreshCw, Save, Edit2, X } from 'lucide-react';
import { getJudges, saveJudges, generateJudges } from '../api';

interface JudgeTeamProps {
  onBack: () => void;
}

export default function JudgeTeam({ onBack }: JudgeTeamProps) {
  const [judgeCount, setJudgeCount] = useState(3);
  const [judges, setJudges] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({ role: '', personality: '', hiring_preference: '', evaluation_style: '', expertise_area: '', task: '' });

  useEffect(() => {
    loadJudges();
  }, []);

  const loadJudges = async () => {
    setLoading(true);
    try {
      const data = await getJudges();
      setJudges(data.judges || []);
    } catch (e) {
      setJudges([]);
    }
    setLoading(false);
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const data = await generateJudges(judgeCount);
      setJudges(data.data.judges);
      alert('生成成功');
    } catch (err: any) {
      alert(err.message || '生成失败');
    }
    setGenerating(false);
  };

  const handleSave = async () => {
    try {
      await saveJudges(judges);
      alert('保存成功');
    } catch (err: any) {
      alert(err.message || '保存失败');
    }
  };

  const handleEdit = (index: number) => {
    setEditingIndex(index);
    setEditForm({
      role: judges[index].role || '',
      personality: judges[index].personality || '',
      hiring_preference: judges[index].hiring_preference || '',
      evaluation_style: judges[index].evaluation_style || '',
      expertise_area: judges[index].expertise_area || '',
      task: judges[index].task || ''
    });
  };

  const handleSaveEdit = () => {
    if (editingIndex !== null) {
      const newJudges = [...judges];
      newJudges[editingIndex] = {
        role: editForm.role,
        personality: editForm.personality,
        hiring_preference: editForm.hiring_preference,
        evaluation_style: editForm.evaluation_style,
        expertise_area: editForm.expertise_area,
        task: editForm.task
      };
      setJudges(newJudges);
      setEditingIndex(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4 flex items-center gap-4">
        <button onClick={onBack} className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-xl font-semibold">评委管理</h1>
      </div>

      <div className="p-6 max-w-4xl mx-auto">
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">评委数量</label>
          <input
            type="number"
            min={1}
            max={10}
            value={judgeCount}
            onChange={e => setJudgeCount(parseInt(e.target.value) || 3)}
            className="w-24 px-3 py-2 border rounded-lg"
          />
          <span className="ml-2 text-gray-600">人</span>
        </div>

        <div className="flex gap-4 mb-6">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-4 py-2 bg-green-600 text-white rounded-lg flex items-center gap-2 hover:bg-green-700"
          >
            <RefreshCw size={16} className={generating ? 'animate-spin' : ''} />
            {generating ? '生成中...' : 'AI生成评委'}
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg flex items-center gap-2 hover:bg-blue-700"
          >
            <Save size={16} />
            保存配置
          </button>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <h3 className="font-medium text-gray-900 mb-4">
            评委配置 ({judges.length}人)
          </h3>
          
          {loading ? (
            <div className="text-center py-8 text-gray-500">加载中...</div>
          ) : judges.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              暂无配置，点击"AI生成评委"自动生成
            </div>
          ) : (
            <div className="space-y-4">
              {judges.map((judge, index) => (
                <div key={index} className="border rounded-lg p-4">
                  {editingIndex === index ? (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">角色名称</label>
                        <input
                          type="text"
                          value={editForm.role}
                          onChange={e => setEditForm({...editForm, role: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">个性描述</label>
                        <input
                          type="text"
                          value={editForm.personality}
                          onChange={e => setEditForm({...editForm, personality: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">用人偏好</label>
                        <input
                          type="text"
                          value={editForm.hiring_preference}
                          onChange={e => setEditForm({...editForm, hiring_preference: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">评价风格</label>
                        <input
                          type="text"
                          value={editForm.evaluation_style}
                          onChange={e => setEditForm({...editForm, evaluation_style: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">专长领域</label>
                        <input
                          type="text"
                          value={editForm.expertise_area}
                          onChange={e => setEditForm({...editForm, expertise_area: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">任务描述</label>
                        <textarea
                          value={editForm.task}
                          onChange={e => setEditForm({...editForm, task: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg min-h-[80px]"
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={handleSaveEdit}
                          className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm"
                        >
                          保存
                        </button>
                        <button
                          onClick={() => setEditingIndex(null)}
                          className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-sm"
                        >
                          取消
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <span className="font-medium text-gray-900">{judge.role}</span>
                          <span className="px-2 py-0.5 text-xs rounded bg-blue-100 text-blue-700">
                            评委
                          </span>
                        </div>
                        <button
                          onClick={() => handleEdit(index)}
                          className="text-blue-600 hover:text-blue-700 text-sm"
                        >
                          编辑
                        </button>
                      </div>
                      <div className="space-y-1 text-sm text-gray-600">
                        {judge.personality && (
                          <div><span className="font-medium">个性：</span>{judge.personality}</div>
                        )}
                        {judge.hiring_preference && (
                          <div><span className="font-medium">用人偏好：</span>{judge.hiring_preference}</div>
                        )}
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <span className="font-medium">评价风格：</span>
                            {judge.evaluation_style || '-'}
                          </div>
                          <div>
                            <span className="font-medium">专长领域：</span>
                            {judge.expertise_area || '-'}
                          </div>
                        </div>
                      </div>
                      {judge.task && (
                        <p className="text-sm text-gray-600 mt-2"><span className="font-medium">任务：</span>{judge.task}</p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
import { ArrowLeft, Download, Edit2, Save, FileText, Copy, Check } from 'lucide-react';
import { useState, useEffect } from 'react';
import { generateJudgeHandbook, getQuestionnaires, getCompetencyModel, getEvaluationMatrix } from '../api';

interface JudgeManualProps {
  onBack: () => void;
}

export default function JudgeManual({ onBack }: JudgeManualProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isGenerated, setIsGenerated] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [manualContent, setManualContent] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    loadExistingHandbook();
  }, []);

  const loadExistingHandbook = async () => {
    try {
      const savedContent = localStorage.getItem('judge_handbook_content');
      if (savedContent) {
        setManualContent(savedContent);
        setIsGenerated(true);
      }
    } catch (err) {
      console.error('Load handbook error:', err);
    }
  };

  const handleDownload = async (format: 'word' | 'pdf') => {
    alert(`正在下载${format === 'word' ? 'Word' : 'PDF'}版本...`);
  };

  const handleCopyContent = async () => {
    if (!manualContent) return;
    try {
      await navigator.clipboard.writeText(manualContent);
      alert('内容已复制到剪贴板！');
    } catch (err) {
      console.error('复制失败:', err);
      alert('复制失败，请手动复制');
    }
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

      const questionnaireList = questionnaires.map((q: any) => ({
        tool_id: q.tool_id,
        tool_name: q.tool_name || q.tool_id,
        content: q.content
      }));

      const response = await generateJudgeHandbook({
        competency_model: model,
        evaluation_matrix: matrix,
        questionnaires: questionnaireList
      });

      if (response.success && response.data?.content) {
        setManualContent(response.data.content);
        localStorage.setItem('judge_handbook_content', response.data.content);
        setIsGenerated(true);
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

  const handleSave = () => {
    localStorage.setItem('judge_handbook_content', manualContent);
    setIsEditing(false);
    alert('评委手册已保存！');
  };

  const handleSubmit = () => {
    localStorage.setItem('judge_handbook_content', manualContent);
    alert('评委手册已提交定稿！');
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
                根据您已提交的题本自动生成，包含测评说明、评分标准、注意事项等内容。
              </p>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {(!isGenerated || manualContent) && (
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed mb-6"
          >
            {isGenerating ? '正在生成中，请稍候...' : (manualContent ? '重新生成' : '生成评委手册')}
          </button>
        )}

        {isGenerated && (
          <>
            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-gray-900">评委手册内容</h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopyContent}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200"
                  >
                    <Copy size={16} />
                    复制
                  </button>
                  <button
                    onClick={() => handleDownload('word')}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200"
                  >
                    <Download size={16} />
                    Word
                  </button>
                  <button
                    onClick={() => handleDownload('pdf')}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200"
                  >
                    <Download size={16} />
                    PDF
                  </button>
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      isEditing 
                        ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                        : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                    }`}
                  >
                    {isEditing ? <Check size={16} /> : <Edit2 size={16} />}
                    {isEditing ? '保存' : '编辑'}
                  </button>
                </div>
              </div>

              {isEditing ? (
                <textarea
                  value={manualContent}
                  onChange={(e) => setManualContent(e.target.value)}
                  className="w-full h-[500px] p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none font-mono text-sm"
                />
              ) : (
                <div className="bg-gray-50 rounded-lg p-6 max-h-[500px] overflow-y-auto">
                  <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700">{manualContent}</pre>
                </div>
              )}
            </div>

            <button
              onClick={handleSubmit}
              className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition-colors font-medium"
            >
              提交定稿
            </button>
          </>
        )}
      </main>
    </div>
  );
}
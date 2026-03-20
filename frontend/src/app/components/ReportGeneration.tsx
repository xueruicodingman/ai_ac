import { ArrowLeft, FileText, Users, User, Download, Upload, CheckCircle, Clock, Eye } from 'lucide-react';
import { useState } from 'react';

interface ReportGenerationProps {
  onBack: () => void;
  onNavigate: (page: string) => void;
}

type ReportType = 'feedback' | 'organization' | 'personal';

interface Report {
  type: ReportType;
  name: string;
  status: 'draft' | 'generated' | 'submitted';
  submitTime?: string;
  canGenerate: boolean;
  needPrevious?: boolean;
}

interface Candidate {
  id: string;
  name: string;
  scores: { [key: string]: number };
  totalScore: number;
}

export default function ReportGeneration({ onBack, onNavigate }: ReportGenerationProps) {
  const [hasUploadedRecords, setHasUploadedRecords] = useState(false);
  const [reports, setReports] = useState<Report[]>([
    { type: 'feedback', name: '反馈版报告', status: 'draft', canGenerate: true },
    { type: 'organization', name: '组织版报告', status: 'draft', canGenerate: false, needPrevious: true },
    { type: 'personal', name: '个人版报告', status: 'draft', canGenerate: false, needPrevious: true },
  ]);
  const [selectedCandidate, setSelectedCandidate] = useState<string>('1');
  const [editingReport, setEditingReport] = useState<Report | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const candidates: Candidate[] = [
    { id: '1', name: '张三', scores: { '领导力': 85, '沟通协作': 90, '创新能力': 78 }, totalScore: 253 },
    { id: '2', name: '李四', scores: { '领导力': 78, '沟通协作': 82, '创新能力': 88 }, totalScore: 248 },
    { id: '3', name: '王五', scores: { '领导力': 92, '沟通协作': 85, '创新能力': 80 }, totalScore: 257 },
  ];

  const currentCandidate = candidates.find(c => c.id === selectedCandidate) || candidates[0];

  const handleUploadRecords = () => {
    onNavigate('upload');
  };

  const handleGenerateReport = (report: Report) => {
    if (!report.canGenerate) return;
    setIsGenerating(true);

    setTimeout(() => {
      setReports(reports.map(r =>
        r.type === report.type ? { ...r, status: 'generated' as const } : r
      ));
      setEditingReport(report);
      setIsGenerating(false);
    }, 2000);
  };

  const handleSubmitReport = () => {
    if (!editingReport) return;

    setReports(reports.map(r => {
      if (r.type === editingReport.type) {
        return { ...r, status: 'submitted' as const, submitTime: new Date().toLocaleString('zh-CN') };
      }
      if (r.type === 'organization' && editingReport.type === 'feedback') {
        return { ...r, canGenerate: true, status: 'draft' as const };
      }
      if (r.type === 'personal' && editingReport.type === 'organization') {
        return { ...r, canGenerate: true, status: 'draft' as const };
      }
      return r;
    }));

    setEditingReport(null);
    alert('报告已提交！');
  };

  const handleDownload = (reportType: ReportType) => {
    alert(`正在下载${reportType}报告...`);
  };

  const getStatusBadge = (report: Report) => {
    if (report.status === 'submitted') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
          <CheckCircle size={12} />
          已提交 {report.submitTime && `• ${report.submitTime}`}
        </span>
      );
    }
    if (report.status === 'generated') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
          <Clock size={12} />
          已生成
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
        待生成
      </span>
    );
  };

  const getReportIcon = (type: ReportType) => {
    switch (type) {
      case 'feedback': return <FileText size={24} />;
      case 'organization': return <Users size={24} />;
      case 'personal': return <User size={24} />;
    }
  };

  const getReportColor = (type: ReportType) => {
    switch (type) {
      case 'feedback': return 'bg-blue-100 text-blue-600';
      case 'organization': return 'bg-purple-100 text-purple-600';
      case 'personal': return 'bg-green-100 text-green-600';
    }
  };

  const handleNextCandidate = () => {
    const currentIndex = candidates.findIndex(c => c.id === selectedCandidate);
    const nextIndex = (currentIndex + 1) % candidates.length;
    setSelectedCandidate(candidates[nextIndex].id);
  };

  const handleBackToList = () => {
    setEditingReport(null);
  };

  if (editingReport) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-5xl mx-auto px-6 py-4">
            <div className="flex items-center gap-4">
              <button
                onClick={handleBackToList}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft size={20} />
                <span>返回列表</span>
              </button>
              <div className="h-6 w-px bg-gray-300" />
              <h1 className="font-semibold text-gray-900">编辑 - {editingReport.name}</h1>
            </div>
          </div>
        </header>

        <main className="max-w-5xl mx-auto px-6 py-8">
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium text-gray-900">选择被测者</h3>
              <button
                onClick={handleNextCandidate}
                className="text-sm text-blue-600 hover:text-blue-700 transition-colors"
              >
                下一个 →
              </button>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {candidates.map(candidate => (
                <button
                  key={candidate.id}
                  onClick={() => setSelectedCandidate(candidate.id)}
                  className={`p-3 rounded-lg border text-left transition-colors ${
                    selectedCandidate === candidate.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <p className="font-medium text-gray-900">{candidate.name}</p>
                  <p className="text-xs text-gray-500">总分：{candidate.totalScore}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
            <h3 className="font-medium text-gray-900 mb-4">能力得分数据</h3>
            <div className="grid grid-cols-3 gap-4 mb-4">
              {Object.entries(currentCandidate.scores).map(([key, value]) => (
                <div key={key} className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500 mb-1">{key}</p>
                  <p className="text-2xl font-semibold text-gray-900">{value}</p>
                </div>
              ))}
            </div>
            <p className="text-center text-gray-500">
              总分：<span className="font-semibold text-gray-900">{currentCandidate.totalScore}</span>
            </p>
          </div>

          {editingReport.type === 'feedback' && (
            <FeedbackReportEditor candidate={currentCandidate} />
          )}
          
          {editingReport.type === 'organization' && (
            <OrganizationReportEditor candidate={currentCandidate} />
          )}
          
          {editingReport.type === 'personal' && (
            <PersonalReportEditor candidate={currentCandidate} />
          )}

          <div className="flex gap-4 mt-6">
            <button
              onClick={handleBackToList}
              className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              返回列表
            </button>
            <button
              onClick={handleNextCandidate}
              className="flex-1 bg-blue-50 text-blue-600 py-3 rounded-lg hover:bg-blue-100 transition-colors font-medium"
            >
              下一个
            </button>
            <button
              onClick={handleSubmitReport}
              className="flex-1 bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition-colors font-medium"
            >
              提交定稿
            </button>
          </div>
        </main>
      </div>
    );
  }

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
            <h1 className="font-semibold text-gray-900">测评报告</h1>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
          <div className="flex items-start justify-between">
            <div className="flex gap-4">
              <div className="w-12 h-12 rounded-lg bg-orange-50 flex items-center justify-center text-orange-600">
                <Upload size={24} />
              </div>
              <div>
                <h3 className="font-medium text-gray-900 mb-1">上传测评记录</h3>
                <p className="text-sm text-gray-500">
                  上传测评数据，支持批量导入分析，下载模板开始录入
                </p>
              </div>
            </div>
            <button
              onClick={handleUploadRecords}
              className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors text-sm font-medium whitespace-nowrap"
            >
              上传数据
            </button>
          </div>
        </div>

        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">生成报告</h2>
          <p className="text-gray-600">按顺序生成反馈版、组织版、个人版报告</p>
        </div>

        <div className="space-y-6">
          {reports.map((report, index) => (
            <div key={report.type} className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex gap-4">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${getReportColor(report.type)}`}>
                    {getReportIcon(report.type)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-gray-900">{report.name}</h3>
                      {report.needPrevious && (
                        <span className="text-xs text-gray-400">（需先生成反馈版）</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mb-2">
                      {index === 0 && '包含一句话评价、优势项和不足项，适合快速反馈'}
                      {index === 1 && '包含详细评价、数据分析和雷达图，供组织决策使用'}
                      {index === 2 && '包含发展建议、学习课程和书籍推荐，帮助个人提升'}
                    </p>
                    {getStatusBadge(report)}
                  </div>
                </div>
                <div className="flex gap-2">
                  {report.status === 'submitted' && (
                    <>
                      <button
                        onClick={() => setEditingReport(report)}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                      >
                        <Eye size={18} />
                      </button>
                      <button
                        onClick={() => handleDownload(report.type)}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                      >
                        <Download size={18} />
                      </button>
                    </>
                  )}
                  {report.status === 'generated' && (
                    <>
                      <button
                        onClick={() => setEditingReport(report)}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                      >
                        <Eye size={18} />
                      </button>
                      <button
                        onClick={() => handleDownload(report.type)}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                      >
                        <Download size={18} />
                      </button>
                    </>
                  )}
                  {report.status === 'draft' && report.canGenerate && (
                    <button
                      onClick={() => handleGenerateReport(report)}
                      disabled={isGenerating}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:bg-gray-400"
                    >
                      {isGenerating ? '生成中...' : '生成'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

function FeedbackReportEditor({ candidate }: { candidate: Candidate }) {
  const [oneLiner, setOneLiner] = useState('');
  const [strengths, setStrengths] = useState([{ competency: '', comment: '', behavior: '' }]);
  const [weaknesses, setWeaknesses] = useState([{ competency: '', comment: '', behavior: '' }]);

  const addStrength = () => setStrengths([...strengths, { competency: '', comment: '', behavior: '' }]);
  const addWeakness = () => setWeaknesses([...weaknesses, { competency: '', comment: '', behavior: '' }]);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="font-medium text-gray-900 mb-4">报告内容（可编辑）</h3>
      
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">一句话评价</label>
          <input
            type="text"
            value={oneLiner}
            onChange={(e) => setOneLiner(e.target.value)}
            placeholder="例如：张三在沟通协作方面表现突出，问题解决有待提升"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm font-medium text-gray-700">优势项</label>
            <button onClick={addStrength} className="text-sm text-blue-600 hover:text-blue-700">+ 添加</button>
          </div>
          {strengths.map((item, index) => (
            <div key={index} className="bg-green-50 rounded-lg p-4 mb-3">
              <input
                type="text"
                value={item.competency}
                onChange={(e) => {
                  const newStrengths = [...strengths];
                  newStrengths[index].competency = e.target.value;
                  setStrengths(newStrengths);
                }}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg mb-2 text-sm font-medium"
                placeholder="能力名称"
              />
              <textarea
                value={item.comment}
                onChange={(e) => {
                  const newStrengths = [...strengths];
                  newStrengths[index].comment = e.target.value;
                  setStrengths(newStrengths);
                }}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg mb-2 text-sm"
                rows={2}
                placeholder="评价语"
              />
              <textarea
                value={item.behavior}
                onChange={(e) => {
                  const newStrengths = [...strengths];
                  newStrengths[index].behavior = e.target.value;
                  setStrengths(newStrengths);
                }}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                rows={2}
                placeholder="行为表现"
              />
            </div>
          ))}
        </div>

        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm font-medium text-gray-700">不足项</label>
            <button onClick={addWeakness} className="text-sm text-blue-600 hover:text-blue-700">+ 添加</button>
          </div>
          {weaknesses.map((item, index) => (
            <div key={index} className="bg-orange-50 rounded-lg p-4 mb-3">
              <input
                type="text"
                value={item.competency}
                onChange={(e) => {
                  const newWeaknesses = [...weaknesses];
                  newWeaknesses[index].competency = e.target.value;
                  setWeaknesses(newWeaknesses);
                }}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg mb-2 text-sm font-medium"
                placeholder="能力名称"
              />
              <textarea
                value={item.comment}
                onChange={(e) => {
                  const newWeaknesses = [...weaknesses];
                  newWeaknesses[index].comment = e.target.value;
                  setWeaknesses(newWeaknesses);
                }}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                rows={2}
                placeholder="评价语"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function OrganizationReportEditor({ candidate }: { candidate: Candidate }) {
  const [evaluation, setEvaluation] = useState('');
  const [strengths, setStrengths] = useState('');
  const [weaknesses, setWeaknesses] = useState('');
  const [valuesPotential, setValuesPotential] = useState('');
  const [suggestions, setSuggestions] = useState({ usage: '', risks: '' });

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="font-medium text-gray-900 mb-4">报告内容（可编辑）</h3>
      
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">个人评价</label>
          <textarea
            value={evaluation}
            onChange={(e) => setEvaluation(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={4}
            placeholder="请输入个人评价..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">个人优势</label>
          <textarea
            value={strengths}
            onChange={(e) => setStrengths(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={3}
            placeholder="请输入个人优势..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">个人不足</label>
          <textarea
            value={weaknesses}
            onChange={(e) => setWeaknesses(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={3}
            placeholder="请输入个人不足..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">价值观/发展潜力</label>
          <textarea
            value={valuesPotential}
            onChange={(e) => setValuesPotential(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={3}
            placeholder="请输入价值观/发展潜力..."
          />
        </div>

        <div className="bg-blue-50 rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">培养使用建议</label>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-gray-500 mb-1">使用建议</p>
              <textarea
                value={suggestions.usage}
                onChange={(e) => setSuggestions({ ...suggestions, usage: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                rows={2}
                placeholder="使用建议..."
              />
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-1">风险提示</p>
              <textarea
                value={suggestions.risks}
                onChange={(e) => setSuggestions({ ...suggestions, risks: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                rows={2}
                placeholder="风险提示..."
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function PersonalReportEditor({ candidate }: { candidate: Candidate }) {
  const [opening, setOpening] = useState('');
  const [strengthsNote, setStrengthsNote] = useState('');
  const [improvementsNote, setImprovementsNote] = useState('');
  const [suggestions, setSuggestions] = useState(['', '', '']);
  const [courses, setCourses] = useState([{ name: '', platform: '', quarter: '' }]);
  const [books, setBooks] = useState('');

  const updateSuggestion = (index: number, value: string) => {
    const newSuggestions = [...suggestions];
    newSuggestions[index] = value;
    setSuggestions(newSuggestions);
  };

  const addCourse = () => setCourses([...courses, { name: '', platform: '', quarter: '' }]);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="font-medium text-gray-900 mb-4">报告内容（可编辑）</h3>
      
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">开头段落（先扬后抑式评价）</label>
          <textarea
            value={opening}
            onChange={(e) => setOpening(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={4}
            placeholder="请输入开头段落..."
          />
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">【优势项】</label>
          <input
            type="text"
            value={strengthsNote}
            onChange={(e) => setStrengthsNote(e.target.value)}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg mb-2 text-sm"
            placeholder="优势项名称，如：沟通协作、用户思维"
          />
          <input
            type="text"
            value=""
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-xs text-gray-500"
            placeholder="标注分数情况，如：最高分项、超过5.5分项"
          />
        </div>

        <div className="bg-orange-50 rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">【待提升项】</label>
          <input
            type="text"
            value={improvementsNote}
            onChange={(e) => setImprovementsNote(e.target.value)}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg mb-2 text-sm"
            placeholder="待提升项名称，如：问题解决"
          />
          <input
            type="text"
            value=""
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-xs text-gray-500"
            placeholder="标注分数情况，如：低于5分项"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">【发展建议】</label>
          <div className="space-y-3">
            {suggestions.map((suggestion, index) => (
              <div key={index} className="flex items-start gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-medium flex-shrink-0 mt-1">
                  {index + 1}
                </span>
                <textarea
                  value={suggestion}
                  onChange={(e) => updateSuggestion(index, e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  rows={2}
                  placeholder={`第${index + 1}条建议...`}
                />
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700">【课程学习】</label>
            <button onClick={addCourse} className="text-sm text-blue-600 hover:text-blue-700">+ 添加</button>
          </div>
          <div className="space-y-2">
            {courses.map((course, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="text"
                  value={course.name}
                  onChange={(e) => {
                    const newCourses = [...courses];
                    newCourses[index].name = e.target.value;
                    setCourses(newCourses);
                  }}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  placeholder="课程名"
                />
                <input
                  type="text"
                  value={course.platform}
                  onChange={(e) => {
                    const newCourses = [...courses];
                    newCourses[index].platform = e.target.value;
                    setCourses(newCourses);
                  }}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  placeholder="公司/平台"
                />
                <input
                  type="text"
                  value={course.quarter}
                  onChange={(e) => {
                    const newCourses = [...courses];
                    newCourses[index].quarter = e.target.value;
                    setCourses(newCourses);
                  }}
                  className="w-32 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  placeholder="季度年份"
                />
              </div>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">【书籍阅读】</label>
          <textarea
            value={books}
            onChange={(e) => setBooks(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={2}
            placeholder="请输入书名，多个用顿号分隔，如：《第一性原理》、《创新者的窘境》"
          />
        </div>
      </div>
    </div>
  );
}

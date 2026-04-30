import React from 'react';
import { ArrowLeft, FileText, Users, User, Download, Upload, CheckCircle, Clock, Eye, X, Edit3, Check, Copy } from 'lucide-react';
import { useState, useEffect } from 'react';
import { generateFullReport, getCompetencyModel, getQuestionnaires, saveReport, getReports, downloadAsDocx, downloadFile } from '../api';
import { toast } from 'sonner';
import { MDXEditor, MDXEditorMethods } from '@mdxeditor/editor';

interface ReportGenerationProps {
  onBack: () => void;
  onNavigate: (page: string) => void;
}

type ReportType = 'feedback' | 'organization' | 'personal';
type ReportTypeChinese = '反馈版' | '组织版' | '个人版';

interface Report {
  type: ReportType;
  chineseType: ReportTypeChinese;
  name: string;
  status: 'draft' | 'generated' | 'submitted';
  submitTime?: string;
  canGenerate: boolean;
  content?: string;
  isGenerating?: boolean;
}

interface Candidate {
  id: string;
  name: string;
  scores: { [key: string]: number };
  totalScore: number;
}

const REPORT_TYPE_MAP: Record<ReportType, ReportTypeChinese> = {
  'feedback': '反馈版',
  'organization': '组织版',
  'personal': '个人版'
};

export default function ReportGeneration({ onBack, onNavigate }: ReportGenerationProps) {
  const [hasUploadedRecords, setHasUploadedRecords] = useState(false);
  const [pastedData, setPastedData] = useState(() => localStorage.getItem('report_pasted_data') || '');
  const [uploadedFileName, setUploadedFileName] = useState(() => localStorage.getItem('report_uploaded_filename') || '');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [dataPreview, setDataPreview] = useState(false);
  const [reports, setReports] = useState<Report[]>([
    { type: 'feedback', chineseType: '反馈版', name: '反馈版报告', status: 'draft', canGenerate: true },
    { type: 'organization', chineseType: '组织版', name: '组织版报告', status: 'draft', canGenerate: true },
    { type: 'personal', chineseType: '个人版', name: '个人版报告', status: 'draft', canGenerate: true },
  ]);
  const [selectedCandidate, setSelectedCandidate] = useState<string>('1');
  const [editingReport, setEditingReport] = useState<Report | null>(null);
  const [error, setError] = useState('');
  const [abilityStandards, setAbilityStandards] = useState<any>(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const editorRef = React.useRef<MDXEditorMethods>(null);

  useEffect(() => {
    loadAbilityStandards();
    loadSavedReports();
  }, []);

  const [editorKey, setEditorKey] = useState(0);

  useEffect(() => {
    setEditorKey(prev => prev + 1);
  }, [editingReport?.type]);

  const loadAbilityStandards = async () => {
    try {
      const model = await getCompetencyModel();
      if (model?.dimensions) {
        setAbilityStandards(model.dimensions);
      }
    } catch (err: any) {
      console.error('Load ability standards error:', err);
      if (err?.message?.includes('404') || err?.detail?.includes('未找到')) {
        setError('请先完成胜任力模型生成');
      }
    }
  };

  const loadSavedReports = async () => {
    try {
      const savedReports = await getReports();
      if (savedReports && savedReports.length > 0) {
        setReports(prevReports => {
          const updatedReports = [...prevReports];
          savedReports.forEach((saved: any) => {
            const reportType = saved.report_type as ReportType;
            const index = updatedReports.findIndex(r => r.type === reportType);
            if (index !== -1) {
              const contentData = saved.content;
              const contentStr = typeof contentData === 'object' 
                ? (contentData.content || contentData.report || JSON.stringify(contentData))
                : contentData;
              updatedReports[index] = {
                ...updatedReports[index],
                status: saved.status === 'submitted' ? 'submitted' : saved.status === 'published' ? 'generated' : 'draft',
                content: contentStr || '',
                submitTime: saved.updated_at ? new Date(saved.updated_at).toLocaleString('zh-CN') : undefined,
                canGenerate: true
              };
            }
          });
          return updatedReports;
        });
      }
    } catch (err: any) {
      console.error('加载保存的报告失败:', err);
    }
  };

  const candidates: Candidate[] = [
    { id: '1', name: '张三', scores: { '领导力': 85, '沟通协作': 90, '创新能力': 78 }, totalScore: 253 },
    { id: '2', name: '李四', scores: { '领导力': 78, '沟通协作': 82, '创新能力': 88 }, totalScore: 248 },
    { id: '3', name: '王五', scores: { '领导力': 92, '沟通协作': 85, '创新能力': 80 }, totalScore: 257 },
  ];

  const currentCandidate = candidates.find(c => c.id === selectedCandidate) || candidates[0];

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setUploadedFile(e.target.files[0]);
      setUploadedFileName(e.target.files[0].name);
      localStorage.setItem('report_uploaded_filename', e.target.files[0].name);
    }
  };

  const handlePreview = () => {
    setDataPreview(true);
  };

  const handleRemoveFile = () => {
    setUploadedFile(null);
    setUploadedFileName('');
    setDataPreview(false);
    localStorage.removeItem('report_uploaded_filename');
  };

  const handlePastedDataChange = (value: string) => {
    setPastedData(value);
    localStorage.setItem('report_pasted_data', value);
  };

  const handleClearData = () => {
    setPastedData('');
    setUploadedFile(null);
    setUploadedFileName('');
    setDataPreview(false);
    localStorage.removeItem('report_pasted_data');
    localStorage.removeItem('report_uploaded_filename');
  };

  const getBehaviorData = (): string => {
    if (uploadedFile) {
      return `文件: ${uploadedFile.name}`;
    }
    return pastedData;
  };

  const handleGenerateReport = async (report: Report) => {
    if (!report.canGenerate) return;
    
    const behaviorData = getBehaviorData();
    if (!behaviorData) {
      setError('请先导入测评数据');
      return;
    }

    if (!abilityStandards) {
      setError('请先完成胜任力模型生成');
      return;
    }

    setReports(reports.map(r => 
      r.type === report.type ? { ...r, isGenerating: true } : r
    ));
    setError('');

    try {
      const response = await generateFullReport({
        behavior_record: behaviorData,
        ability_standards: abilityStandards,
        report_type: report.chineseType
      });

      if (response.success && response.data) {
        const reportContent = response.data[report.chineseType === '反馈版' ? '反馈版报告' : report.chineseType === '个人版' ? '个人版报告' : '组织版报告'] || '';
        
        setReports(reports.map(r =>
          r.type === report.type ? { ...r, status: 'generated' as const, content: reportContent, isGenerating: false } : r
        ));
        
        if (reportContent) {
          setEditingReport({ ...report, content: reportContent, isGenerating: false });
        }
      } else {
        throw new Error('生成失败');
      }
    } catch (err: any) {
      console.error('Generate report error:', err);
      const errorMessage = err?.message || err?.detail || JSON.stringify(err) || '生成报告失败，请重试';
      setError(errorMessage);
      setReports(reports.map(r => 
        r.type === report.type ? { ...r, isGenerating: false } : r
      ));
    }
  };

  const reloadAbilityStandards = async () => {
    try {
      const model = await getCompetencyModel();
      if (model?.dimensions) {
        setAbilityStandards(model.dimensions);
        return true;
      }
    } catch (err: any) {
      console.error('Reload ability standards error:', err);
      if (err?.status === 404 || err?.detail?.includes('未找到')) {
        setError('请先在"胜任力模型"页面生成模型');
      } else {
        setError(err.message || '获取模型失败');
      }
      return false;
    }
    return false;
  };

  const handleGenerateWithReload = async (report: Report) => {
    if (!abilityStandards) {
      const hasModel = await reloadAbilityStandards();
      if (!hasModel) return;
    }
    await handleGenerateReport(report);
  };

  const handleSubmitReport = async () => {
    if (!editingReport) return;

    try {
      await saveReport({
        record_id: 1,
        report_type: editingReport.type,
        candidate_id: selectedCandidate,
        candidate_name: currentCandidate.name,
        scores_data: currentCandidate.scores,
        total_score: currentCandidate.totalScore,
        content: { content: editingReport.content },
        status: 'submitted',
      });

      setReports(reports.map(r => {
        if (r.type === editingReport.type) {
          return { ...r, status: 'submitted' as const, submitTime: new Date().toLocaleString('zh-CN') };
        }
        return r;
      }));

      setEditingReport(null);
      alert('报告已提交并保存到数据库！');
    } catch (err: any) {
      console.error('保存报告失败:', err);
      alert('保存报告失败: ' + (err.message || '未知错误'));
    }
  };

  const handleDownload = async (reportType: ReportType) => {
    const report = reports.find(r => r.type === reportType);
    if (!report?.content) {
      toast.error('报告内容为空，无法下载');
      return;
    }
    try {
      const filename = `${reportType}报告.docx`;
      const blob = await downloadAsDocx(report.content, filename);
      downloadFile(blob, filename);
      toast.success('下载成功');
    } catch (err: any) {
      toast.error(err.message || '下载失败');
    }
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

  const handleCopyContent = async () => {
    const contentText = getReportContent(editingReport);
    if (!contentText) return;
    try {
      await navigator.clipboard.writeText(contentText);
      alert('内容已复制到剪贴板！');
    } catch (err) {
      console.error('复制失败:', err);
      alert('复制失败，请手动复制');
    }
  };

  const getReportContent = (report: Report): string => {
    if (!report?.content) return '';
    if (typeof report.content === 'string') return report.content;
    if (typeof report.content === 'object') {
      const contentObj = report.content as any;
      return contentObj.content || contentObj.report || contentObj.text || JSON.stringify(report.content);
    }
    return String(report.content);
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
              <h1 className="font-semibold text-gray-900">
                编辑 - {editingReport.name}
              </h1>
            </div>
          </div>
        </header>

        <main className="max-w-5xl mx-auto px-6 py-8">
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium text-gray-900">
                报告内容
              </h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopyContent}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200"
                >
                  <Copy size={16} />
                  复制
                </button>
                <button
                  onClick={() => {
                    if (isEditMode) {
                      const content = editorRef.current?.getMarkdown();
                      if (content !== undefined) {
                        setEditingReport({ ...editingReport, content });
                        setReports(reports.map(r => 
                          r.type === editingReport.type ? { ...r, content } : r
                        ));
                      }
                    }
                    setIsEditMode(!isEditMode);
                  }}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    isEditMode 
                      ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                      : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  }`}
                >
                  {isEditMode ? <Check size={16} /> : <Edit3 size={16} />}
                  {isEditMode ? '保存' : '编辑'}
                </button>
              </div>
            </div>
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              {isEditMode ? (
                <div className="p-4">
                  <textarea
                    value={getReportContent(editingReport)}
                    onChange={(e) => {
                      setEditingReport({ ...editingReport, content: e.target.value });
                    }}
                    className="w-full h-[500px] p-4 border border-gray-300 rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="编辑报告内容..."
                  />
                </div>
              ) : (
                <div className="bg-gray-50 p-6 max-h-[500px] overflow-y-auto prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700">
                    {getReportContent(editingReport) || '暂无内容'}
                  </pre>
                </div>
              )}
            </div>
          </div>

          <div className="flex gap-4 mt-6">
            <button
              onClick={handleBackToList}
              className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              返回列表
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
          <h3 className="font-medium text-gray-900 mb-4">导入测评数据</h3>
          <p className="text-sm text-gray-500 mb-4">选择以下方式之一导入测评数据</p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
                  <Upload size={20} />
                </div>
                <h4 className="font-medium text-gray-900">上传文件</h4>
              </div>
              <p className="text-sm text-gray-500 mb-3">上传Excel、Word或PDF文件</p>
              
              {!uploadedFile && !uploadedFileName ? (
                <div className="border-2 border-dashed border-gray-300 rounded-lg py-4 text-center hover:border-blue-400 transition-colors" style={{ minHeight: '78px' }}>
                  <input
                    type="file"
                    accept=".xlsx,.xls,.docx,.doc,.pdf"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="report-file-upload"
                  />
                  <label
                    htmlFor="report-file-upload"
                    className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer text-sm font-medium"
                  >
                    选择文件
                  </label>
                  <p className="text-xs text-gray-400 mt-2">支持 .xlsx, .xls, .docx, .pdf</p>
                </div>
              ) : (
                <div className="bg-blue-50 border border-blue-200 rounded-lg px-3" style={{ minHeight: '78px', display: 'flex', alignItems: 'center' }}>
                  <div className="flex items-center justify-between w-full">
                    <div className="flex items-center gap-2">
                      <FileText className="text-blue-600" size={18} />
                      <span className="text-sm text-gray-900 truncate">{uploadedFile?.name || uploadedFileName}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={handlePreview}
                        className="px-3 py-1 bg-blue-600 text-white rounded text-xs font-medium"
                      >
                        解析
                      </button>
                      <button
                        onClick={handleRemoveFile}
                        className="p-1 text-gray-400 hover:text-red-500"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center text-green-600">
                  <FileText size={20} />
                </div>
                <h4 className="font-medium text-gray-900">粘贴文本</h4>
              </div>
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm text-gray-500">直接在文本框中粘贴数据</p>
                {(pastedData || uploadedFileName) && (
                  <button
                    onClick={handleClearData}
                    className="text-xs text-red-600 hover:text-red-700"
                  >
                    清空数据
                  </button>
                )}
              </div>
              <textarea
                value={pastedData}
                onChange={(e) => handlePastedDataChange(e.target.value)}
                placeholder="请粘贴测评数据，如：
A1-小组讨论-问题解决-行为记录内容...
A1-小组讨论-沟通协作-行为记录内容..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-sm resize-none"
                style={{ height: '78px' }}
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">生成报告</h2>
          <p className="text-gray-600">选择要生成的报告类型</p>
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
                    </div>
                    <p className="text-sm text-gray-500 mb-2">
                      {report.type === 'feedback' && '包含一句话评价、优势项和不足项，适合快速反馈'}
                      {report.type === 'organization' && '包含详细评价、数据分析和雷达图，供组织决策使用'}
                      {report.type === 'personal' && '包含发展建议、学习课程和书籍推荐，帮助个人提升'}
                    </p>
                    {getStatusBadge(report)}
                    {report.isGenerating && (
                      <p className="text-sm text-amber-600 mt-2">预计需要10-20分钟，您可以先完成其他工作</p>
                    )}
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
                      <button
                        onClick={() => handleGenerateWithReload(report)}
                        disabled={report.isGenerating}
                        className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors text-sm font-medium disabled:bg-gray-400"
                      >
                        {report.isGenerating ? '重新生成中...' : '重新生成'}
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
                      <button
                        onClick={() => handleGenerateWithReload(report)}
                        disabled={report.isGenerating}
                        className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors text-sm font-medium disabled:bg-gray-400"
                      >
                        {report.isGenerating ? '重新生成中...' : '重新生成'}
                      </button>
                    </>
                  )}
                  {report.status === 'draft' && report.canGenerate && (
                    <button
                      onClick={() => handleGenerateWithReload(report)}
                      disabled={report.isGenerating}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:bg-gray-400"
                    >
                      {report.isGenerating ? '生成中...' : '生成'}
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
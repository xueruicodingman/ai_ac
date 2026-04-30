import { ArrowLeft, Upload, Download, Edit2, Clock, CheckCircle, FileText, X, Copy, Check } from 'lucide-react';
import { useState, useEffect } from 'react';
import { getCompetencyModel, getEvaluationMatrix, generateQuestionnaire, getQuestionnaires, saveQuestionnaire, uploadFile, getFileContent } from '../api';
import { toast } from 'sonner';

interface QuestionBookProps {
  onBack: () => void;
  onNavigate: (page: string) => void;
}

interface Book {
  id: string;
  name: string;
  duration: string;
  status: 'draft' | 'submitted';
  submitTime?: string;
  backgroundFile?: File | null;
  uploadedFileId?: string;
  uploadedFileName?: string;
  textRequirement?: string;
  jobLevel?: string;
  content?: string;
}

export default function QuestionBook({ onBack, onNavigate }: QuestionBookProps) {
  const allTools = [
    { id: 'beh', name: 'BEI行为事件访谈', duration: '60分钟' },
    { id: 'lgd', name: '无领导小组讨论', duration: '90分钟' },
    { id: 'roleplay', name: '角色扮演', duration: '45分钟' },
    { id: 'case', name: '案例分析', duration: '120分钟' },
    { id: 'vision', name: '个人愿景', duration: '30分钟' },
  ];

  // 工具对应的考察能力（从评估矩阵中获取）
  const [toolAbilities, setToolAbilities] = useState<Record<string, string[]>>({});
  const [books, setBooks] = useState<Book[]>(allTools.map(t => ({ ...t, status: 'draft' as const })));
  const [editingBook, setEditingBook] = useState<Book | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [isEditMode, setIsEditMode] = useState(false);
  const [competencyModel, setCompetencyModel] = useState<any>(null);
  const [evaluationMatrix, setEvaluationMatrix] = useState<any>(null);

  useEffect(() => {
    loadSavedData();
  }, []);

  const isToolEnabled = (toolId: string) => {
    return toolAbilities[toolId] && toolAbilities[toolId].length > 0;
  };

  const loadSavedData = async () => {
    try {
      const modelData = await getCompetencyModel();
      setCompetencyModel(modelData);
      
      const matrixData = await getEvaluationMatrix();
      console.log('Matrix data from API:', matrixData);
      setEvaluationMatrix(matrixData);
      
      // 从评估矩阵中获取每个工具对应的考察能力
      const abilitiesMap: Record<string, string[]> = {};
      if (matrixData && matrixData.matrix) {
        console.log('Matrix content:', matrixData.matrix);
        // 矩阵格式: {能力名: {工具id: true/false}}
        for (const [ability, toolsObj] of Object.entries(matrixData.matrix)) {
          console.log('Ability:', ability, 'Tools:', toolsObj);
          for (const [toolId, enabled] of Object.entries(toolsObj as Record<string, boolean>)) {
            if (enabled) {
              if (!abilitiesMap[toolId]) {
                abilitiesMap[toolId] = [];
              }
              abilitiesMap[toolId].push(ability);
            }
          }
        }
      }
      console.log('Tool abilities map:', abilitiesMap);
      setToolAbilities(abilitiesMap);
      
      // 加载已保存的问卷
      const questionnaires = await getQuestionnaires();
      
      if (questionnaires && questionnaires.length > 0) {
        setBooks(prev => prev.map(book => {
          const saved = questionnaires.find((q: any) => q.tool_id === book.id);
          if (saved) {
            return {
              ...book,
              status: 'submitted' as const,
              submitTime: saved.updated_at,
              content: saved.content
            };
          }
          return book;
        }));
      }
    } catch (err) {
      console.log('No saved data found');
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    console.log('handleFileUpload called, editingBook:', editingBook);
    console.log('handleFileUpload files:', e.target.files);
    
    if (e.target.files && editingBook) {
      const file = e.target.files[0];
      console.log('Uploading file:', file.name);
      
      try {
        const uploadResult = await uploadFile(file);
        console.log('Upload result:', uploadResult);
        
        const fileId = uploadResult.data?.id ?? uploadResult.id;
        const fileName = uploadResult.data?.name ?? uploadResult.name;
        console.log('Setting file info - id:', fileId, 'name:', fileName);
        
        setEditingBook({
          ...editingBook,
          backgroundFile: file,
          uploadedFileId: String(fileId),
          uploadedFileName: fileName,
        });
        localStorage.setItem(`questionnaire_${editingBook.id}_uploaded_file`, fileName);
        localStorage.setItem(`questionnaire_${editingBook.id}_background_file`, file.name);
        localStorage.setItem(`questionnaire_${editingBook.id}_file_id`, String(fileId));
        console.log('editingBook updated');
      } catch (err: any) {
        console.error('File upload failed:', err);
        setError('文件上传失败: ' + (err.message || '未知错误'));
      }
    } else {
      console.log('Cannot upload - editingBook is null/undefined');
    }
  };

  const handleRemoveBackgroundFile = () => {
    if (editingBook) {
      setEditingBook({
        ...editingBook,
        backgroundFile: null,
        uploadedFileId: undefined,
        uploadedFileName: undefined,
        textRequirement: undefined,
      });
      localStorage.removeItem(`questionnaire_${editingBook.id}_background_file`);
      localStorage.removeItem(`questionnaire_${editingBook.id}_text_requirement`);
      localStorage.removeItem(`questionnaire_${editingBook.id}_uploaded_file`);
      localStorage.removeItem(`questionnaire_${editingBook.id}_file_id`);
    }
  };

  const handleCopyContent = async () => {
    if (!editingBook?.content) return;
    try {
      await navigator.clipboard.writeText(editingBook.content);
      alert('内容已复制到剪贴板！');
    } catch (err) {
      console.error('复制失败:', err);
      alert('复制失败，请手动复制');
    }
  };

  const handleGenerate = async () => {
    if (!editingBook || !competencyModel || !evaluationMatrix) {
      setError('请先确保已提交胜任力模型和评估矩阵');
      return;
    }

    setError('');
    setIsGenerating(true);

    try {
      // 获取背景材料内容
      let backgroundFileContent = null;
      if (editingBook.uploadedFileId) {
        try {
          console.log('获取文件内容 - file_id:', editingBook.uploadedFileId);
          const fileContentResult = await getFileContent(editingBook.uploadedFileId);
          console.log('文件内容结果:', fileContentResult);
          backgroundFileContent = fileContentResult.data?.content || null;
          console.log('解析后的背景材料内容:', backgroundFileContent);
          console.log('内容长度:', backgroundFileContent?.length);
        } catch (err) {
          console.error('Failed to get file content:', err);
        }
      }

      console.log('开始生成题本 - tool_id:', editingBook.id);
      console.log('传递的背景材料:', backgroundFileContent?.substring(0, 200) + '...');
      
      const response = await generateQuestionnaire(
        editingBook.id,
        competencyModel,
        evaluationMatrix,
        backgroundFileContent,
        editingBook.textRequirement || ""
      );

      console.log('题本生成结果:', response);
      
      const generatedContent = response.data?.content || '';
      console.log('生成的题本内容:', generatedContent.substring(0, 200) + '...');
      console.log('generatedContent 类型:', typeof generatedContent);
      console.log('generatedContent 长度:', generatedContent.length);
      
      // 更新books状态
      setBooks(prev => prev.map(book => 
        book.id === editingBook.id 
          ? { ...book, content: generatedContent, status: 'submitted' as const, submitTime: new Date().toISOString() }
          : book
      ));

      // 保存到后端
      await saveQuestionnaire({
        tool_id: editingBook.id,
        model_id: competencyModel.id,
        matrix_id: evaluationMatrix.id,
        content: generatedContent
      });

      // 更新editingBook的内容，保留在当前页面
      setEditingBook({
        ...editingBook,
        content: generatedContent
      });
    } catch (err: any) {
      setError(err.message || '生成失败');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSubmit = () => {
    if (!editingBook) return;

    setBooks(books.map(book =>
      book.id === editingBook.id
        ? {
            ...book,
            status: 'submitted' as const,
            submitTime: new Date().toLocaleString('zh-CN'),
            backgroundFile: editingBook.backgroundFile,
            textRequirement: editingBook.textRequirement,
            content: editingBook.content,
          }
        : book
    ));

    setEditingBook(null);
    toast.success('题本已提交！', {
      action: {
        label: '前往测评报告',
        onClick: () => window.location.hash = 'report',
      },
      duration: 5000,
    });
  };

  const handleNextBook = () => {
    if (!editingBook) return;

    const currentIndex = books.findIndex(b => b.id === editingBook.id);
    const nextIndex = (currentIndex + 1) % books.length;
    const nextBook = books[nextIndex];

    const existingBook = books.find(b => b.id === nextBook.id);
    setEditingBook({
      ...nextBook,
      backgroundFile: existingBook?.backgroundFile,
      textRequirement: existingBook?.textRequirement,
      content: existingBook?.content,
    });
  };

  const handleDownload = (bookName: string) => {
    alert(`正在下载：${bookName}`);
  };

  if (editingBook) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setEditingBook(null)}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft size={20} />
                <span>返回列表</span>
              </button>
              <div className="h-6 w-px bg-gray-300" />
              <h1 className="font-semibold text-gray-900">题本编辑 - {editingBook.name}</h1>
            </div>
          </div>
        </header>

        <main className="max-w-5xl mx-auto px-6 py-8">
          {editingBook && editingBook.id !== 'beh' && (
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
            <h3 className="font-medium text-gray-900 mb-4">背景材料（可选）</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
                    <Upload size={20} />
                  </div>
                  <h4 className="font-medium text-gray-900">上传文件</h4>
                </div>
                <p className="text-sm text-gray-500 mb-3">上传PDF、Word或Excel文件</p>
                
                {!editingBook.backgroundFile && !editingBook.uploadedFileName ? (
                  <div className="border-2 border-dashed border-gray-300 rounded-lg py-4 text-center hover:border-blue-400 transition-colors" style={{ minHeight: '78px' }}>
                    <input
                      type="file"
                      accept=".pdf,.doc,.docx,.xls,.xlsx"
                      onChange={handleFileUpload}
                      className="hidden"
                      id="background-upload"
                    />
                    <label
                      htmlFor="background-upload"
                      className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer text-sm font-medium"
                    >
                      选择文件
                    </label>
                    <p className="text-xs text-gray-400 mt-2">支持 .pdf, .doc, .docx, .xls, .xlsx</p>
                  </div>
                ) : (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <FileText className="text-blue-600 flex-shrink-0" size={18} />
                        <span className="text-sm text-gray-900 truncate">{editingBook.backgroundFile?.name || editingBook.uploadedFileName}</span>
                      </div>
                      <button
                        onClick={handleRemoveBackgroundFile}
                        className="p-1 text-gray-400 hover:text-red-500 flex-shrink-0"
                      >
                        <X size={16} />
                      </button>
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
                  <p className="text-sm text-gray-500">直接在文本框中粘贴背景材料</p>
                  {(editingBook.textRequirement) && (
                    <button
                      onClick={() => {
                        if (editingBook) {
                          setEditingBook({ ...editingBook, textRequirement: undefined });
                          localStorage.removeItem(`questionnaire_${editingBook.id}_text_requirement`);
                        }
                      }}
                      className="text-xs text-red-500 hover:text-red-600"
                    >
                      清空
                    </button>
                  )}
                </div>
                <textarea
                  value={editingBook.textRequirement || ''}
                  onChange={(e) => {
                    if (editingBook) {
                      setEditingBook({ ...editingBook, textRequirement: e.target.value });
                      localStorage.setItem(`questionnaire_${editingBook.id}_text_requirement`, e.target.value);
                    }
                  }}
                  placeholder="在此粘贴背景材料文本内容..."
                  className="w-full h-[78px] px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-sm resize-none"
                />
              </div>
            </div>
          </div>
          )}

          {editingBook && ['lgd', 'roleplay', 'case', 'vision'].includes(editingBook.id) && (
            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
              <h3 className="font-medium text-gray-900 mb-4">考生岗位层级</h3>
              <input
                type="text"
                value={editingBook.jobLevel || ''}
                onChange={(e) => {
                  if (editingBook) {
                    setEditingBook({ ...editingBook, jobLevel: e.target.value });
                  }
                }}
                placeholder="如：基层管理者、中层管理者、高层管理者"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed mb-2"
          >
            {isGenerating ? '正在生成中...' : (editingBook?.content ? '重新生成' : '生成题本')}
          </button>

          {isGenerating && (
            <div className="text-sm text-gray-500 mb-4 text-center">
              预计需要5-15min左右，正是摸鱼好时机！
            </div>
          )}

          {error && (
            <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg text-sm mb-4">
              {error}
            </div>
          )}

          {editingBook.content && (
            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-gray-900">题本内容</h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopyContent}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200"
                  >
                    <Copy size={16} />
                    复制
                  </button>
                  <button
                    onClick={() => setIsEditMode(!isEditMode)}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      isEditMode 
                        ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                        : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                    }`}
                  >
                    {isEditMode ? <Check size={16} /> : <Edit2 size={16} />}
                    {isEditMode ? '保存' : '编辑'}
                  </button>
                </div>
              </div>
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                {isEditMode ? (
                  <textarea
                    value={editingBook.content}
                    onChange={(e) => {
                      if (editingBook) {
                        setEditingBook({ ...editingBook, content: e.target.value });
                      }
                    }}
                    className="w-full px-4 py-3 border-0 focus:outline-none resize-none font-mono text-sm"
                    rows={20}
                  />
                ) : (
                  <div className="bg-gray-50 p-6 max-h-[500px] overflow-y-auto">
                    <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700">
                      {editingBook.content}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="flex gap-4">
            <button
              onClick={() => setEditingBook(null)}
              className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              返回列表
            </button>
            <button
              onClick={handleSubmit}
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
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft size={20} />
              <span>返回首页</span>
            </button>
            <div className="h-6 w-px bg-gray-300" />
            <h1 className="font-semibold text-gray-900">题本生成</h1>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {Object.keys(toolAbilities).length === 0 ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
            <p className="text-yellow-800">
              请先在评估矩阵页面选择要使用的测评工具，然后返回题本生成页面。
            </p>
          </div>
        ) : (
          <>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">测评题本</h2>
              <p className="text-gray-600">根据评估矩阵，已为您配置 {Object.keys(toolAbilities).length} 个测评工具</p>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
              <div className="flex items-start justify-between">
                <div className="flex gap-4">
                  <div className="w-12 h-12 rounded-lg bg-green-50 flex items-center justify-center text-green-600">
                    <FileText size={24} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-gray-900">评委手册</h3>
                      {(() => {
                        const handbookContent = localStorage.getItem('judge_handbook_content');
                        return handbookContent ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                            <CheckCircle size={12} />
                            已提交
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                            草稿
                          </span>
                        );
                      })()}
                    </div>
                    <p className="text-sm text-gray-500">
                      基于已生成的题本自动生成评委手册，支持在线编辑和下载
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {(() => {
                    const handbookContent = localStorage.getItem('judge_handbook_content');
                    return handbookContent ? (
                      <>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(handbookContent).then(() => {
                              alert('内容已复制到剪贴板！');
                            }).catch(() => {
                              alert('复制失败，请手动复制');
                            });
                          }}
                          className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                          title="一键复制"
                        >
                          <Copy size={16} />
                        </button>
                        <button
                          onClick={() => alert('正在下载评委手册...')}
                          className="px-3 py-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 transition-colors text-sm font-medium"
                          title="下载"
                        >
                          <Download size={16} />
                        </button>
                      </>
                    ) : null;
                  })()}
                  <button
                    onClick={() => onNavigate('judge-manual')}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium whitespace-nowrap"
                  >
                    进入编辑
                  </button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {books.map((book) => {
                const enabled = isToolEnabled(book.id);
                const abilities = toolAbilities[book.id] || [];
                return (
            <div
              key={book.id}
              className={`rounded-lg border p-6 transition-shadow ${
                enabled 
                  ? 'bg-white border-gray-200 hover:shadow-lg' 
                  : 'bg-gray-100 border-gray-300'
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900 mb-2">{book.name}</h3>
                  <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                    <Clock size={16} />
                    <span>{book.duration}</span>
                  </div>
                  {enabled && abilities.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-gray-500 mb-1">考察能力：</p>
                      <div className="flex flex-wrap gap-1">
                        {abilities.map((ability, idx) => (
                          <span key={idx} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">
                            {ability}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {!enabled && (
                    <div className="mt-2">
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-400 text-xs rounded">
                        未在评估矩阵中选择
                      </span>
                    </div>
                  )}
                  <div className="flex items-center gap-2 mt-3">
                    {book.status === 'submitted' ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                        <CheckCircle size={12} />
                        已提交
                      </span>
                    ) : enabled ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                        草稿
                      </span>
                    ) : null}
                  </div>
                </div>
              </div>

              {book.submitTime && (
                <p className="text-xs text-gray-400 mb-4">提交时间：{book.submitTime}</p>
              )}

                  <div className="flex gap-2">
                {enabled ? (
                  <button
                    onClick={() => {
                      const savedFileName = localStorage.getItem(`questionnaire_${book.id}_uploaded_file`);
                      const savedText = localStorage.getItem(`questionnaire_${book.id}_text_requirement`);
                      const savedFileId = localStorage.getItem(`questionnaire_${book.id}_file_id`);
                      setEditingBook({
                        ...book,
                        textRequirement: savedText || undefined,
                        uploadedFileName: savedFileName || undefined,
                        uploadedFileId: savedFileId || undefined,
                      });
                    }}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
                  >
                    <Edit2 size={16} />
                    编辑
                  </button>
                ) : (
                  <button
                    disabled
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-400 rounded-lg text-sm font-medium cursor-not-allowed"
                  >
                    <Edit2 size={16} />
                    不可编辑
                  </button>
                )}
                {book.status === 'submitted' && book.content && (
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(book.content || '').then(() => {
                        alert('内容已复制到剪贴板！');
                      }).catch(() => {
                        alert('复制失败，请手动复制');
                      });
                    }}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                    title="一键复制"
                  >
                    <Copy size={16} />
                  </button>
                )}
                {book.status === 'submitted' && enabled && (
                  <button
                    onClick={() => handleDownload(book.name)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <Download size={16} />
                  </button>
                )}
              </div>
            </div>
                );
              })}
        </div>
        </>
        )}
      </main>
    </div>
  );
}

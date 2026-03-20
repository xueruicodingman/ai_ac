import { ArrowLeft, Upload, Download, Edit2, Clock, CheckCircle, FileText } from 'lucide-react';
import { useState } from 'react';

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
  textRequirement?: string;
  content?: string;
}

export default function QuestionBook({ onBack, onNavigate }: QuestionBookProps) {
  const [books, setBooks] = useState<Book[]>([
    { id: 'bei', name: 'BEI行为事件访谈', duration: '60分钟', status: 'draft' },
    { id: 'lgd', name: '无领导小组讨论', duration: '90分钟', status: 'draft' },
    { id: 'role', name: '角色扮演', duration: '45分钟', status: 'draft' },
    { id: 'case', name: '案例分析', duration: '120分钟', status: 'draft' },
    { id: 'vision', name: '个人愿景', duration: '30分钟', status: 'draft' },
  ]);

  const [editingBook, setEditingBook] = useState<Book | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && editingBook) {
      setEditingBook({
        ...editingBook,
        backgroundFile: e.target.files[0],
      });
    }
  };

  const handleGenerate = () => {
    if (!editingBook) return;
    setIsGenerating(true);

    setTimeout(() => {
      const generatedContent = `# ${editingBook.name}题本

## 一、任务说明
本环节为${editingBook.name}，您有${editingBook.duration}的时间进行准备。

## 二、背景信息
（根据评估矩阵和背景材料自动生成）

## 三、任务要求
1. 请围绕能力维度设计具体任务
2. 任务应能够有效评估被测者的相关能力
`;
      setEditingBook({
        ...editingBook,
        content: generatedContent,
      });
      setIsGenerating(false);
    }, 2000);
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
    alert('题本已提交！');
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
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
            <h3 className="font-medium text-gray-900 mb-4">背景材料（可选）</h3>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
              <Upload className="mx-auto mb-3 text-gray-400" size={32} />
              <p className="text-sm text-gray-600 mb-2">上传背景材料</p>
              <p className="text-xs text-gray-400 mb-4">支持 PDF、Word、Excel</p>
              <input
                type="file"
                accept=".pdf,.doc,.docx,.xls,.xlsx"
                onChange={handleFileUpload}
                className="hidden"
                id="background-upload"
              />
              <label
                htmlFor="background-upload"
                className="inline-block px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors cursor-pointer text-sm font-medium"
              >
                选择文件
              </label>
            </div>
            {editingBook.backgroundFile && (
              <div className="mt-4 bg-gray-50 rounded-lg px-4 py-3">
                <span className="text-sm text-gray-700">{editingBook.backgroundFile.name}</span>
              </div>
            )}
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
            <h3 className="font-medium text-gray-900 mb-4">文字要求（可选）</h3>
            <textarea
              value={editingBook.textRequirement || ''}
              onChange={(e) => {
                if (editingBook) {
                  setEditingBook({ ...editingBook, textRequirement: e.target.value });
                }
              }}
              placeholder="请输入对题本的具体要求..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={4}
            />
          </div>

          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed mb-6"
          >
            {isGenerating ? '正在生成中...' : '生成题本'}
          </button>

          {editingBook.content && (
            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
              <h3 className="font-medium text-gray-900 mb-4">题本内容（可编辑）</h3>
              <textarea
                value={editingBook.content}
                onChange={(e) => {
                  if (editingBook) {
                    setEditingBook({ ...editingBook, content: e.target.value });
                  }
                }}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none font-mono text-sm"
                rows={15}
              />
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
              onClick={handleNextBook}
              className="flex-1 bg-blue-50 text-blue-600 py-3 rounded-lg hover:bg-blue-100 transition-colors font-medium"
            >
              下一个题本
            </button>
            <button
              onClick={handleSubmit}
              className="flex-1 bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition-colors font-medium"
            >
              提交题本
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
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">测评题本</h2>
          <p className="text-gray-600">选择题本进行编辑或生成新题本</p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
          <div className="flex items-start justify-between">
            <div className="flex gap-4">
              <div className="w-12 h-12 rounded-lg bg-green-50 flex items-center justify-center text-green-600">
                <FileText size={24} />
              </div>
              <div>
                <h3 className="font-medium text-gray-900 mb-1">评委手册</h3>
                <p className="text-sm text-gray-500">
                  基于已生成的题本自动生成评委手册，支持在线编辑和下载
                </p>
              </div>
            </div>
            <button
              onClick={() => onNavigate('judge-manual')}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium whitespace-nowrap"
            >
              进入编辑
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {books.map((book) => (
            <div
              key={book.id}
              className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900 mb-2">{book.name}</h3>
                  <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                    <Clock size={16} />
                    <span>{book.duration}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {book.status === 'submitted' ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                        <CheckCircle size={12} />
                        已提交
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                        草稿
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {book.submitTime && (
                <p className="text-xs text-gray-400 mb-4">提交时间：{book.submitTime}</p>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => setEditingBook(book)}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
                >
                  <Edit2 size={16} />
                  编辑
                </button>
                {book.status === 'submitted' && (
                  <button
                    onClick={() => handleDownload(book.name)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <Download size={16} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

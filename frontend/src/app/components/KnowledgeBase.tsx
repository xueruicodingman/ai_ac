import { useState, useEffect } from 'react';
import { ArrowLeft, Upload, Trash2, RefreshCw, FileText, BookOpen, Save, X, Edit2, Plus } from 'lucide-react';
import { getKnowledgeBase, uploadDocument, updateChunks, deleteKnowledgeBase, useHandbookAsSource, updateChunkContent, deleteChunk, addChunk } from '../api';

interface KnowledgeBaseProps {
  onBack: () => void;
  initialTool?: string;
}

const TOOLS = [
  { id: 'beh', name: '行为面试(BEI)' },
  { id: 'roleplay', name: '角色扮演' },
  { id: 'lgd', name: '无领导小组讨论' },
  { id: 'case', name: '案例分析' },
  { id: 'vision', name: '个人愿景' }
];

export default function KnowledgeBase({ onBack, initialTool = 'roleplay' }: KnowledgeBaseProps) {
  const [selectedTool, setSelectedTool] = useState(initialTool);
  const [knowledgeBase, setKnowledgeBase] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [maxChunkLength, setMaxChunkLength] = useState(500);
  const [separator, setSeparator] = useState('##');
  const [editingChunk, setEditingChunk] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ title: '', content: '', keywords: '' });

  useEffect(() => {
    loadKnowledgeBase();
  }, [selectedTool]);

  const loadKnowledgeBase = async () => {
    setLoading(true);
    try {
      const data = await getKnowledgeBase(selectedTool);
      setKnowledgeBase(data);
      if (data.chunk_config) {
        setMaxChunkLength(data.chunk_config.max_length || 500);
        setSeparator(data.chunk_config.separator || '##');
      }
    } catch (e) {
      console.error(e);
      setKnowledgeBase({ chunks: [], source_documents: [] });
    }
    setLoading(false);
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setUploading(true);
    try {
      await uploadDocument(selectedTool, file, { separator, max_length: maxChunkLength });
      await loadKnowledgeBase();
      alert('上传成功');
    } catch (err: any) {
      alert(err.message || '上传失败');
    }
    setUploading(false);
  };

  const handleRechunk = async () => {
    setLoading(true);
    try {
      await updateChunks(selectedTool, { separator, max_length: maxChunkLength });
      await loadKnowledgeBase();
      alert('重新切片成功');
    } catch (err: any) {
      alert(err.message || '重新切片失败');
    }
    setLoading(false);
  };

  const handleDelete = async () => {
    if (!confirm('确认删除知识库？')) return;
    try {
      await deleteKnowledgeBase(selectedTool);
      await loadKnowledgeBase();
      alert('删除成功');
    } catch (err: any) {
      alert(err.message || '删除失败');
    }
  };

  const handleUseHandbook = async () => {
    setLoading(true);
    try {
      await useHandbookAsSource(selectedTool, { separator, max_length: maxChunkLength });
      await loadKnowledgeBase();
      alert('已使用评委手册作为知识库');
    } catch (err: any) {
      alert(err.message || '使用评委手册失败，请确认已生成评委手册');
    }
    setLoading(false);
  };

  const handleEditChunk = (chunk: any) => {
    setEditingChunk(chunk.id);
    setEditForm({
      title: chunk.title || '',
      content: chunk.content || '',
      keywords: chunk.keywords?.join(', ') || ''
    });
  };

  const handleSaveChunk = async (chunkId: string) => {
    try {
      const keywords = editForm.keywords.split(',').map(k => k.trim()).filter(k => k);
      await updateChunkContent(selectedTool, chunkId, {
        title: editForm.title,
        content: editForm.content,
        keywords
      });
      await loadKnowledgeBase();
      setEditingChunk(null);
      alert('保存成功');
    } catch (err: any) {
      alert(err.message || '保存失败');
    }
  };

  const handleCancelEdit = () => {
    setEditingChunk(null);
    setEditForm({ title: '', content: '', keywords: '' });
  };

  const handleDeleteChunk = async (chunkId: string) => {
    if (!confirm('确认删除该切片？')) return;
    try {
      await deleteChunk(selectedTool, chunkId);
      await loadKnowledgeBase();
      alert('删除成功');
    } catch (err: any) {
      alert(err.message || '删除失败');
    }
  };

  const handleAddChunk = async () => {
    try {
      await addChunk(selectedTool, { title: '新切片', content: '', keywords: [] });
      await loadKnowledgeBase();
      alert('新增成功');
    } catch (err: any) {
      alert(err.message || '新增失败');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4 flex items-center gap-4">
        <button onClick={onBack} className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-xl font-semibold">知识库管理</h1>
      </div>

      <div className="p-6 max-w-6xl mx-auto">
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">选择测评工具</label>
          <div className="flex gap-2 flex-wrap">
            {TOOLS.map(tool => (
              <button
                key={tool.id}
                onClick={() => setSelectedTool(tool.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedTool === tool.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                {tool.name}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4 mb-6">
          <h3 className="font-medium text-gray-900 mb-4">切片配置</h3>
          <div className="flex gap-4 items-end">
            <div>
              <label className="block text-sm text-gray-600 mb-1">分隔符</label>
              <input
                type="text"
                value={separator}
                onChange={e => setSeparator(e.target.value)}
                className="px-3 py-2 border rounded-lg w-32"
                placeholder="##"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">最大长度(字)</label>
              <input
                type="number"
                value={maxChunkLength}
                onChange={e => setMaxChunkLength(Number(e.target.value))}
                className="px-3 py-2 border rounded-lg w-32"
                min={100}
                max={2000}
              />
            </div>
            <button
              onClick={handleRechunk}
              disabled={loading}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
              重新切片
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4 mb-6">
          <h3 className="font-medium text-gray-900 mb-4">知识库来源</h3>
          <div className="grid grid-cols-2 gap-4">
            {/* 上传文档 */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
              <input
                type="file"
                onChange={handleUpload}
                accept=".txt,.md,.docx,.pdf"
                className="hidden"
                id="file-upload"
                disabled={uploading}
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Upload className="mx-auto h-10 w-10 text-gray-400 mb-2" />
                <p className="text-sm text-gray-600 font-medium">上传文档</p>
                <p className="text-xs text-gray-500 mt-1">txt/md/docx/pdf</p>
              </label>
            </div>
            
            {/* 使用评委手册 */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-green-400 transition-colors">
              <button 
                onClick={handleUseHandbook}
                disabled={loading}
                className="w-full h-full flex flex-col items-center justify-center"
              >
                <BookOpen className="mx-auto h-10 w-10 text-gray-400 mb-2" />
                <p className="text-sm text-gray-600 font-medium">使用评委手册</p>
                <p className="text-xs text-gray-500 mt-1">自动导入已生成的评委手册</p>
              </button>
            </div>
          </div>
          
          {knowledgeBase?.source_documents?.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">已添加的知识库</h4>
              <div className="space-y-2">
                {knowledgeBase.source_documents.map((doc: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      {doc.source === 'handbook' ? (
                        <BookOpen size={16} className="text-green-500" />
                      ) : (
                        <FileText size={16} className="text-gray-500" />
                      )}
                      <span className="text-sm">{doc.name}</span>
                      {doc.source === 'handbook' && (
                        <span className="text-xs text-green-600">(评委手册)</span>
                      )}
                    </div>
                    <button onClick={handleDelete} className="p-1 text-red-500 hover:bg-red-50 rounded">
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-gray-900">切片结果 ({knowledgeBase?.chunks?.length || 0} 个)</h3>
            <button
              onClick={handleAddChunk}
              className="px-3 py-1.5 bg-green-600 text-white rounded-lg flex items-center gap-1 text-sm hover:bg-green-700"
            >
              <Plus size={14} />
              新增切片
            </button>
          </div>
          
          {loading ? (
            <div className="text-center py-8 text-gray-500">加载中...</div>
          ) : knowledgeBase?.chunks?.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无切片，请上传文档</div>
          ) : (
            <div className="space-y-4">
              {knowledgeBase?.chunks?.map((chunk: any) => (
                <div key={chunk.id} className="border rounded-lg p-4">
                  {editingChunk === chunk.id ? (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">标题</label>
                        <input
                          type="text"
                          value={editForm.title}
                          onChange={e => setEditForm({...editForm, title: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">内容</label>
                        <textarea
                          value={editForm.content}
                          onChange={e => setEditForm({...editForm, content: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg min-h-[100px]"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">关键词 (逗号分隔)</label>
                        <input
                          type="text"
                          value={editForm.keywords}
                          onChange={e => setEditForm({...editForm, keywords: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg"
                          placeholder="关键词1, 关键词2, 关键词3"
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleSaveChunk(chunk.id)}
                          className="px-3 py-1.5 bg-blue-600 text-white rounded-lg flex items-center gap-1 text-sm"
                        >
                          <Save size={14} />
                          保存
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg flex items-center gap-1 text-sm"
                        >
                          <X size={14} />
                          取消
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">{chunk.title}</span>
                          <span className="text-xs text-gray-500">{chunk.content?.length || 0} 字</span>
                        </div>
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleEditChunk(chunk)}
                            className="p-1.5 text-blue-600 hover:bg-blue-50 rounded flex items-center gap-1 text-sm"
                          >
                            <Edit2 size={14} />
                            编辑
                          </button>
                          <button
                            onClick={() => handleDeleteChunk(chunk.id)}
                            className="p-1.5 text-red-600 hover:bg-red-50 rounded flex items-center gap-1 text-sm"
                          >
                            <Trash2 size={14} />
                            删除
                          </button>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 whitespace-pre-wrap line-clamp-3">
                        {chunk.content}
                      </p>
                      {chunk.keywords?.length > 0 && (
                        <div className="mt-2 flex gap-1 flex-wrap">
                          {chunk.keywords.map((kw: string, i: number) => (
                            <span key={i} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">
                              {kw}
                            </span>
                          ))}
                        </div>
                      )}
                    </>
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
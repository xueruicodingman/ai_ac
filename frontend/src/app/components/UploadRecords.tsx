import { ArrowLeft, Upload, FileSpreadsheet, CheckCircle, X } from 'lucide-react';
import { useState } from 'react';

interface UploadRecordsProps {
  onBack: () => void;
}

interface CandidateScore {
  name: string;
  scores: { [key: string]: number };
  total: number;
}

export default function UploadRecords({ onBack }: UploadRecordsProps) {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [dataPreview, setDataPreview] = useState(false);
  const [parsedData, setParsedData] = useState<CandidateScore[]>([]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setUploadedFile(e.target.files[0]);
    }
  };

  const handlePreview = () => {
    setParsedData([
      { name: '张三', scores: { '领导力': 85, '沟通协作': 90, '创新能力': 78 }, total: 253 },
      { name: '李四', scores: { '领导力': 78, '沟通协作': 82, '创新能力': 88 }, total: 248 },
      { name: '王五', scores: { '领导力': 92, '沟通协作': 85, '创新能力': 80 }, total: 257 },
    ]);
    setDataPreview(true);
  };

  const handleRemoveFile = () => {
    setUploadedFile(null);
    setDataPreview(false);
    setParsedData([]);
  };

  const handleSave = () => {
    alert('记录已保存！');
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
            <h1 className="font-semibold text-gray-900">上传测评记录</h1>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <div className="flex items-start gap-4 mb-6">
            <div className="w-12 h-12 rounded-lg bg-green-50 flex items-center justify-center text-green-600 flex-shrink-0">
              <Upload size={24} />
            </div>
            <div className="flex-1">
              <h3 className="font-medium text-gray-900 mb-2">上传文件</h3>
              <p className="text-sm text-gray-600">
                支持上传Excel、Word或PDF文件
              </p>
            </div>
          </div>

          {!uploadedFile ? (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
              <Upload className="mx-auto mb-3 text-gray-400" size={40} />
              <p className="text-sm text-gray-600 mb-2">点击或拖拽文件上传</p>
              <p className="text-xs text-gray-400 mb-4">支持 .xlsx, .xls, .docx, .pdf 格式</p>
              <input
                type="file"
                accept=".xlsx,.xls,.docx,.doc,.pdf"
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
          ) : (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileSpreadsheet className="text-blue-600" size={24} />
                  <div>
                    <p className="font-medium text-gray-900">{uploadedFile.name}</p>
                    <p className="text-xs text-gray-500">
                      {(uploadedFile.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handlePreview}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                  >
                    解析预览
                  </button>
                  <button
                    onClick={handleRemoveFile}
                    className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <X size={18} />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {dataPreview && parsedData.length > 0 && (
          <>
            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
              <h3 className="font-medium text-gray-900 mb-4">数据预览</h3>

              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">姓名</th>
                      <th className="text-center py-3 px-4 text-sm font-medium text-gray-700">领导力</th>
                      <th className="text-center py-3 px-4 text-sm font-medium text-gray-700">沟通协作</th>
                      <th className="text-center py-3 px-4 text-sm font-medium text-gray-700">创新能力</th>
                      <th className="text-center py-3 px-4 text-sm font-medium text-gray-700">总分</th>
                    </tr>
                  </thead>
                  <tbody>
                    {parsedData.map((person, index) => (
                      <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4 text-sm font-medium text-gray-900">{person.name}</td>
                        <td className="py-3 px-4 text-sm text-center text-gray-600">{person.scores['领导力']}</td>
                        <td className="py-3 px-4 text-sm text-center text-gray-600">{person.scores['沟通协作']}</td>
                        <td className="py-3 px-4 text-sm text-center text-gray-600">{person.scores['创新能力']}</td>
                        <td className="py-3 px-4 text-sm font-medium text-center text-gray-900">{person.total}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-4 flex items-center gap-2 text-sm text-green-600">
                <CheckCircle size={18} />
                <span>数据格式正确，共解析到 {parsedData.length} 条记录</span>
              </div>
            </div>

            <button
              onClick={handleSave}
              className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition-colors font-medium"
            >
              保存记录
            </button>
          </>
        )}
      </main>
    </div>
  );
}
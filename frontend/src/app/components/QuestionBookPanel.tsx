import { FileText } from "lucide-react";

interface QuestionBookPanelProps {
  content?: string;
}

export default function QuestionBookPanel({ content }: QuestionBookPanelProps) {
  if (!content) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <div className="text-center">
          <FileText size={48} className="mx-auto mb-2 opacity-50" />
          <p>暂无题本内容</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center gap-2 mb-3 pb-3 border-b border-gray-200">
          <FileText size={18} className="text-blue-600" />
          <h3 className="font-medium text-gray-900">角色扮演题本</h3>
        </div>
        <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
          {content}
        </pre>
      </div>
    </div>
  );
}

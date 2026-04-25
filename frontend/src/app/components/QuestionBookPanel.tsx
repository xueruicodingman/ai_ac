import { useState, useEffect, useRef } from "react";
import { FileText, Tag, Users, Lightbulb, MessageSquare, Briefcase, Eye, FileAnswer } from "lucide-react";

interface QuestionBookPanelProps {
  content?: string;
  userAnswer?: string;
}

interface Section {
  id: string;
  title: string;
  content: string;
}

export default function QuestionBookPanel({ content, userAnswer }: QuestionBookPanelProps) {
  const [activeTab, setActiveTab] = useState("questionnaire");
  const contentRef = useRef<HTMLDivElement>(null);

  const parseContent = () => {
    return { sections: [], toolId: "", toolName: "题本" };
  };

  const { sections, toolId, toolName } = parseContent();

  const tabs = userAnswer
    ? [
        { id: "questionnaire", label: "题本内容" },
        { id: "answer", label: "我的答案" }
      ]
    : [
        { id: "questionnaire", label: "题本内容" }
      ];

  return (
    <div className="h-full flex flex-col">
      <div className="flex border-b border-gray-200">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === tab.id
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === "questionnaire" ? <p>Questionnaire content</p> : null}
        {activeTab === "answer" && userAnswer ? <p>{userAnswer}</p> : null}
      </div>
    </div>
  );
}
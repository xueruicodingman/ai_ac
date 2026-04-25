import { useState, useEffect, useRef } from "react";
import { FileText, Tag, Users, Lightbulb, MessageSquare, Briefcase, Eye, FileAnswer } from "lucide-react";

// 统一JSON格式类型定义
interface UnifiedQuestionnaire {
  meta: {
    tool_id: string;
    tool_name: string;
    level?: string;
    duration?: number;
    generated_at?: string;
  };
  content: {
    role_info?: {
      subordinate_name?: string;
      position?: string;
      background?: string;
      personality?: string;
    };
    scenario?: string;
    competencies?: any[];
    challenge_points?: string[];
    company_info?: string;
    theory?: string;
    followup_strategy?: string;
    background?: string;
    materials?: string[];
    discussion_topic?: string;
    vision_prompt?: string;
  };
}

// 解析统一JSON格式
function parseQuestionnaire(content: string): UnifiedQuestionnaire | null {
  try {
    const parsed = JSON.parse(content);
    if (parsed.meta && parsed.content) {
      return parsed as UnifiedQuestionnaire;
    }
    // 兼容旧格式
    return null;
  } catch {
    return null;
  }
}

// 根据tool_id获取工具图标
function getToolIcon(toolId: string) {
  switch (toolId) {
    case 'beh':
      return <Lightbulb size={18} className="text-amber-600" />;
    case 'roleplay':
      return <Users size={18} className="text-purple-600" />;
    case 'lgd':
      return <MessageSquare size={18} className="text-green-600" />;
    case 'case':
      return <Briefcase size={18} className="text-blue-600" />;
    case 'vision':
      return <Eye size={18} className="text-indigo-600" />;
    default:
      return <FileText size={18} className="text-gray-600" />;
  }
}

// 根据tool_id获取工具名称
function getToolName(toolId: string, fallbackName?: string): string {
  const toolNames: Record<string, string> = {
    'beh': '行为分析题本',
    'roleplay': '角色扮演题本',
    'lgd': '小组讨论题本',
    'case': '案例分析题本',
    'vision': '愿景规划题本'
  };
  return toolNames[toolId] || fallbackName || '题本';

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

  const parseContent = (): { sections: Section[], toolId: string, toolName: string } => {
    if (!content) return { sections: [], toolId: '', toolName: '题本' };
    
    // 优先尝试解析统一JSON格式
    const unified = parseQuestionnaire(content);
    
    if (unified) {
      const { meta, content: ctx } = unified;
      const toolId = meta.tool_id || '';
      const toolName = meta.tool_name || getToolName(toolId);
      const sections: Section[] = [];
      
      // 根据不同工具类型提取不同内容
      switch (toolId) {
        case 'beh':
          // 行为分析题本：显示理论要点、追问策略、能力模型
          if (ctx.theory) {
            sections.push({
              id: "theory",
              title: "理论要点",
              content: ctx.theory
            });
          }
          if (ctx.followup_strategy) {
            sections.push({
              id: "followup",
              title: "追问策略",
              content: ctx.followup_strategy
            });
          }
          if (ctx.competencies && ctx.competencies.length > 0) {
            sections.push({
              id: "competencies",
              title: "能力模型",
              content: ctx.competencies.map((c: any) => 
                `${c.name || c.competency_name || '能力'}: ${c.description || c.level_description || ''}`
              ).join('\n\n')
            });
          }
          break;
          
        case 'roleplay':
          // 角色扮演题本：显示角色信息、场景、考察重点
          if (ctx.role_info) {
            const { role_info } = ctx;
            sections.push({
              id: "role",
              title: "角色设定",
              content: `姓名：${role_info.subordinate_name || '未设置'}
职位：${role_info.position || '未设置'}
背景：${role_info.background || '未设置'}
性格：${role_info.personality || '未设置'}`
            });
          }
          if (ctx.scenario) {
            sections.push({
              id: "scenario",
              title: "场景说明",
              content: ctx.scenario
            });
          }
          if (ctx.challenge_points && ctx.challenge_points.length > 0) {
            sections.push({
              id: "challenge",
              title: "考察重点",
              content: ctx.challenge_points.join('、')
            });
          }
          if (ctx.company_info) {
            sections.push({
              id: "company",
              title: "公司信息",
              content: ctx.company_info
            });
          }
          break;
          
        case 'lgd':
          // 小组讨论题本：显示场景、讨论话题
          if (ctx.scenario) {
            sections.push({
              id: "scenario",
              title: "背景场景",
              content: ctx.scenario
            });
          }
          if (ctx.discussion_topic) {
            sections.push({
              id: "topic",
              title: "讨论话题",
              content: ctx.discussion_topic
            });
          }
          if (ctx.challenge_points && ctx.challenge_points.length > 0) {
            sections.push({
              id: "challenge",
              title: "考察重点",
              content: ctx.challenge_points.join('、')
            });
          }
          break;
          
        case 'case':
          // 案例分析题本：显示案例背景、相关材料
          if (ctx.scenario || ctx.background) {
            sections.push({
              id: "case",
              title: "案例背景",
              content: ctx.scenario || ctx.background
            });
          }
          if (ctx.materials && ctx.materials.length > 0) {
            sections.push({
              id: "materials",
              title: "相关材料",
              content: ctx.materials.join('\n\n')
            });
          }
          if (ctx.challenge_points && ctx.challenge_points.length > 0) {
            sections.push({
              id: "challenge",
              title: "考察重点",
              content: ctx.challenge_points.join('、')
            });
          }
          break;
          
        case 'vision':
          // 愿景规划题本：显示场景、愿景提示
          if (ctx.scenario) {
            sections.push({
              id: "scenario",
              title: "场景背景",
              content: ctx.scenario
            });
          }
          if (ctx.vision_prompt) {
            sections.push({
              id: "vision",
              title: "愿景提示",
              content: ctx.vision_prompt
            });
          }
          if (ctx.challenge_points && ctx.challenge_points.length > 0) {
            sections.push({
              id: "challenge",
              title: "考察重点",
              content: ctx.challenge_points.join('、')
            });
          }
          break;
          
        default:
          // 其他类型，显示所有content内容
          const contentStr = JSON.stringify(ctx, null, 2);
          sections.push({
            id: "content",
            title: "完整内容",
            content: contentStr
          });
      }
      
      // 如果没有解析出任何sections，显示完整JSON
      if (sections.length === 0) {
        sections.push({
          id: "all",
          title: "完整内容",
          content: JSON.stringify(unified, null, 2)
        });
      }
      
      return { sections, toolId, toolName };
    }
    
    // 兼容旧格式解析
    const sections: Section[] = [];
    
    try {
      const data = typeof content === 'string' ? JSON.parse(content) : content;
      
      if (data.role_play_content) {
        const rc = data.role_play_content;
        if (rc.role_info) {
          sections.push({
            id: "role",
            title: "角色设定",
            content: `姓名：${rc.role_info.subordinate_name || '未设置'}
职位：${rc.role_info.position || '未设置'}
背景：${rc.role_info.background || '未设置'}
性格：${rc.role_info.personality || '未设置'}`
          });
        }
        if (rc.scenario) {
          sections.push({
            id: "scenario",
            title: "场景说明",
            content: rc.scenario
          });
        }
      }
      
      if (data.challenge_points && Array.isArray(data.challenge_points)) {
        sections.push({
          id: "challenge",
          title: "考察重点",
          content: data.challenge_points.join('、')
        });
      }
      
      if (data.company_info) {
        sections.push({
          id: "company",
          title: "公司信息",
          content: data.company_info
        });
      }
      
      if (sections.length === 0 && content) {
        sections.push({
          id: "all",
          title: "完整内容",
          content: typeof content === 'string' ? content : JSON.stringify(content, null, 2)
        });
      }
      
      return { sections, toolId: '', toolName: '题本' };
    } catch {
      return {
        sections: [{
          id: "all",
          title: "完整内容",
          content: content as string
        }],
        toolId: '',
        toolName: '题本'
      };
    }
  };

  const { sections, toolId, toolName } = parseContent();
  
  // Determine tabs based on userAnswer prop
  const tabs = userAnswer
    ? [
        { id: "questionnaire", label: "题本内容" },
        { id: "answer", label: "我的答案" }
      ]
    : [
        { id: "questionnaire", label: "题本内容" },
        ...sections.map(s => ({ id: s.id, label: s.title }))
      ];

  const scrollToSection = (sectionId: string) => {
    setActiveTab(sectionId);
    if (sectionId === "questionnaire") {
      contentRef.current?.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    
    const element = document.getElementById(`section-${sectionId}`);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

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
    <div className="h-full flex flex-col bg-white rounded-lg border border-gray-200">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200">
        {getToolIcon(toolId)}
        <h3 className="font-medium text-gray-900">{toolName}</h3>
      </div>
      
      <div className="flex gap-1 px-4 py-2 border-b border-gray-200 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => scrollToSection(tab.id)}
            className={`px-3 py-1 text-sm rounded-md whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? "bg-blue-100 text-blue-700"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div ref={contentRef} className="flex-1 overflow-y-auto p-4">
        {activeTab === "questionnaire" ? (
          <div className="space-y-4">
            {sections.map((section) => (
              <div key={section.id} id={`section-${section.id}`} className="scroll-mt-4">
                <div className="flex items-center gap-2 mb-2">
                  <Tag size={14} className="text-blue-600" />
                  <h4 className="font-medium text-gray-800">{section.title}</h4>
                </div>
                <pre className="whitespace-pre-wrap text-sm text-gray-600 font-sans bg-gray-50 p-3 rounded-md">
                  {section.content}
                </pre>
              </div>
            ))}
          </div>
        ) : activeTab === "answer" && userAnswer ? (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <FileAnswer size={14} className="text-green-600" />
              <h4 className="font-medium text-gray-800">我的答案</h4>
            </div>
            <pre className="whitespace-pre-wrap text-sm text-gray-600 font-sans bg-green-50 p-3 rounded-md border border-green-200">
              {userAnswer}
            </pre>
          </div>
        ) : (
          sections
            .filter((s) => s.id === activeTab)
            .map((section) => (
              <div key={section.id}>
                <div className="flex items-center gap-2 mb-2">
                  <Tag size={14} className="text-blue-600" />
                  <h4 className="font-medium text-gray-800">{section.title}</h4>
                </div>
                <pre className="whitespace-pre-wrap text-sm text-gray-600 font-sans bg-gray-50 p-3 rounded-md">
                  {section.content}
                </pre>
              </div>
            ))
        )}
      </div>
    </div>
  );
}
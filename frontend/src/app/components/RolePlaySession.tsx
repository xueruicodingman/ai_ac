import { useState, useEffect, useRef } from "react";
import { ArrowLeft, User, Clock, XCircle, Loader2 } from "lucide-react";
import {
  startRolePlayPractice,
  submitRolePlayAnswer,
  submitRolePlayAnswerStream,
  getRolePlaySessionStatus,
} from "../api";
import ChatPanel from "./ChatPanel";
import QuestionBookPanel from "./QuestionBookPanel";
import Timer from "./Timer";

interface RolePlaySessionProps {
  onBack: () => void;
  username?: string;
}

interface Message {
  role: "ai" | "user";
  content: string;
  timestamp?: string;
}

export default function RolePlaySession({
  onBack,
  username = "考生",
}: RolePlaySessionProps) {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [timeLimit, setTimeLimit] = useState(45 * 60);
  const [questionBookContent, setQuestionBookContent] = useState<string>("");
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    initPractice();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const initPractice = async () => {
    try {
      setIsLoading(true);
      const result = await startRolePlayPractice();
      setSessionId(result.session_id);
      setTimeLimit(result.time_limit * 60);
      setQuestionBookContent(result.question_book_content || "");

      setMessages([
        {
          role: "ai",
          content: result.welcome_message || "您好，我是您的角色扮演练习对手。让我们开始吧！",
        },
      ]);
    } catch (error) {
      console.error("开始练习失败:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async (content: string) => {
    if (!sessionId || isLoading) return;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setMessages((prev) => [...prev, { role: "user", content }]);

    const aiMessage: Message = { role: "ai", content: "" };
    setMessages((prev) => [...prev, aiMessage]);

    try {
      setIsLoading(true);
      
      await submitRolePlayAnswerStream(
        sessionId,
        content,
        (chunk: string, done: boolean) => {
          if (done) {
            if (chunk.includes("练习已结束") || chunk.includes("时间到")) {
              setIsCompleted(true);
            }
          } else {
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastMsg = newMessages[newMessages.length - 1];
              if (lastMsg && lastMsg.role === "ai") {
                lastMsg.content += chunk;
              }
              return newMessages;
            });
          }
        },
        abortControllerRef.current.signal
      );
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }
      console.error("提交回答失败:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEndPractice = () => {
    if (confirm("确定要结束练习吗？")) {
      setIsCompleted(true);
    }
  };

  const handleTimeUp = () => {
    setIsCompleted(true);
    setMessages((prev) => [
      ...prev,
      {
        role: "ai",
        content: "时间到！练习已结束。",
      },
    ]);
  };

  if (isLoading && !sessionId) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">正在初始化练习...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={onBack}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft size={20} />
              </button>
              <div className="flex items-center gap-2">
                <User size={18} className="text-gray-500" />
                <span className="font-medium text-gray-900">{username}</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Timer seconds={timeLimit} onTimeUp={handleTimeUp} />
              <button
                onClick={handleEndPractice}
                disabled={isCompleted}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                <XCircle size={18} />
                结束练习
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-180px)]">
          <div className="h-full">
            <ChatPanel
              messages={messages}
              onSend={handleSend}
              isLoading={isLoading}
              disabled={isCompleted}
            />
          </div>
          <div className="h-full">
            <QuestionBookPanel content={questionBookContent} />
          </div>
        </div>
      </main>
    </div>
  );
}

import { useState, useEffect, useRef } from "react";
import { ArrowLeft, Mic, MicOff, Send, Loader2 } from "lucide-react";
import {
  startPractice,
  submitAnswer,
  getSessionStatus,
  getSessionHistory,
} from "../api";

interface PracticeSessionProps {
  onBack: () => void;
  toolId?: string;
}

interface Message {
  role: "ai" | "user";
  content: string;
  timestamp?: string;
}

export default function PracticeSession({
  onBack,
  toolId = "beh",
}: PracticeSessionProps) {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [currentCompetency, setCurrentCompetency] = useState("");
  const [isCompleted, setIsCompleted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    initPractice();
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const initPractice = async () => {
    try {
      setIsLoading(true);
      const result = await startPractice(toolId);
      setSessionId(result.session_id);
      setProgress(result.progress);
      setCurrentCompetency(result.current_competency.name);
      setMessages([
        {
          role: "ai",
          content: result.current_competency.question,
        },
      ]);
    } catch (error) {
      console.error("开始练习失败:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async () => {
    if (!inputText.trim() || !sessionId || isLoading) return;

    const userMessage = inputText.trim();
    setInputText("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      setIsLoading(true);
      const result = await submitAnswer(sessionId, userMessage);

      setProgress(result.progress);

      if (result.ai_message.type === "question") {
        setMessages((prev) => [
          ...prev,
          { role: "ai", content: result.ai_message.content },
        ]);
      } else if (result.ai_message.type === "transition") {
        setCurrentCompetency((prev) => {
          const next = result.ai_message.content.match(/【(.+?)】/)?.[1] || prev;
          return next;
        });
        setMessages((prev) => [
          ...prev,
          { role: "ai", content: result.ai_message.content },
        ]);
      } else if (result.ai_message.type === "completion") {
        setMessages((prev) => [
          ...prev,
          { role: "ai", content: result.ai_message.content },
        ]);
        setIsCompleted(true);
      }
    } catch (error) {
      console.error("提交回答失败:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleVoice = () => {
    if (isRecording) {
      recognitionRef.current?.stop();
      setIsRecording(false);
      return;
    }

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("您的浏览器不支持语音识别");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "zh-CN";
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => setIsRecording(true);

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInputText(transcript);
    };

    recognition.onerror = () => setIsRecording(false);
    recognition.onend = () => setIsRecording(false);

    recognition.start();
    recognitionRef.current = recognition;
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
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
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={onBack}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft size={20} />
              </button>
              <div>
                <h1 className="font-semibold text-gray-900">BEI行为事件访谈</h1>
                <p className="text-sm text-gray-500">
                  {currentCompetency} · {progress.current}/{progress.total}
                </p>
              </div>
            </div>
          </div>
          <div className="mt-2 h-1 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-300"
              style={{ width: `${(progress.current / progress.total) * 100}%` }}
            />
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm min-h-[500px] flex flex-col">
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-900"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg px-4 py-2">
                  <Loader2 className="w-5 h-5 animate-spin text-gray-500" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="border-t border-gray-200 p-4">
            <div className="flex items-end gap-2">
              <div className="flex-1">
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="请输入您的回答..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  rows={2}
                  disabled={isCompleted}
                />
              </div>
              <button
                onClick={toggleVoice}
                className={`p-3 rounded-lg transition-colors ${
                  isRecording
                    ? "bg-red-100 text-red-600"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
                disabled={isCompleted}
              >
                {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
              </button>
              <button
                onClick={handleSend}
                disabled={!inputText.trim() || isLoading || isCompleted}
                className="p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

import { useState, useEffect, useRef, useCallback } from "react";
import { ArrowLeft, User, Clock, Play, Pause, XCircle, Loader2, FileText } from "lucide-react";
import {
  startVisionPractice,
  submitVisionAnswerStream,
  submitVisionFollowupStream,
  endVisionPracticeSession,
} from "../api";
import ChatPanel from "./ChatPanel";
import QuestionBookPanel from "./QuestionBookPanel";

interface VisionPracticeSessionProps {
  onBack: () => void;
  questionnaireContent: string;
  username?: string;
}

interface Message {
  role: "ai" | "user";
  content: string;
  timestamp?: string;
}

type PracticePhase = "preparing" | "running" | "ai_interaction" | "completed";

export default function VisionPracticeSession({
  onBack,
  questionnaireContent,
  username = "考生",
}: VisionPracticeSessionProps) {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [phase, setPhase] = useState<PracticePhase>("preparing");
  const [userAnswer, setUserAnswer] = useState("");
  const [userAnswerLocked, setUserAnswerLocked] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [timeLimit, setTimeLimit] = useState(30 * 60);
  const [timeLeft, setTimeLeft] = useState(timeLimit);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Initialize practice
  useEffect(() => {
    initPractice();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Timer effect
  useEffect(() => {
    if (phase !== "running" || isPaused || isCompleted || timeLeft <= 0) {
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          handleTimeUp();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [phase, isPaused, isCompleted, timeLeft]);

  const initPractice = async () => {
    try {
      setIsLoading(true);
      const result = await startVisionPractice({
        questionnaire_content: questionnaireContent,
        duration: 30,
      });
      setSessionId(result.session_id);
      setTimeLimit(result.remaining_time);
      setTimeLeft(result.remaining_time);
    } catch (error) {
      console.error("开始练习失败:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStart = () => {
    if (phase === "preparing") {
      setPhase("running");
    } else if (phase === "ai_interaction") {
      setIsPaused(false);
    }
  };

  const handlePause = () => {
    if (phase === "running") {
      setIsPaused(true);
    } else if (phase === "ai_interaction") {
      setIsPaused(true);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!sessionId || !userAnswer.trim() || userAnswerLocked) return;

    // Lock the answer
    setUserAnswerLocked(true);

    // Transition to AI interaction phase
    setPhase("ai_interaction");

    // Send to backend
    try {
      setIsLoading(true);

      // Add initial AI message
      setMessages([
        {
          role: "ai",
          content: "感谢提交您的个人愿景答案。让我分析一下您的回答，准备进行追问...",
        },
      ]);

      // Call submitVisionAnswer with stream
      await submitVisionAnswerStream(
        sessionId,
        userAnswer,
        (chunk: string, done: boolean) => {
          if (done) {
            if (chunk.includes("练习已结束") || chunk.includes("追问完成")) {
              setIsCompleted(true);
              setPhase("completed");
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
        abortControllerRef.current?.signal || new AbortController().signal
      );
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        return;
      }
      console.error("提交回答失败:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendFollowup = async (content: string) => {
    if (!sessionId || isLoading || isCompleted) return;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setMessages((prev) => [...prev, { role: "user", content }]);

    const aiMessage: Message = { role: "ai", content: "" };
    setMessages((prev) => [...prev, aiMessage]);

    try {
      setIsLoading(true);

      await submitVisionFollowupStream(
        sessionId,
        content,
        (chunk: string, done: boolean) => {
          if (done) {
            if (chunk.includes("练习已结束") || chunk.includes("追问完成")) {
              setIsCompleted(true);
              setPhase("completed");
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
        abortControllerRef.current!.signal
      );
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        return;
      }
      console.error("提交追问回答失败:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const endPractice = async () => {
    if (confirm("确定要结束练习吗？")) {
      if (sessionId) {
        try {
          await endVisionPracticeSession(sessionId);
        } catch (error) {
          console.error("结束会话失败:", error);
        }
      }
      setIsCompleted(true);
      setPhase("completed");
    }
  };

  const handleTimeUp = useCallback(() => {
    if (phase === "running") {
      // Auto submit current answer if time is up
      if (userAnswer.trim() && !userAnswerLocked) {
        handleSubmitAnswer();
      } else {
        setIsCompleted(true);
        setPhase("completed");
      }
    } else if (phase === "ai_interaction") {
      endPractice();
    }
  }, [phase, userAnswer, userAnswerLocked]);

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

  // Calculate formatted time
  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = secs % 60;
    return `${mins.toString().padStart(2, "0")}:${remainingSecs.toString().padStart(2, "0")}`;
  };

  const isWarning = timeLeft <= 60;
  const isDanger = timeLeft <= 30;

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

            <div className="flex items-center gap-2">
              <div
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
                  isDanger
                    ? "bg-red-100 text-red-700"
                    : isWarning
                    ? "bg-yellow-100 text-yellow-700"
                    : "bg-gray-100 text-gray-700"
                }`}
              >
                <Clock size={16} />
                <span className="font-mono font-medium">{formatTime(timeLeft)}</span>
              </div>

              {!isCompleted && (
                <>
                  {phase === "preparing" ? (
                    <button
                      onClick={handleStart}
                      className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                    >
                      <Play size={18} />
                      开始练习
                    </button>
                  ) : isPaused ? (
                    <button
                      onClick={handleStart}
                      className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                    >
                      <Play size={18} />
                      继续
                    </button>
                  ) : (
                    <button
                      onClick={handlePause}
                      className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors"
                    >
                      <Pause size={18} />
                      暂停
                    </button>
                  )}

                  <button
                    onClick={endPractice}
                    className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <XCircle size={18} />
                    结束练习
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-180px)]">
          {/* Left panel: Question Book */}
          <div className="h-full overflow-hidden">
            <QuestionBookPanel
              content={questionnaireContent}
              userAnswer={userAnswerLocked ? userAnswer : undefined}
            />
          </div>

          {/* Right panel: Answer input (Phase 1) or Chat (Phase 2) */}
          <div className="h-full">
            {phase === "running" ? (
              <div className="h-full flex flex-col bg-white rounded-lg border border-gray-200">
                <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200">
                  <FileText size={18} className="text-blue-600" />
                  <h3 className="font-medium text-gray-900">作答区</h3>
                  <span className="text-sm text-gray-500 ml-auto">
                    请输入您的个人愿景规划
                  </span>
                </div>

                <div className="flex-1 p-4 overflow-y-auto">
                  <textarea
                    value={userAnswer}
                    onChange={(e) => setUserAnswer(e.target.value)}
                    placeholder="请在此输入您的个人愿景规划，包括：
1. 您的长期职业目标
2. 实现目标的关键路径
3. 面临的挑战及应对策略
..."
                    className="w-full h-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none text-sm leading-relaxed"
                    disabled={userAnswerLocked || isPaused}
                  />
                </div>

                <div className="border-t border-gray-200 p-4">
                  <div className="flex justify-end gap-3">
                    <button
                      onClick={endPractice}
                      className="px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
                    >
                      放弃
                    </button>
                    <button
                      onClick={handleSubmitAnswer}
                      disabled={!userAnswer.trim() || userAnswerLocked || isPaused}
                      className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                      {userAnswerLocked ? "已提交" : "提交答案"}
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <ChatPanel
                messages={messages}
                onSend={handleSendFollowup}
                isLoading={isLoading}
                disabled={isCompleted}
              />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
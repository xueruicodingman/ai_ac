import { useState, useEffect, useRef } from "react";

interface TimerProps {
  seconds: number;
  onTimeUp?: () => void;
}

export default function Timer({ seconds, onTimeUp }: TimerProps) {
  const [timeLeft, setTimeLeft] = useState(seconds);
  const onTimeUpRef = useRef(onTimeUp);

  useEffect(() => {
    onTimeUpRef.current = onTimeUp;
  }, [onTimeUp]);

  useEffect(() => {
    setTimeLeft(seconds);
  }, [seconds]);

  useEffect(() => {
    if (timeLeft <= 0) {
      onTimeUpRef.current?.();
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft]);

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = secs % 60;
    return `${mins.toString().padStart(2, "0")}:${remainingSecs.toString().padStart(2, "0")}`;
  };

  const isWarning = timeLeft <= 60;
  const isDanger = timeLeft <= 30;

  return (
    <div
      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
        isDanger
          ? "bg-red-100 text-red-700"
          : isWarning
          ? "bg-yellow-100 text-yellow-700"
          : "bg-gray-100 text-gray-700"
      }`}
    >
      <svg
        className="w-4 h-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <span className="font-mono font-medium">{formatTime(timeLeft)}</span>
    </div>
  );
}

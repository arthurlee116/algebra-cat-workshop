"use client";

import { Fragment } from 'react';
import { useRecentQuestions } from '@/hooks/useRecentQuestions';

interface RecentQuestion {
  questionId: string;
  expressionText: string;
  createdAt: string;
}

interface RecentQuestionsProps {
  userId?: number;
  refreshKey?: number;
}

function relativeTime(createdAt: string): string {
  const now = new Date();
  const past = new Date(createdAt);
  const diffMs = now.getTime() - past.getTime();
  const diffSec = Math.floor(diffMs / 1000);

  if (diffSec < 60) return '刚刚';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}分钟前`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour}小时前`;
  const diffDay = Math.floor(diffHour / 24);
  return `${diffDay}天前`;
}

export default function RecentQuestions({ userId, refreshKey = 0 }: RecentQuestionsProps) {
  const { data, loading, error } = useRecentQuestions(userId, refreshKey);

  if (loading) {
    return (
      <div className="space-y-2">
        <div className="h-4 bg-gray-200 rounded animate-pulse" />
        <div className="h-4 bg-gray-200 rounded w-3/4 animate-pulse" />
        <div className="h-4 bg-gray-200 rounded w-1/2 animate-pulse" />
      </div>
    );
  }

  if (error || !data) {
    return <p className="text-sm text-gray-500 italic">加载最近题目失败</p>;
  }

  if (data.questions.length === 0) {
    return <p className="text-sm text-gray-500 italic">暂无最近题目</p>;
  }

  return (
    <Fragment>
      <p className="text-xs font-semibold uppercase text-gray-500 mb-3">最近题目</p>
      <ul className="space-y-2 max-h-64 overflow-y-auto">
        {data.questions.map((q: RecentQuestion) => (
          <li key={q.questionId} className="group bg-white/50 hover:bg-white rounded-xl p-3 border border-gray-100 hover:border-purple-200 transition-all duration-200">
            <code className="text-xs font-mono text-gray-900 block break-all group-hover:text-purple-700 mb-1">
              {q.expressionText}
            </code>
            <span className="text-xs text-gray-500">{relativeTime(q.createdAt)}</span>
          </li>
        ))}
      </ul>
    </Fragment>
  );
}

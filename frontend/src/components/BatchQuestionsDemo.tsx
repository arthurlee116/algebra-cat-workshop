'use client';

import React from 'react';
import { useBatchQuestions } from '../hooks/useBatchQuestions';

export default function BatchQuestionsDemo() {
  const { questions, loading, error, fetchQuestions } = useBatchQuestions();

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-bold">Batch Question Generator</h2>
      <div className="flex gap-2">
        <button
          onClick={() => fetchQuestions(5, 'basic')}
          disabled={loading}
          className="bg-blue-500 text-white px-4 py-2 rounded disabled:opacity-50"
        >
          Generate 5 Basic
        </button>
        <button
          onClick={() => fetchQuestions(5, 'advanced')}
          disabled={loading}
          className="bg-purple-500 text-white px-4 py-2 rounded disabled:opacity-50"
        >
          Generate 5 Advanced
        </button>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}

      <div className="space-y-2">
        {questions.map((q) => (
          <div key={q.questionId} className="border p-2 rounded">
            <p><strong>ID:</strong> {q.questionId}</p>
            <p><strong>Topic:</strong> {q.topic}</p>
            <p><strong>Prompt:</strong> {q.expressionText}</p>
            <p><strong>Answer:</strong> {q.solutionExpression}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

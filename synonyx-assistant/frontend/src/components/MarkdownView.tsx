import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  content: string;
}

export const MarkdownView: React.FC<Props> = ({ content }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      className="space-y-2 text-sm leading-relaxed text-slate-200"
      components={{
        h1: ({ children }) => <h1 className="text-base font-bold text-white mt-2">{children}</h1>,
        h2: ({ children }) => <h2 className="text-sm font-bold text-teal-400 mt-3">{children}</h2>,
        h3: ({ children }) => <h3 className="text-sm font-semibold text-amber-300 mt-2">{children}</h3>,
        ul: ({ children }) => <ul className="list-disc pl-5 space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-5 space-y-1">{children}</ol>,
        strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
        code: ({ children }) => (
          <code className="rounded bg-slate-800 px-1.5 py-0.5 text-xs text-amber-300">{children}</code>
        ),
        table: ({ children }) => (
          <div className="overflow-x-auto my-2 rounded-lg border border-slate-700">
            <table className="w-full text-left text-xs border-collapse">{children}</table>
          </div>
        ),
        thead: ({ children }) => <thead className="bg-slate-800 text-slate-300">{children}</thead>,
        th: ({ children }) => <th className="p-2 border-b border-slate-700 font-semibold">{children}</th>,
        td: ({ children }) => <td className="p-2 border-b border-slate-800">{children}</td>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

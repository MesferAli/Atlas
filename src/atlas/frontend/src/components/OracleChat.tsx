"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Send,
  Code,
  ChevronDown,
  ChevronUp,
  Loader2,
  Sparkles,
  TableProperties,
  Terminal,
  Copy,
  Check,
  MessageSquare,
  Bot,
  User,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { apiRequest } from "@/lib/queryClient";

interface ChatResponse {
  question: string;
  relevant_tables: Array<{
    table_name: string;
    owner: string;
    comments: string | null;
    score: number;
  }>;
  generated_sql: string;
  results: Array<Record<string, unknown>> | null;
  error: string | null;
}

interface ChatMessage {
  id: string;
  type: "user" | "assistant";
  question: string;
  response?: ChatResponse;
  timestamp: Date;
  isLoading?: boolean;
}

const EXAMPLE_QUERIES = [
  "Show me top 10 employees by salary",
  "List all active purchase orders",
  "Count employees by department",
  "Show recent HR assignments",
];

export function OracleChat() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const chatMutation = useMutation({
    mutationFn: async (q: string) => {
      const res = await apiRequest("POST", "/v1/chat", { question: q });
      return res.json() as Promise<ChatResponse>;
    },
    onSuccess: (data) => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.isLoading
            ? { ...msg, response: data, isLoading: false }
            : msg
        )
      );
    },
    onError: (error: Error, q: string) => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.isLoading
            ? {
                ...msg,
                isLoading: false,
                response: {
                  question: q,
                  relevant_tables: [],
                  generated_sql: "",
                  results: null,
                  error: error.message,
                },
              }
            : msg
        )
      );
    },
  });

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    const q = question.trim();
    if (!q || chatMutation.isPending) return;

    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        type: "user",
        question: q,
        timestamp: new Date(),
      },
      {
        id: crypto.randomUUID(),
        type: "assistant",
        question: q,
        timestamp: new Date(),
        isLoading: true,
      },
    ]);

    setQuestion("");
    chatMutation.mutate(q);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const copySQL = (sql: string, id: string) => {
    navigator.clipboard.writeText(sql);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <Card className="flex flex-col h-[calc(100vh-13rem)] border-0 shadow-lg bg-gradient-to-b from-card to-card/80">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b bg-card/50 backdrop-blur-sm">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-primary/70 shadow-sm">
          <Sparkles className="h-4 w-4 text-primary-foreground" />
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold">Oracle AI Assistant</h3>
          <p className="text-xs text-muted-foreground">
            Natural language queries — Read-only mode
          </p>
        </div>
        <Badge variant="outline" className="text-xs gap-1 border-green-500/30 text-green-600 dark:text-green-400">
          <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
          Connected
        </Badge>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 px-6" ref={scrollRef}>
        <div className="py-4 space-y-6">
          {/* Empty State */}
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 space-y-6">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 border border-primary/10">
                <MessageSquare className="h-8 w-8 text-primary/60" />
              </div>
              <div className="text-center space-y-2 max-w-md">
                <h3 className="font-semibold text-lg">Ask anything about your data</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Write your question in English or Arabic. Atlas converts it to SQL, validates it as read-only, and returns results from Oracle.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2 w-full max-w-lg">
                {EXAMPLE_QUERIES.map((q) => (
                  <button
                    key={q}
                    onClick={() => {
                      setQuestion(q);
                      inputRef.current?.focus();
                    }}
                    className="text-left text-xs px-3 py-2.5 rounded-lg border border-border/50 bg-muted/30 hover:bg-muted/60 hover:border-border text-muted-foreground hover:text-foreground transition-all duration-200"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Chat Messages */}
          {messages.map((msg) => (
            <div key={msg.id} className="space-y-1">
              {msg.type === "user" ? (
                <UserMessage question={msg.question} />
              ) : (
                <AssistantMessage
                  msg={msg}
                  copiedId={copiedId}
                  onCopySQL={copySQL}
                />
              )}
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="px-6 py-4 border-t bg-card/50 backdrop-blur-sm">
        <form onSubmit={handleSubmit} className="relative">
          <Textarea
            ref={inputRef}
            placeholder="Ask about your Oracle data... (Shift+Enter for new line)"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={chatMutation.isPending}
            className="min-h-[52px] max-h-[120px] resize-none pr-14 rounded-xl border-border/50 bg-muted/30 focus:bg-background transition-colors"
            rows={1}
          />
          <Button
            type="submit"
            size="icon"
            disabled={chatMutation.isPending || !question.trim()}
            className="absolute bottom-2 right-2 h-8 w-8 rounded-lg shadow-sm"
          >
            {chatMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-3.5 w-3.5" />
            )}
          </Button>
        </form>
      </div>
    </Card>
  );
}

function UserMessage({ question }: { question: string }) {
  return (
    <div className="flex gap-3 justify-end">
      <div className="max-w-[80%] px-4 py-2.5 rounded-2xl rounded-br-md bg-primary text-primary-foreground text-sm leading-relaxed shadow-sm">
        {question}
      </div>
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 mt-1">
        <User className="h-3.5 w-3.5 text-primary" />
      </div>
    </div>
  );
}

function AssistantMessage({
  msg,
  copiedId,
  onCopySQL,
}: {
  msg: ChatMessage;
  copiedId: string | null;
  onCopySQL: (sql: string, id: string) => void;
}) {
  const [sqlOpen, setSqlOpen] = useState(false);

  if (msg.isLoading) {
    return (
      <div className="flex gap-3">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary/20 to-primary/10 mt-1">
          <Bot className="h-3.5 w-3.5 text-primary" />
        </div>
        <div className="flex items-center gap-2 px-4 py-3 rounded-2xl rounded-bl-md bg-muted/50 border border-border/30">
          <div className="flex gap-1">
            <span className="h-2 w-2 rounded-full bg-primary/40 animate-bounce [animation-delay:0ms]" />
            <span className="h-2 w-2 rounded-full bg-primary/40 animate-bounce [animation-delay:150ms]" />
            <span className="h-2 w-2 rounded-full bg-primary/40 animate-bounce [animation-delay:300ms]" />
          </div>
          <span className="text-xs text-muted-foreground ml-1">Analyzing query...</span>
        </div>
      </div>
    );
  }

  const response = msg.response;
  if (!response) return null;

  if (response.error) {
    return (
      <div className="flex gap-3">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-destructive/10 mt-1">
          <Bot className="h-3.5 w-3.5 text-destructive" />
        </div>
        <div className="max-w-[85%] px-4 py-3 rounded-2xl rounded-bl-md bg-destructive/5 border border-destructive/20 text-sm text-destructive">
          {response.error}
        </div>
      </div>
    );
  }

  const resultColumns = response.results?.[0]
    ? Object.keys(response.results[0])
    : [];

  return (
    <div className="flex gap-3">
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary/20 to-primary/10 mt-1">
        <Bot className="h-3.5 w-3.5 text-primary" />
      </div>
      <div className="flex-1 space-y-3 max-w-[85%]">
        {/* Tables Used */}
        {response.relevant_tables.length > 0 && (
          <div className="flex items-start gap-2">
            <TableProperties className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" />
            <div className="flex flex-wrap gap-1.5">
              {response.relevant_tables.map((table) => (
                <Badge
                  key={`${table.owner}.${table.table_name}`}
                  variant="secondary"
                  className="text-[10px] font-mono px-2 py-0.5"
                >
                  {table.table_name}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* SQL Block */}
        <Collapsible open={sqlOpen} onOpenChange={setSqlOpen}>
          <CollapsibleTrigger asChild>
            <button className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors group">
              <Terminal className="h-3 w-3" />
              <span className="group-hover:underline">Generated SQL</span>
              {sqlOpen ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
            </button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="relative mt-2 rounded-lg bg-zinc-950 dark:bg-zinc-900 border border-border/30 overflow-hidden">
              <div className="flex items-center justify-between px-3 py-1.5 bg-zinc-900 dark:bg-zinc-800/50 border-b border-border/20">
                <span className="text-[10px] font-mono text-zinc-500">SQL</span>
                <button
                  onClick={() => onCopySQL(response.generated_sql, msg.id)}
                  className="flex items-center gap-1 text-[10px] text-zinc-500 hover:text-zinc-300 transition-colors"
                >
                  {copiedId === msg.id ? (
                    <>
                      <Check className="h-3 w-3" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3" />
                      Copy
                    </>
                  )}
                </button>
              </div>
              <pre className="p-3 text-xs text-emerald-400 font-mono overflow-x-auto leading-relaxed">
                <code>{response.generated_sql}</code>
              </pre>
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Results Table */}
        {response.results && response.results.length > 0 && (
          <div className="rounded-lg border border-border/30 overflow-hidden shadow-sm">
            <div className="px-3 py-1.5 bg-muted/30 border-b border-border/20 flex items-center justify-between">
              <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                Results
              </span>
              <span className="text-[10px] text-muted-foreground font-mono">
                {response.results.length} row{response.results.length !== 1 ? "s" : ""}
              </span>
            </div>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/20 hover:bg-muted/20">
                    {resultColumns.map((col) => (
                      <TableHead
                        key={col}
                        className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground h-8 px-3"
                      >
                        {col}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {response.results.map((row, idx) => (
                    <TableRow key={idx} className="hover:bg-muted/30">
                      {resultColumns.map((col) => (
                        <TableCell
                          key={col}
                          className="text-xs py-2 px-3 font-mono"
                        >
                          {String(row[col] ?? "\u2014")}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        )}

        {/* No Results */}
        {response.results && response.results.length === 0 && (
          <div className="text-xs text-muted-foreground px-3 py-2 rounded-lg bg-muted/30 border border-border/20">
            Query executed successfully — no rows returned
          </div>
        )}
      </div>
    </div>
  );
}

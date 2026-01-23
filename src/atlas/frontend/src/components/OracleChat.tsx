"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Send, Database, Code, ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
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

export function OracleChat() {
  const [question, setQuestion] = useState("");
  const [sqlOpen, setSqlOpen] = useState(false);
  const [response, setResponse] = useState<ChatResponse | null>(null);

  const chatMutation = useMutation({
    mutationFn: async (question: string) => {
      const res = await apiRequest("POST", "/v1/chat", { question });
      return res.json() as Promise<ChatResponse>;
    },
    onSuccess: (data) => {
      setResponse(data);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim()) {
      chatMutation.mutate(question);
    }
  };

  const resultColumns = response?.results?.[0]
    ? Object.keys(response.results[0])
    : [];

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="h-5 w-5" />
          Oracle Chat
        </CardTitle>
        <CardDescription>
          Ask questions about your Oracle database in natural language
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Query Input */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            placeholder="e.g., Show me top 5 customers by purchases"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={chatMutation.isPending}
            className="flex-1"
          />
          <Button type="submit" disabled={chatMutation.isPending || !question.trim()}>
            {chatMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>

        {/* Error Display */}
        {(chatMutation.isError || response?.error) && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {chatMutation.error?.message || response?.error}
          </div>
        )}

        {/* Response Section */}
        {response && !response.error && (
          <div className="space-y-4">
            {/* Relevant Tables */}
            {response.relevant_tables.length > 0 && (
              <div className="flex flex-wrap gap-2">
                <span className="text-sm text-muted-foreground">Tables used:</span>
                {response.relevant_tables.map((table) => (
                  <Badge key={`${table.owner}.${table.table_name}`} variant="secondary">
                    {table.owner}.{table.table_name}
                  </Badge>
                ))}
              </div>
            )}

            {/* Generated SQL (Collapsible) */}
            <Collapsible open={sqlOpen} onOpenChange={setSqlOpen}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="flex items-center gap-2">
                  <Code className="h-4 w-4" />
                  Generated SQL
                  {sqlOpen ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <pre className="mt-2 rounded-md bg-muted p-4 text-sm overflow-x-auto">
                  <code>{response.generated_sql}</code>
                </pre>
              </CollapsibleContent>
            </Collapsible>

            {/* Results Table */}
            {response.results && response.results.length > 0 && (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      {resultColumns.map((col) => (
                        <TableHead key={col}>{col}</TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {response.results.map((row, idx) => (
                      <TableRow key={idx}>
                        {resultColumns.map((col) => (
                          <TableCell key={col}>
                            {String(row[col] ?? "")}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}

            {/* No Results */}
            {response.results && response.results.length === 0 && (
              <div className="text-center text-sm text-muted-foreground py-4">
                No results returned
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!response && !chatMutation.isPending && (
          <div className="text-center text-sm text-muted-foreground py-8">
            Ask a question to query your Oracle database
          </div>
        )}
      </CardContent>
    </Card>
  );
}

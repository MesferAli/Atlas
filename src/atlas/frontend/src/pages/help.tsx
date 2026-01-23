import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Search,
  Book,
  Code,
  FileText,
  ExternalLink,
  MessageCircle,
  Video,
  Lightbulb,
  Shield,
  Plug,
  GitBranch,
  AlertTriangle,
} from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useState } from "react";

const docCategories = [
  {
    title: "Getting Started",
    icon: Lightbulb,
    articles: [
      { title: "What is Enterprise AI Layer?", time: "5 min read" },
      { title: "Quick Start Guide", time: "10 min read" },
      { title: "Understanding the Canonical Model", time: "8 min read" },
    ],
  },
  {
    title: "Connectors",
    icon: Plug,
    articles: [
      { title: "Configuring REST Connectors", time: "7 min read" },
      { title: "Authentication Types", time: "5 min read" },
      { title: "Health Checks & Monitoring", time: "4 min read" },
    ],
  },
  {
    title: "Mapping Studio",
    icon: GitBranch,
    articles: [
      { title: "JSONPath Basics", time: "6 min read" },
      { title: "Data Transformations", time: "8 min read" },
      { title: "Version Control & Rollback", time: "5 min read" },
    ],
  },
  {
    title: "AI Intelligence",
    icon: Lightbulb,
    articles: [
      { title: "How AI Recommendations Work", time: "10 min read" },
      { title: "Understanding Confidence Scores", time: "5 min read" },
      { title: "Anomaly Detection Explained", time: "7 min read" },
    ],
  },
  {
    title: "Governance",
    icon: Shield,
    articles: [
      { title: "Creating Policies", time: "8 min read" },
      { title: "RBAC & Permissions", time: "6 min read" },
      { title: "Audit Log Best Practices", time: "4 min read" },
    ],
  },
];

const faqs = [
  {
    question: "Can EAL automatically execute actions in my systems?",
    answer: "No. EAL follows a strict 'Human-in-the-Loop' principle. AI only generates recommendations and draft actions. All actual executions require explicit human approval. This is a core security feature that cannot be disabled.",
  },
  {
    question: "How does EAL protect my credentials?",
    answer: "All credentials are stored in an encrypted secrets vault. They are never logged or exposed in the UI. API keys are encrypted at rest and in transit. We support API Key, Bearer Token, OAuth 2.0, and custom header authentication.",
  },
  {
    question: "What is the Canonical Model?",
    answer: "The Canonical Model is a standardized data schema that normalizes data from any source system. AI operates only on canonical data, ensuring consistent analysis regardless of which ERP or inventory system you use. This makes the AI truly 'plug & play'.",
  },
  {
    question: "Can I rollback a mapping change?",
    answer: "Yes. All mappings are versioned. You can view the complete history and rollback to any previous version instantly. This ensures you can safely experiment with mapping configurations.",
  },
  {
    question: "How accurate are the AI recommendations?",
    answer: "Each recommendation includes a confidence score (0-100%). The AI also provides explainability - a human-readable explanation of why it made the recommendation. You should review recommendations with lower confidence scores more carefully.",
  },
  {
    question: "What happens if a connector goes offline?",
    answer: "EAL continuously monitors connector health. If a connection fails, you'll receive an alert. The system will automatically retry failed connections. Historical data remains available, and AI continues to work with cached data.",
  },
];

export default function Help() {
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Help & Documentation"
        description="Guides, tutorials, and support resources"
      />

      <ScrollArea className="flex-1">
        <div className="p-6 space-y-6 max-w-5xl mx-auto">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Search documentation..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 h-12 text-lg"
              data-testid="input-search-docs"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="hover-elevate cursor-pointer">
              <CardContent className="p-6 flex flex-col items-center text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary mb-4">
                  <Book className="h-6 w-6" />
                </div>
                <h3 className="font-medium mb-1">Documentation</h3>
                <p className="text-sm text-muted-foreground">Comprehensive guides and reference</p>
              </CardContent>
            </Card>
            <Card className="hover-elevate cursor-pointer">
              <CardContent className="p-6 flex flex-col items-center text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-chart-3/10 text-chart-3 mb-4">
                  <Code className="h-6 w-6" />
                </div>
                <h3 className="font-medium mb-1">API Reference</h3>
                <p className="text-sm text-muted-foreground">OpenAPI specification and examples</p>
              </CardContent>
            </Card>
            <Card className="hover-elevate cursor-pointer">
              <CardContent className="p-6 flex flex-col items-center text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-chart-2/10 text-chart-2 mb-4">
                  <MessageCircle className="h-6 w-6" />
                </div>
                <h3 className="font-medium mb-1">Support</h3>
                <p className="text-sm text-muted-foreground">Contact our support team</p>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Documentation</CardTitle>
                <CardDescription>Browse by category</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {docCategories.map((category) => (
                  <div key={category.title} className="space-y-2">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <category.icon className="h-4 w-4" />
                      <span className="text-sm font-medium">{category.title}</span>
                    </div>
                    <div className="ml-6 space-y-1">
                      {category.articles.map((article) => (
                        <a
                          key={article.title}
                          href="#"
                          className="flex items-center justify-between p-2 rounded hover:bg-muted text-sm group"
                        >
                          <span className="group-hover:text-primary transition-colors">
                            {article.title}
                          </span>
                          <span className="text-xs text-muted-foreground">{article.time}</span>
                        </a>
                      ))}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Frequently Asked Questions</CardTitle>
                <CardDescription>Common questions about EAL</CardDescription>
              </CardHeader>
              <CardContent>
                <Accordion type="single" collapsible className="w-full">
                  {faqs.map((faq, index) => (
                    <AccordionItem key={index} value={`faq-${index}`}>
                      <AccordionTrigger className="text-left text-sm">
                        {faq.question}
                      </AccordionTrigger>
                      <AccordionContent className="text-sm text-muted-foreground">
                        {faq.answer}
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Video Tutorials</CardTitle>
              <CardDescription>Watch step-by-step guides</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { title: "Onboarding Walkthrough", duration: "12:45" },
                  { title: "Creating Your First Mapping", duration: "8:30" },
                  { title: "Understanding AI Recommendations", duration: "10:15" },
                ].map((video) => (
                  <div
                    key={video.title}
                    className="relative rounded-lg bg-muted aspect-video flex items-center justify-center cursor-pointer hover-elevate"
                  >
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-background/80 text-foreground">
                      <Video className="h-5 w-5" />
                    </div>
                    <div className="absolute bottom-3 left-3 right-3">
                      <p className="text-sm font-medium">{video.title}</p>
                      <p className="text-xs text-muted-foreground">{video.duration}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-primary/5 border-primary/20">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground shrink-0">
                  <MessageCircle className="h-6 w-6" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium mb-1">Need more help?</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Our support team is available 24/7 to help with any questions about the Enterprise AI Layer.
                  </p>
                  <div className="flex gap-3">
                    <Button data-testid="button-contact-support">
                      Contact Support
                    </Button>
                    <Button variant="outline" data-testid="button-schedule-demo">
                      Schedule a Demo
                      <ExternalLink className="ml-2 h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}

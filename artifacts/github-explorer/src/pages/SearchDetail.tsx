import { useParams } from "wouter";
import { Link } from "wouter";
import { useSearch } from "@/hooks/useSearches";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, ExternalLink, MapPin, Clock, BellRing, History } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function SearchDetail() {
  const { id } = useParams<{ id: string }>();
  const { search, isLoading, pauseSearch, resumeSearch, isPausing, isResuming } = useSearch(id || "");

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-48" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (!search) {
    return <div>Search not found.</div>;
  }

  // Mock results since API shape isn't fully defined for this relation
  const results = search.results || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link href="/searches" className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors hover:bg-secondary h-9 w-9">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-3">
              {search.keyword}
              {search.status === "active" ? (
                <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-xs">Active</Badge>
              ) : (
                <Badge variant="secondary" className="text-xs">Paused</Badge>
              )}
            </h1>
            <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
              <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> {search.location || "Anywhere"}</span>
              <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> Every {search.interval_minutes}m</span>
            </div>
          </div>
        </div>
        <div>
          {search.status === "active" ? (
            <Button variant="outline" onClick={() => pauseSearch()} disabled={isPausing}>Pause</Button>
          ) : (
            <Button onClick={() => resumeSearch()} disabled={isResuming}>Resume</Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BellRing className="w-5 h-5 text-primary" />
                Latest Results
              </CardTitle>
              <CardDescription>Items found for this search.</CardDescription>
            </CardHeader>
            <CardContent>
              {results.length === 0 ? (
                <div className="py-12 text-center text-muted-foreground bg-secondary/20 rounded-lg border border-dashed border-border">
                  <p>No items found yet.</p>
                  <p className="text-sm">We'll keep looking.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {results.map((item: any, i: number) => (
                    <div key={i} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-lg border border-border bg-card hover:bg-secondary/50 transition-colors">
                      <div className="space-y-1">
                        <h4 className="font-medium text-foreground">{item.title}</h4>
                        <div className="flex items-center gap-3 text-sm text-muted-foreground">
                          <span className="font-mono text-primary font-semibold">{item.price}</span>
                          <span>•</span>
                          <span>{new Date(item.found_at).toLocaleString()}</span>
                        </div>
                      </div>
                      <a href={item.url} target="_blank" rel="noopener noreferrer" className="mt-3 sm:mt-0 inline-flex items-center text-sm text-primary hover:underline">
                        View <ExternalLink className="w-3 h-3 ml-1" />
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <History className="w-4 h-4" />
                Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div>
                <p className="text-muted-foreground mb-1">Created At</p>
                <p className="font-medium">{new Date(search.created_at || Date.now()).toLocaleDateString()}</p>
              </div>
              <div>
                <p className="text-muted-foreground mb-1">Webhook URL</p>
                <p className="font-mono text-xs break-all bg-secondary p-2 rounded border border-border">
                  {search.webhook_url || "Not configured"}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

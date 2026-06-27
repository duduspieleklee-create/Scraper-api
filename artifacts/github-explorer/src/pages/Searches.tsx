import { useSearches } from "@/hooks/useSearches";
import { Link } from "wouter";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Search, Plus, Play, Pause, Trash2, MapPin, Clock } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { motion } from "framer-motion";

function calculateTokenCost(interval: number) {
  if (interval === 1) return 5;
  if (interval === 15) return 3;
  if (interval === 60) return 2;
  return 1;
}

export default function Searches() {
  const { searches, isLoading, deleteSearch, pauseSearch, resumeSearch } = useSearches();
  const { toast } = useToast();

  const handlePause = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    try {
      await pauseSearch(id);
      toast({ title: "Search paused" });
    } catch (err) {
      toast({ title: "Error pausing search", variant: "destructive" });
    }
  };

  const handleResume = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    try {
      await resumeSearch(id);
      toast({ title: "Search resumed" });
    } catch (err) {
      toast({ title: "Error resuming search", variant: "destructive" });
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    if (!confirm("Are you sure?")) return;
    try {
      await deleteSearch(id);
      toast({ title: "Search deleted" });
    } catch (err) {
      toast({ title: "Error deleting search", variant: "destructive" });
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-[400px]" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Saved Searches</h1>
          <p className="text-muted-foreground mt-2">Manage your active monitoring tasks.</p>
        </div>
        <Link href="/searches/new" className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2" data-testid="link-new-search">
          <Plus className="w-4 h-4 mr-2" />
          New Search
        </Link>
      </div>

      {!searches?.length ? (
        <Card className="border-dashed bg-transparent">
          <CardContent className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 bg-secondary rounded-full flex items-center justify-center mb-6">
              <Search className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold">No searches yet</h3>
            <p className="text-muted-foreground mt-2 max-w-sm">
              Create your first search to start monitoring Kleinanzeigen for deals automatically.
            </p>
            <Link href="/searches/new" className="mt-6 inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2">
              <Plus className="w-4 h-4 mr-2" />
              Create Search
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {searches.map((search: any, i: number) => (
            <motion.div
              key={search.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Link href={`/searches/${search.id}`}>
                <Card className="hover:border-primary/50 transition-colors cursor-pointer group">
                  <CardContent className="p-6">
                    <div className="flex flex-col md:flex-row gap-6 md:items-center justify-between">
                      <div className="space-y-3 flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="font-semibold text-lg">{search.keyword}</h3>
                          {search.status === "active" ? (
                            <Badge variant="default" className="bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 border-emerald-500/20">Active</Badge>
                          ) : (
                            <Badge variant="secondary" className="text-slate-500">Paused</Badge>
                          )}
                        </div>
                        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                          <div className="flex items-center gap-1.5">
                            <MapPin className="w-4 h-4" />
                            {search.location || "Anywhere"}
                          </div>
                          <div className="flex items-center gap-1.5">
                            <Clock className="w-4 h-4" />
                            Every {search.interval_minutes}m
                          </div>
                          <div className="flex items-center gap-1.5 font-mono bg-secondary px-2 py-0.5 rounded text-xs border border-border">
                            {calculateTokenCost(search.interval_minutes)} tokens/find
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2" onClick={(e) => e.preventDefault()}>
                        {search.status === "active" ? (
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={(e) => handlePause(search.id, e)}
                            data-testid={`btn-pause-${search.id}`}
                          >
                            <Pause className="w-4 h-4 mr-2" /> Pause
                          </Button>
                        ) : (
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={(e) => handleResume(search.id, e)}
                            data-testid={`btn-resume-${search.id}`}
                          >
                            <Play className="w-4 h-4 mr-2" /> Resume
                          </Button>
                        )}
                        <Button 
                          variant="ghost" 
                          size="sm"
                          className="text-destructive hover:text-destructive hover:bg-destructive/10"
                          onClick={(e) => handleDelete(search.id, e)}
                          data-testid={`btn-delete-${search.id}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}

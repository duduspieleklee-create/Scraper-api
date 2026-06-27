import { useState } from "react";
import { useLocation, Link } from "wouter";
import { useSearches } from "@/hooks/useSearches";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { ArrowLeft, Save } from "lucide-react";

export default function NewSearch() {
  const [, setLocation] = useLocation();
  const { createSearch, isCreating } = useSearches();
  const { toast } = useToast();

  const [formData, setFormData] = useState({
    keyword: "",
    location: "",
    interval_minutes: "60",
    webhook_url: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createSearch({
        ...formData,
        interval_minutes: parseInt(formData.interval_minutes),
      });
      toast({ title: "Search created successfully" });
      setLocation("/searches");
    } catch (err: any) {
      toast({ 
        title: "Failed to create search", 
        description: err.message,
        variant: "destructive" 
      });
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/searches" className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors hover:bg-secondary h-9 w-9">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Create Search</h1>
          <p className="text-muted-foreground mt-1">Set up a new monitoring task.</p>
        </div>
      </div>

      <Card>
        <form onSubmit={handleSubmit}>
          <CardHeader>
            <CardTitle>Search Parameters</CardTitle>
            <CardDescription>
              Define what to look for and how often.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="keyword">Keyword *</Label>
              <Input
                id="keyword"
                placeholder="e.g. ThinkPad T14, Herman Miller Aeron"
                value={formData.keyword}
                onChange={(e) => setFormData(p => ({ ...p, keyword: e.target.value }))}
                required
                data-testid="input-keyword"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                placeholder="e.g. Berlin, 10115"
                value={formData.location}
                onChange={(e) => setFormData(p => ({ ...p, location: e.target.value }))}
                data-testid="input-location"
              />
              <p className="text-xs text-muted-foreground">Leave blank to search all of Germany.</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="interval">Check Interval *</Label>
              <Select
                value={formData.interval_minutes}
                onValueChange={(v) => setFormData(p => ({ ...p, interval_minutes: v }))}
              >
                <SelectTrigger id="interval" data-testid="select-interval">
                  <SelectValue placeholder="Select interval" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Every 1 minute (5 tokens/find)</SelectItem>
                  <SelectItem value="15">Every 15 minutes (3 tokens/find)</SelectItem>
                  <SelectItem value="60">Every 1 hour (2 tokens/find)</SelectItem>
                  <SelectItem value="180">Every 3 hours (1 token/find)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2 pt-4 border-t border-border">
              <Label htmlFor="webhook">Webhook URL (Optional)</Label>
              <Input
                id="webhook"
                type="url"
                placeholder="https://your-server.com/webhook"
                value={formData.webhook_url}
                onChange={(e) => setFormData(p => ({ ...p, webhook_url: e.target.value }))}
                data-testid="input-webhook"
              />
              <p className="text-xs text-muted-foreground">We'll POST to this URL when a new item is found.</p>
            </div>
          </CardContent>
          <CardFooter className="flex justify-end gap-4 border-t border-border pt-6 mt-2 bg-secondary/20">
            <Link href="/searches" className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors hover:bg-secondary h-10 px-4 py-2">
              Cancel
            </Link>
            <Button type="submit" disabled={isCreating} data-testid="btn-save-search">
              <Save className="w-4 h-4 mr-2" />
              {isCreating ? "Saving..." : "Create Search"}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}

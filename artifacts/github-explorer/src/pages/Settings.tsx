import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { Server } from "lucide-react";

export default function Settings() {
  const { toast } = useToast();
  const [apiUrl, setApiUrl] = useState(() => {
    return localStorage.getItem("SCRAPER_API_URL") || "http://localhost:8000";
  });

  const handleSave = () => {
    localStorage.setItem("SCRAPER_API_URL", apiUrl);
    toast({
      title: "Settings saved",
      description: "API URL has been updated. You may need to refresh to apply changes.",
    });
    // Hard refresh to re-init API client
    window.location.reload();
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Settings</h1>
        <p className="text-muted-foreground mt-2">Configure application preferences.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="w-5 h-5 text-primary" />
            API Connection
          </CardTitle>
          <CardDescription>
            Configure the backend server URL this dashboard connects to.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="apiUrl">Scraper API Base URL</Label>
            <Input
              id="apiUrl"
              type="url"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              placeholder="http://localhost:8000"
              className="font-mono text-sm"
              data-testid="input-api-url"
            />
          </div>
        </CardContent>
        <CardFooter className="border-t border-border pt-6 bg-secondary/10">
          <Button onClick={handleSave} data-testid="btn-save-settings">Save Configuration</Button>
        </CardFooter>
      </Card>
    </div>
  );
}

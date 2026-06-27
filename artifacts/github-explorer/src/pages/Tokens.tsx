import { useTokens } from "@/hooks/useTokens";
import { useAuth } from "@/hooks/useAuth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Coins, ArrowDownRight, ArrowUpRight } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export default function Tokens() {
  const { user, isLoading: userLoading } = useAuth();
  const { transactions, isLoading: tokensLoading } = useTokens();

  if (userLoading || tokensLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-48" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Tokens</h1>
        <p className="text-muted-foreground mt-2">Manage your balance and view history.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-1 bg-primary text-primary-foreground border-none overflow-hidden relative">
          <div className="absolute -right-4 -bottom-4 opacity-20 pointer-events-none">
            <Coins className="w-48 h-48" />
          </div>
          <CardHeader>
            <CardTitle className="text-primary-foreground/80 font-normal">Current Balance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-6xl font-bold font-mono tracking-tight">{user?.token_balance ?? 0}</div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Top up your balance</CardTitle>
            <CardDescription>Tokens are charged per item found based on the search interval.</CardDescription>
          </CardHeader>
          <CardContent>
            <Alert className="bg-secondary/50 border-primary/20">
              <Coins className="h-4 w-4 text-primary" />
              <AlertTitle className="text-primary font-semibold">Payment Integration</AlertTitle>
              <AlertDescription className="text-muted-foreground mt-2">
                To add tokens, send a POST request to our Stripe webhook with your user ID.
                <br /><br />
                <code className="text-xs bg-background p-2 block rounded border border-border mt-2 overflow-x-auto">
                  curl -X POST {window.location.origin}/api/webhooks/stripe \
                  <br />  -d '{"{"}"user_id": "{user?.id}", "amount": 100{"}"}'
                </code>
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Transaction History</CardTitle>
          <CardDescription>Recent token usage and top-ups.</CardDescription>
        </CardHeader>
        <CardContent>
          {!transactions?.length ? (
            <div className="py-8 text-center text-muted-foreground">
              No transactions yet.
            </div>
          ) : (
            <div className="space-y-4">
              {transactions.map((tx: any, i: number) => {
                const isPositive = tx.amount > 0;
                return (
                  <div key={i} className="flex items-center justify-between p-4 rounded-lg border border-border bg-card">
                    <div className="flex items-center gap-4">
                      <div className={`p-2 rounded-full ${isPositive ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500'}`}>
                        {isPositive ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                      </div>
                      <div>
                        <p className="font-medium">{tx.reason || (isPositive ? "Top up" : "Search result found")}</p>
                        <p className="text-xs text-muted-foreground">{new Date(tx.timestamp || Date.now()).toLocaleString()}</p>
                      </div>
                    </div>
                    <div className={`font-mono font-bold ${isPositive ? 'text-emerald-500' : 'text-rose-500'}`}>
                      {isPositive ? '+' : ''}{tx.amount}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

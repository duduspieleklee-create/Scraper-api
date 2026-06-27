import { useSearches } from "@/hooks/useSearches";
import { useAuth } from "@/hooks/useAuth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Coins, Search, Play, Pause, AlertCircle } from "lucide-react";
import { motion } from "framer-motion";

export default function Dashboard() {
  const { user, isLoading: userLoading } = useAuth();
  const { searches, isLoading: searchesLoading } = useSearches();

  if (userLoading || searchesLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  const activeCount = searches?.filter((s: any) => s.status === "active").length || 0;
  const pausedCount = searches?.filter((s: any) => s.status === "paused").length || 0;

  const stats = [
    {
      title: "Token Balance",
      value: user?.token_balance ?? 0,
      icon: Coins,
      description: "Available tokens",
      color: "text-amber-500",
      bg: "bg-amber-500/10",
    },
    {
      title: "Active Searches",
      value: activeCount,
      icon: Play,
      description: "Currently monitoring",
      color: "text-emerald-500",
      bg: "bg-emerald-500/10",
    },
    {
      title: "Paused Searches",
      value: pausedCount,
      icon: Pause,
      description: "Not consuming tokens",
      color: "text-slate-500",
      bg: "bg-slate-500/10",
    },
  ];

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Dashboard</h1>
        <p className="text-muted-foreground mt-2">Welcome back, {user?.email}</p>
      </div>

      <motion.div 
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
        variants={container}
        initial="hidden"
        animate="show"
      >
        {stats.map((stat, i) => (
          <motion.div key={i} variants={item}>
            <Card className="border-border shadow-sm overflow-hidden relative">
              <div className="absolute top-0 right-0 p-6 opacity-10 pointer-events-none">
                <stat.icon className="w-24 h-24" />
              </div>
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
                <div className={`p-2 rounded-md ${stat.bg}`}>
                  <stat.icon className={`w-4 h-4 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold font-mono tracking-tight">{stat.value}</div>
                <p className="text-xs text-muted-foreground mt-1">{stat.description}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
            <Search className="w-12 h-12 mb-4 opacity-20" />
            <p>No recent listings found.</p>
            <p className="text-sm mt-1">Make sure your searches are active.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

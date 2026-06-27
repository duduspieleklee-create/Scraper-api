import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAdminProxies } from "@/hooks/useProxies";
import { useAdminScraperUsers } from "@/hooks/useScraperUsers";
import { ServerCrash, Users, Coins, Activity, ArrowRight } from "lucide-react";
import { Link } from "wouter";
import { motion } from "framer-motion";
import { Skeleton } from "@/components/ui/skeleton";

export default function AdminDashboard() {
  const { statsQuery: { data: proxyStats, isLoading: proxiesLoading } } = useAdminProxies();
  const { listQuery: { data: users, isLoading: usersLoading } } = useAdminScraperUsers();

  const totalTokens = users?.reduce((sum, user) => sum + user.tokenBalance, 0) || 0;

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-zinc-100">Overview</h1>
        <p className="text-zinc-400 mt-2">System status and key metrics.</p>
      </div>

      <motion.div 
        variants={container}
        initial="hidden"
        animate="show"
        className="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
      >
        <motion.div variants={item}>
          <Card className="bg-[#0f0f0f] border-zinc-800 text-zinc-100 overflow-hidden relative group">
            <div className="absolute top-0 right-0 p-6 opacity-5 transition-opacity group-hover:opacity-10">
              <ServerCrash className="w-24 h-24 text-amber-500" />
            </div>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-zinc-400 uppercase tracking-wider">Proxies</CardTitle>
              <ServerCrash className="w-4 h-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              {proxiesLoading ? (
                <Skeleton className="h-10 w-24 bg-zinc-800" />
              ) : (
                <>
                  <div className="text-4xl font-bold">{proxyStats?.total || 0}</div>
                  <div className="text-xs text-zinc-500 mt-2 flex items-center gap-2">
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                      {proxyStats?.enabled || 0} enabled
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-red-500"></span>
                      {proxyStats?.disabled || 0} disabled
                    </span>
                  </div>
                </>
              )}
            </CardContent>
            <div className="px-6 pb-4 pt-2">
              <Link href="/admin/proxies" className="text-xs text-amber-500 hover:text-amber-400 font-medium flex items-center gap-1 transition-colors">
                Manage Proxies <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </Card>
        </motion.div>

        <motion.div variants={item}>
          <Card className="bg-[#0f0f0f] border-zinc-800 text-zinc-100 overflow-hidden relative group">
            <div className="absolute top-0 right-0 p-6 opacity-5 transition-opacity group-hover:opacity-10">
              <Users className="w-24 h-24 text-amber-500" />
            </div>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-zinc-400 uppercase tracking-wider">Scraper Users</CardTitle>
              <Users className="w-4 h-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              {usersLoading ? (
                <Skeleton className="h-10 w-24 bg-zinc-800" />
              ) : (
                <>
                  <div className="text-4xl font-bold">{users?.length || 0}</div>
                  <div className="text-xs text-zinc-500 mt-2">
                    Registered accounts
                  </div>
                </>
              )}
            </CardContent>
            <div className="px-6 pb-4 pt-2">
              <Link href="/admin/users" className="text-xs text-amber-500 hover:text-amber-400 font-medium flex items-center gap-1 transition-colors">
                Manage Users <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </Card>
        </motion.div>

        <motion.div variants={item}>
          <Card className="bg-[#0f0f0f] border-zinc-800 text-zinc-100 overflow-hidden relative group">
            <div className="absolute top-0 right-0 p-6 opacity-5 transition-opacity group-hover:opacity-10">
              <Coins className="w-24 h-24 text-amber-500" />
            </div>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-zinc-400 uppercase tracking-wider">Total Tokens</CardTitle>
              <Activity className="w-4 h-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              {usersLoading ? (
                <Skeleton className="h-10 w-24 bg-zinc-800" />
              ) : (
                <>
                  <div className="text-4xl font-bold font-mono">{totalTokens.toLocaleString()}</div>
                  <div className="text-xs text-zinc-500 mt-2">
                    Circulating in system
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </div>
  );
}
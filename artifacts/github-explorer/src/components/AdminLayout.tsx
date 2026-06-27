import { Link, useLocation } from "wouter";
import { 
  ShieldAlert, 
  LayoutDashboard, 
  ServerCrash, 
  Users, 
  LogOut 
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAdminMe } from "@/hooks/useAdmin";
import { motion } from "framer-motion";

export function AdminLayout({ children }: { children: React.ReactNode }) {
  const [location, setLocation] = useLocation();
  const { data: admin } = useAdminMe();

  const handleLogout = () => {
    localStorage.removeItem("admin_token");
    setLocation("/admin/login");
  };

  const navItems = [
    { href: "/admin", label: "Dashboard", icon: LayoutDashboard },
    { href: "/admin/proxies", label: "Proxies", icon: ServerCrash },
    { href: "/admin/users", label: "Users", icon: Users },
  ];

  return (
    <div className="flex min-h-[100dvh] w-full bg-[#0a0a0a] text-zinc-100 font-sans selection:bg-amber-500/30">
      {/* Sidebar */}
      <aside className="hidden md:flex w-64 flex-col border-r border-zinc-800 bg-[#0f0f0f]">
        <div className="h-16 flex items-center px-6 border-b border-zinc-800 gap-2 text-amber-500">
          <ShieldAlert className="w-5 h-5" />
          <span className="font-bold tracking-widest uppercase text-sm">Ops Center</span>
        </div>
        
        <nav className="flex-1 px-3 py-6 space-y-1">
          {navItems.map((item) => {
            const isActive = location === item.href;
            return (
              <Link 
                key={item.href} 
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-all text-sm font-medium ${
                  isActive 
                    ? "bg-amber-500/10 text-amber-500 border border-amber-500/20" 
                    : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100"
                }`}
                data-testid={`admin-nav-${item.label.toLowerCase()}`}
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-zinc-800">
          <div className="flex items-center justify-between mb-4 px-2">
            <div className="flex flex-col">
              <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Active Session</span>
              <span className="text-sm font-medium text-zinc-200">
                {admin?.username || "Admin"}
              </span>
            </div>
          </div>
          <Button 
            variant="ghost" 
            className="w-full justify-start text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800" 
            onClick={handleLogout}
            data-testid="admin-btn-logout"
          >
            <LogOut className="w-4 h-4 mr-2" />
            End Session
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 flex items-center justify-between px-6 border-b border-zinc-800 bg-[#0f0f0f]/80 backdrop-blur sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <span className="text-xs font-mono text-zinc-500 px-2 py-1 rounded bg-zinc-900 border border-zinc-800">
              SECURE_CONTEXT
            </span>
          </div>
        </header>
        <main className="flex-1 p-6 md:p-8 overflow-x-hidden">
          <motion.div
            key={location}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="max-w-6xl mx-auto h-full"
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
}
import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/ThemeProvider";

import { Layout } from "@/components/Layout";
import { ProtectedRoute } from "@/components/ProtectedRoute";

import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Searches from "@/pages/Searches";
import NewSearch from "@/pages/NewSearch";
import SearchDetail from "@/pages/SearchDetail";
import Tokens from "@/pages/Tokens";
import Settings from "@/pages/Settings";
import NotFound from "@/pages/not-found";

import AdminLogin from "@/pages/admin/AdminLogin";
import AdminDashboard from "@/pages/admin/AdminDashboard";
import ProxyManager from "@/pages/admin/ProxyManager";
import UserManager from "@/pages/admin/UserManager";
import { AdminProtectedRoute } from "@/components/AdminProtectedRoute";
import { AdminLayout } from "@/components/AdminLayout";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
});

function Router() {
  return (
    <Switch>
      <Route path="/login" component={Login} />
      
      <Route path="/">
        {() => (
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        )}
      </Route>

      <Route path="/dashboard">
        {() => (
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        )}
      </Route>

      <Route path="/searches">
        {() => (
          <ProtectedRoute>
            <Layout>
              <Searches />
            </Layout>
          </ProtectedRoute>
        )}
      </Route>

      <Route path="/searches/new">
        {() => (
          <ProtectedRoute>
            <Layout>
              <NewSearch />
            </Layout>
          </ProtectedRoute>
        )}
      </Route>

      <Route path="/searches/:id">
        {() => (
          <ProtectedRoute>
            <Layout>
              <SearchDetail />
            </Layout>
          </ProtectedRoute>
        )}
      </Route>

      <Route path="/tokens">
        {() => (
          <ProtectedRoute>
            <Layout>
              <Tokens />
            </Layout>
          </ProtectedRoute>
        )}
      </Route>

      <Route path="/settings">
        {() => (
          <ProtectedRoute>
            <Layout>
              <Settings />
            </Layout>
          </ProtectedRoute>
        )}
      </Route>

      <Route path="/admin/login" component={AdminLogin} />
      
      <Route path="/admin">
        {() => (
          <AdminProtectedRoute>
            <AdminLayout>
              <AdminDashboard />
            </AdminLayout>
          </AdminProtectedRoute>
        )}
      </Route>
      
      <Route path="/admin/proxies">
        {() => (
          <AdminProtectedRoute>
            <AdminLayout>
              <ProxyManager />
            </AdminLayout>
          </AdminProtectedRoute>
        )}
      </Route>
      
      <Route path="/admin/users">
        {() => (
          <AdminProtectedRoute>
            <AdminLayout>
              <UserManager />
            </AdminLayout>
          </AdminProtectedRoute>
        )}
      </Route>

      <Route>
        {() => (
          <Layout>
            <NotFound />
          </Layout>
        )}
      </Route>
    </Switch>
  );
}

function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
            <Router />
          </WouterRouter>
          <Toaster />
        </TooltipProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;

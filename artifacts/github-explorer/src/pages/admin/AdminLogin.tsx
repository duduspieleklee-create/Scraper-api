import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ShieldAlert, LogIn, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { useAdminLogin } from "@/hooks/useAdmin";
import { motion } from "framer-motion";

const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function AdminLogin() {
  const loginMutation = useAdminLogin();
  
  const form = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: "",
      password: "",
    },
  });

  const onSubmit = (data: LoginForm) => {
    loginMutation.mutate(data);
  };

  return (
    <div className="min-h-[100dvh] flex items-center justify-center bg-[#0a0a0a] text-zinc-100 p-4 selection:bg-amber-500/30 font-sans">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-md"
      >
        <div className="flex flex-col items-center mb-8 text-amber-500">
          <ShieldAlert className="w-12 h-12 mb-4" />
          <h1 className="text-2xl font-bold tracking-widest uppercase">Ops Center</h1>
          <p className="text-sm text-zinc-500 mt-2 tracking-wide">RESTRICTED ACCESS</p>
        </div>

        <Card className="border-zinc-800 bg-[#0f0f0f]/80 backdrop-blur shadow-2xl shadow-amber-500/5 text-zinc-100">
          <CardHeader>
            <CardTitle className="text-xl">Authenticate</CardTitle>
            <CardDescription className="text-zinc-400">
              Enter your administrative credentials.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form id="admin-login-form" onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username" className="text-zinc-300">Username</Label>
                <Input
                  id="username"
                  {...form.register("username")}
                  className="bg-zinc-900/50 border-zinc-800 focus-visible:ring-amber-500 focus-visible:border-amber-500 text-zinc-100"
                  placeholder="admin"
                  data-testid="input-username"
                  disabled={loginMutation.isPending}
                />
                {form.formState.errors.username && (
                  <p className="text-sm text-red-500">{form.formState.errors.username.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="text-zinc-300">Password</Label>
                </div>
                <Input
                  id="password"
                  type="password"
                  {...form.register("password")}
                  className="bg-zinc-900/50 border-zinc-800 focus-visible:ring-amber-500 focus-visible:border-amber-500 text-zinc-100"
                  placeholder="••••••••"
                  data-testid="input-password"
                  disabled={loginMutation.isPending}
                />
                {form.formState.errors.password && (
                  <p className="text-sm text-red-500">{form.formState.errors.password.message}</p>
                )}
              </div>
            </form>
          </CardContent>
          <CardFooter className="flex flex-col gap-4">
            <Button 
              type="submit" 
              form="admin-login-form"
              className="w-full bg-amber-600 hover:bg-amber-500 text-zinc-950 font-bold tracking-wide disabled:opacity-50 transition-colors"
              disabled={loginMutation.isPending}
              data-testid="button-submit"
            >
              {loginMutation.isPending ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <LogIn className="w-4 h-4 mr-2" />
              )}
              {loginMutation.isPending ? "Authenticating..." : "Login"}
            </Button>
            
            <div className="text-xs text-zinc-500 text-center flex items-center justify-center gap-1 border border-zinc-800/50 rounded-md p-2 bg-zinc-900/20">
              <span className="font-mono">admin</span> / <span className="font-mono">admin123</span>
            </div>
          </CardFooter>
        </Card>
      </motion.div>
    </div>
  );
}
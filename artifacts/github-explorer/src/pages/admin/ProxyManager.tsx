import { useState } from "react";
import { useAdminProxies } from "@/hooks/useProxies";
import { 
  ServerCrash, 
  Plus, 
  Trash2, 
  Power, 
  PowerOff,
  MoreVertical,
  Loader2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { motion, AnimatePresence } from "framer-motion";
import { format } from "date-fns";

const proxySchema = z.object({
  host: z.string().min(1, "Host is required"),
  port: z.coerce.number().min(1).max(65535),
  protocol: z.enum(["http", "https", "socks5"]),
  label: z.string().optional(),
  username: z.string().optional(),
  password: z.string().optional(),
  enabled: z.boolean().default(true),
});

type ProxyForm = z.infer<typeof proxySchema>;

export default function ProxyManager() {
  const { listQuery, createMutation, deleteMutation, toggleMutation } = useAdminProxies();
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [proxyToDelete, setProxyToDelete] = useState<number | null>(null);

  const form = useForm<ProxyForm>({
    resolver: zodResolver(proxySchema),
    defaultValues: {
      host: "",
      port: 8080,
      protocol: "http",
      label: "",
      username: "",
      password: "",
      enabled: true,
    },
  });

  const onSubmit = (data: ProxyForm) => {
    createMutation.mutate(
      { data },
      {
        onSuccess: () => {
          setIsAddOpen(false);
          form.reset();
        },
      }
    );
  };

  const handleDelete = () => {
    if (proxyToDelete) {
      deleteMutation.mutate({ id: proxyToDelete }, {
        onSuccess: () => setProxyToDelete(null)
      });
    }
  };

  const handleToggle = (id: number) => {
    toggleMutation.mutate({ id });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-zinc-100 flex items-center gap-3">
            <ServerCrash className="w-8 h-8 text-amber-500" />
            Proxy Fleet
          </h1>
          <p className="text-zinc-400 mt-1">Manage outbound nodes for scraper rotation.</p>
        </div>

        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogTrigger asChild>
            <Button className="bg-amber-600 hover:bg-amber-500 text-zinc-950 font-semibold" data-testid="btn-add-proxy">
              <Plus className="w-4 h-4 mr-2" />
              Add Proxy
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px] bg-[#0f0f0f] border-zinc-800 text-zinc-100">
            <DialogHeader>
              <DialogTitle>Add New Proxy</DialogTitle>
              <DialogDescription className="text-zinc-400">
                Register a new node in the proxy pool.
              </DialogDescription>
            </DialogHeader>
            <form id="add-proxy-form" onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 py-4">
              <div className="grid grid-cols-4 gap-4">
                <div className="col-span-3 space-y-2">
                  <Label htmlFor="host" className="text-zinc-300">Host / IP</Label>
                  <Input 
                    id="host" 
                    {...form.register("host")} 
                    className="bg-zinc-900/50 border-zinc-800 focus-visible:ring-amber-500 focus-visible:border-amber-500 text-zinc-100" 
                    placeholder="192.168.1.1"
                  />
                  {form.formState.errors.host && <p className="text-xs text-red-500">{form.formState.errors.host.message}</p>}
                </div>
                <div className="col-span-1 space-y-2">
                  <Label htmlFor="port" className="text-zinc-300">Port</Label>
                  <Input 
                    id="port" 
                    type="number" 
                    {...form.register("port")} 
                    className="bg-zinc-900/50 border-zinc-800 focus-visible:ring-amber-500 focus-visible:border-amber-500 text-zinc-100" 
                  />
                  {form.formState.errors.port && <p className="text-xs text-red-500">{form.formState.errors.port.message}</p>}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="protocol" className="text-zinc-300">Protocol</Label>
                  <Select onValueChange={(v) => form.setValue("protocol", v as any)} defaultValue={form.getValues("protocol")}>
                    <SelectTrigger className="bg-zinc-900/50 border-zinc-800 focus-visible:ring-amber-500 text-zinc-100">
                      <SelectValue placeholder="Protocol" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#0f0f0f] border-zinc-800 text-zinc-100">
                      <SelectItem value="http">HTTP</SelectItem>
                      <SelectItem value="https">HTTPS</SelectItem>
                      <SelectItem value="socks5">SOCKS5</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="label" className="text-zinc-300">Label (Optional)</Label>
                  <Input 
                    id="label" 
                    {...form.register("label")} 
                    className="bg-zinc-900/50 border-zinc-800 focus-visible:ring-amber-500 focus-visible:border-amber-500 text-zinc-100" 
                    placeholder="Datacenter US-East"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="username" className="text-zinc-300">Username (Auth)</Label>
                  <Input 
                    id="username" 
                    {...form.register("username")} 
                    className="bg-zinc-900/50 border-zinc-800 focus-visible:ring-amber-500 focus-visible:border-amber-500 text-zinc-100" 
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password" className="text-zinc-300">Password (Auth)</Label>
                  <Input 
                    id="password" 
                    type="password" 
                    {...form.register("password")} 
                    className="bg-zinc-900/50 border-zinc-800 focus-visible:ring-amber-500 focus-visible:border-amber-500 text-zinc-100" 
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <Switch 
                  id="enabled" 
                  checked={form.watch("enabled")}
                  onCheckedChange={(v) => form.setValue("enabled", v)}
                  className="data-[state=checked]:bg-amber-500"
                />
                <Label htmlFor="enabled" className="text-zinc-300">Enable immediately</Label>
              </div>
            </form>
            <DialogFooter>
              <Button 
                type="submit" 
                form="add-proxy-form" 
                className="bg-amber-600 hover:bg-amber-500 text-zinc-950 font-semibold"
                disabled={createMutation.isPending}
              >
                {createMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Register Node
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="rounded-md border border-zinc-800 bg-[#0f0f0f] overflow-hidden">
        <Table>
          <TableHeader className="bg-zinc-900/50">
            <TableRow className="border-zinc-800 hover:bg-transparent">
              <TableHead className="text-zinc-400 font-mono uppercase tracking-wider text-xs">Target</TableHead>
              <TableHead className="text-zinc-400 font-mono uppercase tracking-wider text-xs">Protocol</TableHead>
              <TableHead className="text-zinc-400 font-mono uppercase tracking-wider text-xs">Label</TableHead>
              <TableHead className="text-zinc-400 font-mono uppercase tracking-wider text-xs">Status</TableHead>
              <TableHead className="text-zinc-400 font-mono uppercase tracking-wider text-xs">Last Used</TableHead>
              <TableHead className="text-right text-zinc-400 font-mono uppercase tracking-wider text-xs">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {listQuery.isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-zinc-500">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto text-amber-500" />
                </TableCell>
              </TableRow>
            ) : listQuery.data?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="h-32 text-center text-zinc-500">
                  <ServerCrash className="w-8 h-8 mx-auto mb-2 opacity-20" />
                  No proxies in the fleet.
                </TableCell>
              </TableRow>
            ) : (
              <AnimatePresence>
                {listQuery.data?.map((proxy) => (
                  <motion.tr 
                    key={proxy.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="border-zinc-800 hover:bg-zinc-900/50 transition-colors group"
                  >
                    <TableCell className="font-mono text-sm text-zinc-200">
                      {proxy.host}:{proxy.port}
                      {proxy.username && (
                         <span className="text-xs text-zinc-600 block">auth required</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="bg-zinc-900 border-zinc-700 text-zinc-300 font-mono text-xs">
                        {proxy.protocol.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-zinc-400">
                      {proxy.label || "—"}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          className={`w-8 h-8 rounded-full transition-all ${
                            proxy.enabled 
                              ? "bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 hover:text-emerald-400" 
                              : "bg-zinc-800 text-zinc-500 hover:bg-zinc-700 hover:text-zinc-400"
                          }`}
                          onClick={() => handleToggle(proxy.id)}
                          disabled={toggleMutation.isPending}
                          title={proxy.enabled ? "Disable" : "Enable"}
                        >
                          {proxy.enabled ? <Power className="w-4 h-4" /> : <PowerOff className="w-4 h-4" />}
                        </Button>
                        <span className={`text-xs font-medium ${proxy.enabled ? "text-emerald-500" : "text-zinc-500"}`}>
                          {proxy.enabled ? "ACTIVE" : "INACTIVE"}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-zinc-500 font-mono text-xs">
                      {proxy.lastUsedAt ? format(new Date(proxy.lastUsedAt), "MM/dd HH:mm") : "Never"}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800">
                            <span className="sr-only">Open menu</span>
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="bg-[#0f0f0f] border-zinc-800 text-zinc-100">
                          <DropdownMenuItem 
                            className="text-red-400 hover:text-red-300 focus:text-red-300 hover:bg-red-950/20 focus:bg-red-950/20 cursor-pointer"
                            onClick={() => setProxyToDelete(proxy.id)}
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete Proxy
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </motion.tr>
                ))}
              </AnimatePresence>
            )}
          </TableBody>
        </Table>
      </div>

      <Dialog open={proxyToDelete !== null} onOpenChange={(open) => !open && setProxyToDelete(null)}>
        <DialogContent className="sm:max-w-[425px] bg-[#0f0f0f] border-zinc-800 text-zinc-100">
          <DialogHeader>
            <DialogTitle className="text-red-500 flex items-center gap-2">
              <Trash2 className="w-5 h-5" />
              Confirm Deletion
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              Are you sure you want to permanently remove this proxy? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4">
            <Button variant="outline" className="border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100" onClick={() => setProxyToDelete(null)}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              className="bg-red-600 hover:bg-red-500 text-white" 
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              Terminate Node
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

    </div>
  );
}
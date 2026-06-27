import { useState } from "react";
import { useAdminScraperUsers } from "@/hooks/useScraperUsers";
import { 
  Users, 
  Plus, 
  Trash2, 
  MoreVertical,
  Loader2,
  Minus,
  Activity
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
import { motion, AnimatePresence } from "framer-motion";
import { format } from "date-fns";

const userSchema = z.object({
  email: z.string().email("Invalid email address"),
  tokenBalance: z.coerce.number().int().min(0).default(0),
  externalId: z.string().optional(),
  notes: z.string().optional(),
});

type UserForm = z.infer<typeof userSchema>;

export default function UserManager() {
  const { listQuery, createMutation, deleteMutation, adjustTokensMutation } = useAdminScraperUsers();
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<number | null>(null);
  
  const [adjustingUser, setAdjustingUser] = useState<{id: number, email: string} | null>(null);
  const [adjustAmount, setAdjustAmount] = useState<number>(0);

  const form = useForm<UserForm>({
    resolver: zodResolver(userSchema),
    defaultValues: {
      email: "",
      tokenBalance: 0,
      externalId: "",
      notes: "",
    },
  });

  const onSubmit = (data: UserForm) => {
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
    if (userToDelete) {
      deleteMutation.mutate({ id: userToDelete }, {
        onSuccess: () => setUserToDelete(null)
      });
    }
  };

  const handleAdjustTokens = () => {
    if (adjustingUser && adjustAmount !== 0) {
      adjustTokensMutation.mutate(
        { id: adjustingUser.id, data: { amount: adjustAmount, reason: "Admin adjustment" } },
        {
          onSuccess: () => {
            setAdjustingUser(null);
            setAdjustAmount(0);
          }
        }
      );
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-zinc-100 flex items-center gap-3">
            <Users className="w-8 h-8 text-amber-500" />
            Client Accounts
          </h1>
          <p className="text-zinc-400 mt-1">Manage scraper users and token allocations.</p>
        </div>

        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogTrigger asChild>
            <Button className="bg-amber-600 hover:bg-amber-500 text-zinc-950 font-semibold" data-testid="btn-add-user">
              <Plus className="w-4 h-4 mr-2" />
              New Account
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px] bg-[#0f0f0f] border-zinc-800 text-zinc-100">
            <DialogHeader>
              <DialogTitle>Provision Account</DialogTitle>
              <DialogDescription className="text-zinc-400">
                Create a new user profile for API access.
              </DialogDescription>
            </DialogHeader>
            <form id="add-user-form" onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-zinc-300">Email Address</Label>
                <Input 
                  id="email" 
                  {...form.register("email")} 
                  className="bg-zinc-900/50 border-zinc-800 focus-visible:ring-amber-500 focus-visible:border-amber-500 text-zinc-100" 
                  placeholder="client@example.com"
                />
                {form.formState.errors.email && <p className="text-xs text-red-500">{form.formState.errors.email.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="tokenBalance" className="text-zinc-300">Initial Token Grant</Label>
                <Input 
                  id="tokenBalance" 
                  type="number" 
                  {...form.register("tokenBalance")} 
                  className="bg-zinc-900/50 border-zinc-800 focus-visible:ring-amber-500 focus-visible:border-amber-500 text-zinc-100" 
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="externalId" className="text-zinc-300">External/Billing ID (Optional)</Label>
                <Input 
                  id="externalId" 
                  {...form.register("externalId")} 
                  className="bg-zinc-900/50 border-zinc-800 focus-visible:ring-amber-500 focus-visible:border-amber-500 text-zinc-100" 
                  placeholder="cus_..."
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes" className="text-zinc-300">Administrative Notes</Label>
                <Input 
                  id="notes" 
                  {...form.register("notes")} 
                  className="bg-zinc-900/50 border-zinc-800 focus-visible:ring-amber-500 focus-visible:border-amber-500 text-zinc-100" 
                />
              </div>
            </form>
            <DialogFooter>
              <Button 
                type="submit" 
                form="add-user-form" 
                className="bg-amber-600 hover:bg-amber-500 text-zinc-950 font-semibold"
                disabled={createMutation.isPending}
              >
                {createMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Provision
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="rounded-md border border-zinc-800 bg-[#0f0f0f] overflow-hidden">
        <Table>
          <TableHeader className="bg-zinc-900/50">
            <TableRow className="border-zinc-800 hover:bg-transparent">
              <TableHead className="text-zinc-400 font-mono uppercase tracking-wider text-xs">Client Identity</TableHead>
              <TableHead className="text-zinc-400 font-mono uppercase tracking-wider text-xs text-center">Token Balance</TableHead>
              <TableHead className="text-zinc-400 font-mono uppercase tracking-wider text-xs hidden md:table-cell">References</TableHead>
              <TableHead className="text-zinc-400 font-mono uppercase tracking-wider text-xs hidden lg:table-cell">Created</TableHead>
              <TableHead className="text-right text-zinc-400 font-mono uppercase tracking-wider text-xs">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {listQuery.isLoading ? (
              <TableRow>
                <TableCell colSpan={5} className="h-24 text-center text-zinc-500">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto text-amber-500" />
                </TableCell>
              </TableRow>
            ) : listQuery.data?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="h-32 text-center text-zinc-500">
                  <Users className="w-8 h-8 mx-auto mb-2 opacity-20" />
                  No client accounts provisioned.
                </TableCell>
              </TableRow>
            ) : (
              <AnimatePresence>
                {listQuery.data?.map((user) => (
                  <motion.tr 
                    key={user.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="border-zinc-800 hover:bg-zinc-900/50 transition-colors group"
                  >
                    <TableCell>
                      <div className="font-medium text-zinc-200">{user.email}</div>
                      {user.notes && <div className="text-xs text-zinc-500 mt-1 max-w-[200px] truncate">{user.notes}</div>}
                    </TableCell>
                    <TableCell className="text-center align-middle">
                      <div className="flex items-center justify-center gap-2">
                        <Badge 
                          variant="outline" 
                          className={`font-mono text-sm px-2 py-0.5 border ${
                            user.tokenBalance < 5 ? "bg-red-500/10 text-red-400 border-red-500/20" :
                            user.tokenBalance <= 20 ? "bg-amber-500/10 text-amber-400 border-amber-500/20" :
                            "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          }`}
                        >
                          {user.tokenBalance}
                        </Badge>
                        <div className="flex bg-zinc-900 rounded border border-zinc-800 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="w-6 h-6 rounded-none rounded-l text-zinc-400 hover:text-red-400 hover:bg-red-950/30"
                            onClick={() => { setAdjustingUser({id: user.id, email: user.email}); setAdjustAmount(-10); }}
                          >
                            <Minus className="w-3 h-3" />
                          </Button>
                          <div className="w-[1px] bg-zinc-800" />
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="w-6 h-6 rounded-none rounded-r text-zinc-400 hover:text-emerald-400 hover:bg-emerald-950/30"
                            onClick={() => { setAdjustingUser({id: user.id, email: user.email}); setAdjustAmount(10); }}
                          >
                            <Plus className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-zinc-400 hidden md:table-cell">
                      {user.externalId ? (
                        <Badge variant="outline" className="bg-zinc-900 border-zinc-800 text-zinc-500 font-mono text-[10px]">
                          {user.externalId}
                        </Badge>
                      ) : "—"}
                    </TableCell>
                    <TableCell className="text-sm text-zinc-500 hidden lg:table-cell font-mono text-xs">
                      {format(new Date(user.createdAt), "MM/dd/yy")}
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
                            className="hover:text-amber-400 focus:text-amber-400 hover:bg-amber-950/20 focus:bg-amber-950/20 cursor-pointer"
                            onClick={() => { setAdjustingUser({id: user.id, email: user.email}); setAdjustAmount(0); }}
                          >
                            <Activity className="w-4 h-4 mr-2" />
                            Adjust Tokens
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            className="text-red-400 hover:text-red-300 focus:text-red-300 hover:bg-red-950/20 focus:bg-red-950/20 cursor-pointer"
                            onClick={() => setUserToDelete(user.id)}
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Terminate Account
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

      <Dialog open={adjustingUser !== null} onOpenChange={(open) => !open && setAdjustingUser(null)}>
        <DialogContent className="sm:max-w-[425px] bg-[#0f0f0f] border-zinc-800 text-zinc-100">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-amber-500" />
              Token Adjustment
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              Modify balance for <span className="font-mono text-zinc-300">{adjustingUser?.email}</span>. Use negative numbers to deduct.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="amount" className="text-zinc-300">Adjustment Amount</Label>
            <div className="flex gap-2 mt-2">
              <Button variant="outline" className="border-zinc-800 bg-zinc-900 text-zinc-400" onClick={() => setAdjustAmount(a => a - 10)}>-10</Button>
              <Input 
                id="amount" 
                type="number" 
                value={adjustAmount || ""} 
                onChange={(e) => setAdjustAmount(parseInt(e.target.value) || 0)}
                className="bg-zinc-900/50 border-zinc-800 focus-visible:ring-amber-500 focus-visible:border-amber-500 text-zinc-100 text-center font-mono text-lg" 
              />
              <Button variant="outline" className="border-zinc-800 bg-zinc-900 text-zinc-400" onClick={() => setAdjustAmount(a => a + 10)}>+10</Button>
            </div>
            <div className="text-center mt-3 text-sm text-zinc-500">
              Net change: <span className={`font-mono font-bold ${adjustAmount > 0 ? "text-emerald-500" : adjustAmount < 0 ? "text-red-500" : "text-zinc-500"}`}>
                {adjustAmount > 0 ? "+" : ""}{adjustAmount}
              </span> tokens
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" className="border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100" onClick={() => setAdjustingUser(null)}>
              Cancel
            </Button>
            <Button 
              className="bg-amber-600 hover:bg-amber-500 text-zinc-950 font-bold" 
              onClick={handleAdjustTokens}
              disabled={adjustTokensMutation.isPending || adjustAmount === 0}
            >
              {adjustTokensMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Execute Adjustment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={userToDelete !== null} onOpenChange={(open) => !open && setUserToDelete(null)}>
        <DialogContent className="sm:max-w-[425px] bg-[#0f0f0f] border-zinc-800 text-zinc-100">
          <DialogHeader>
            <DialogTitle className="text-red-500 flex items-center gap-2">
              <Trash2 className="w-5 h-5" />
              Confirm Termination
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              This will permanently delete the user account and revoke all access. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4">
            <Button variant="outline" className="border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100" onClick={() => setUserToDelete(null)}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              className="bg-red-600 hover:bg-red-500 text-white font-bold" 
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Terminate Account
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
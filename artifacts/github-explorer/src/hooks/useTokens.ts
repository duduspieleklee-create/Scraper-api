import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/apiClient";

export function useTokens() {
  const transactionsQuery = useQuery({
    queryKey: ["tokens", "transactions"],
    queryFn: () => apiFetch("/tokens/transactions").catch(() => []),
  });

  return {
    transactions: transactionsQuery.data || [],
    isLoading: transactionsQuery.isLoading,
    isError: transactionsQuery.isError,
  };
}

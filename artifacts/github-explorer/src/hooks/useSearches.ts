import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/apiClient";

export function useSearches() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["searches"],
    queryFn: () => apiFetch("/searches"),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) =>
      apiFetch("/searches", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["searches"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string | number) =>
      apiFetch(`/searches/${id}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["searches"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const pauseMutation = useMutation({
    mutationFn: (id: string | number) =>
      apiFetch(`/searches/${id}/pause`, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["searches"] });
    },
  });

  const resumeMutation = useMutation({
    mutationFn: (id: string | number) =>
      apiFetch(`/searches/${id}/resume`, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["searches"] });
    },
  });

  return {
    searches: query.data || [],
    isLoading: query.isLoading,
    isError: query.isError,
    createSearch: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
    deleteSearch: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
    pauseSearch: pauseMutation.mutateAsync,
    isPausing: pauseMutation.isPending,
    resumeSearch: resumeMutation.mutateAsync,
    isResuming: resumeMutation.isPending,
  };
}

export function useSearch(id: string) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["search", id],
    queryFn: () => apiFetch(`/searches/${id}`),
    enabled: !!id,
  });

  const pauseMutation = useMutation({
    mutationFn: () =>
      apiFetch(`/searches/${id}/pause`, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["search", id] });
      queryClient.invalidateQueries({ queryKey: ["searches"] });
    },
  });

  const resumeMutation = useMutation({
    mutationFn: () =>
      apiFetch(`/searches/${id}/resume`, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["search", id] });
      queryClient.invalidateQueries({ queryKey: ["searches"] });
    },
  });

  return {
    search: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    pauseSearch: pauseMutation.mutateAsync,
    isPausing: pauseMutation.isPending,
    resumeSearch: resumeMutation.mutateAsync,
    isResuming: resumeMutation.isPending,
  };
}

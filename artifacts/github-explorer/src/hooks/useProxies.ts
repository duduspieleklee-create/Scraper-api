import { useQueryClient } from "@tanstack/react-query";
import { 
  useListProxies, 
  useCreateProxy, 
  useUpdateProxy, 
  useDeleteProxy, 
  useToggleProxy,
  useGetProxyStats,
  getListProxiesQueryKey,
  getGetProxyStatsQueryKey
} from "@workspace/api-client-react";

export function useAdminProxies() {
  const queryClient = useQueryClient();

  const invalidateProxies = () => {
    queryClient.invalidateQueries({ queryKey: getListProxiesQueryKey() });
    queryClient.invalidateQueries({ queryKey: getGetProxyStatsQueryKey() });
  };

  const listQuery = useListProxies();
  const statsQuery = useGetProxyStats();
  
  const createMutation = useCreateProxy({
    mutation: { onSuccess: invalidateProxies }
  });
  
  const updateMutation = useUpdateProxy({
    mutation: { onSuccess: invalidateProxies }
  });
  
  const deleteMutation = useDeleteProxy({
    mutation: { onSuccess: invalidateProxies }
  });
  
  const toggleMutation = useToggleProxy({
    mutation: { onSuccess: invalidateProxies }
  });

  return {
    listQuery,
    statsQuery,
    createMutation,
    updateMutation,
    deleteMutation,
    toggleMutation
  };
}
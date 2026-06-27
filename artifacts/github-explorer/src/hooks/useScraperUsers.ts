import { useQueryClient } from "@tanstack/react-query";
import { 
  useListScraperUsers, 
  useCreateScraperUser, 
  useDeleteScraperUser, 
  useAdjustUserTokens,
  getListScraperUsersQueryKey,
  getGetScraperUserQueryKey
} from "@workspace/api-client-react";

export function useAdminScraperUsers() {
  const queryClient = useQueryClient();

  const invalidateUsers = () => {
    queryClient.invalidateQueries({ queryKey: getListScraperUsersQueryKey() });
  };

  const listQuery = useListScraperUsers();
  
  const createMutation = useCreateScraperUser({
    mutation: { onSuccess: invalidateUsers }
  });
  
  const deleteMutation = useDeleteScraperUser({
    mutation: { onSuccess: invalidateUsers }
  });
  
  const adjustTokensMutation = useAdjustUserTokens({
    mutation: { onSuccess: invalidateUsers }
  });

  return {
    listQuery,
    createMutation,
    deleteMutation,
    adjustTokensMutation
  };
}
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { empresaService } from '../services/empresaService';
import { Empresa, EmpresaForm } from '../types';

export const useEmpresas = (page = 1, size = 10, search?: string) => {
  return useQuery({
    queryKey: ['empresas', page, size, search],
    queryFn: () => empresaService.getEmpresas(page, size, search),
  });
};

export const useEmpresa = (id: number) => {
  return useQuery({
    queryKey: ['empresa', id],
    queryFn: () => empresaService.getEmpresaById(id),
    enabled: !!id,
  });
};

export const useCreateEmpresa = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (empresa: EmpresaForm) => empresaService.createEmpresa(empresa),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['empresas'] });
    },
  });
};

export const useUpdateEmpresa = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, empresa }: { id: number; empresa: Partial<EmpresaForm> }) =>
      empresaService.updateEmpresa(id, empresa),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['empresa', id] });
      queryClient.invalidateQueries({ queryKey: ['empresas'] });
    },
  });
};

export const useDeleteEmpresa = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => empresaService.deleteEmpresa(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['empresas'] });
    },
  });
};

export const useEmpresaStats = (id: number) => {
  return useQuery({
    queryKey: ['empresa-stats', id],
    queryFn: () => empresaService.getEmpresaStats(id),
    enabled: !!id,
  });
};

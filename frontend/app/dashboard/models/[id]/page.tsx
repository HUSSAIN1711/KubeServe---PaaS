'use client';

import { use } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { modelsApi } from '@/lib/api';
import { DashboardLayout } from '@/components/Layout/DashboardLayout';
import Link from 'next/link';
import { format } from 'date-fns';

function StatusBadge({ status }: { status: string }) {
  const statusColors: Record<string, string> = {
    Ready: 'bg-green-100 text-green-800',
    Building: 'bg-yellow-100 text-yellow-800',
    Failed: 'bg-red-100 text-red-800',
    Pending: 'bg-gray-100 text-gray-800',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        statusColors[status] || statusColors.Pending
      }`}
    >
      {status}
    </span>
  );
}

export default function ModelDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();
  const modelId = parseInt(id);

  const { data: model, isLoading } = useQuery({
    queryKey: ['model', modelId],
    queryFn: () => modelsApi.getModel(modelId),
    refetchInterval: 30000, // Poll every 30 seconds
  });

  const { data: versions } = useQuery({
    queryKey: ['versions', modelId],
    queryFn: () => modelsApi.getVersions(modelId),
    enabled: !!modelId,
    refetchInterval: 30000,
  });

  const deleteModelMutation = useMutation({
    mutationFn: () => modelsApi.deleteModel(modelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
      router.push('/dashboard/models');
    },
  });

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Loading model...</div>
        </div>
      </DashboardLayout>
    );
  }

  if (!model) {
    return (
      <DashboardLayout>
        <div className="rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-800">Model not found</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="px-4 py-6 sm:px-0">
        <div className="mb-6">
          <Link
            href="/dashboard/models"
            className="text-primary-600 hover:text-primary-500 text-sm font-medium"
          >
            ← Back to Models
          </Link>
        </div>

        <div className="bg-white shadow sm:rounded-lg mb-6">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">{model.name}</h1>
                <p className="mt-1 text-sm text-gray-500">
                  Type: <span className="font-medium uppercase">{model.type}</span>
                </p>
                <p className="mt-1 text-sm text-gray-500">
                  Created {format(new Date(model.created_at), 'MMM d, yyyy')}
                </p>
              </div>
              <button
                onClick={() => {
                  if (confirm('Are you sure you want to delete this model?')) {
                    deleteModelMutation.mutate();
                  }
                }}
                disabled={deleteModelMutation.isPending}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
              >
                {deleteModelMutation.isPending ? 'Deleting...' : 'Delete Model'}
              </button>
            </div>
          </div>
        </div>

        <div className="bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-medium text-gray-900">Versions</h2>
              <Link
                href={`/dashboard/models/${modelId}/versions/new`}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                Add Version
              </Link>
            </div>

            {!versions || versions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No versions yet.</p>
                <Link
                  href={`/dashboard/models/${modelId}/versions/new`}
                  className="text-primary-600 hover:text-primary-500 font-medium mt-2 inline-block"
                >
                  Create first version →
                </Link>
              </div>
            ) : (
              <div className="overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Version
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        S3 Path
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {versions.map((version: any) => (
                      <tr key={version.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {version.version_tag}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <StatusBadge status={version.status || 'Pending'} />
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {version.s3_path || (
                            <span className="text-gray-400">Not uploaded</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {format(new Date(version.created_at), 'MMM d, yyyy')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <Link
                            href={`/dashboard/models/${modelId}/versions/${version.id}`}
                            className="text-primary-600 hover:text-primary-900"
                          >
                            View
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}


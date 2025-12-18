'use client';

import { DashboardLayout } from '@/components/Layout/DashboardLayout';
import { useQuery } from '@tanstack/react-query';
import { modelsApi } from '@/lib/api';
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

export default function DashboardPage() {
  const { data: models, isLoading, error } = useQuery({
    queryKey: ['models'],
    queryFn: modelsApi.getModels,
    refetchInterval: 30000, // Poll every 30 seconds
  });

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Loading models...</div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-800">
            Failed to load models. Please try again.
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="px-4 py-6 sm:px-0">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <Link
            href="/dashboard/models/new"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Create Model
          </Link>
        </div>

        {!models || models.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">No models yet.</p>
            <Link
              href="/dashboard/models/new"
              className="text-primary-600 hover:text-primary-500 font-medium"
            >
              Create your first model →
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {models.map((model: any) => (
              <Link
                key={model.id}
                href={`/dashboard/models/${model.id}`}
                className="bg-white overflow-hidden shadow rounded-lg hover:shadow-lg transition-shadow"
              >
                <div className="p-5">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-medium text-gray-900">{model.name}</h3>
                    <span className="text-xs text-gray-500 uppercase">{model.type}</span>
                  </div>
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Versions:</span>
                      <span className="font-medium">{model.versions?.length || 0}</span>
                    </div>
                    <div className="mt-2">
                      {model.versions && model.versions.length > 0 && (
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-500">Latest:</span>
                          <StatusBadge
                            status={model.versions[0].status || 'Pending'}
                          />
                        </div>
                      )}
                    </div>
                    <div className="mt-4 text-xs text-gray-400">
                      Created {format(new Date(model.created_at), 'MMM d, yyyy')}
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}


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

export default function ModelsPage() {
  const { data: models, isLoading, error, refetch } = useQuery({
    queryKey: ['models'],
    queryFn: modelsApi.getModels,
    refetchInterval: 30000, // Poll every 30 seconds for status updates
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
          <h1 className="text-3xl font-bold text-gray-900">Models</h1>
          <div className="flex gap-3">
            <button
              onClick={() => refetch()}
              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Refresh
            </button>
            <Link
              href="/dashboard/models/new"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Create Model
            </Link>
          </div>
        </div>

        {!models || models.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500 mb-4">No models yet.</p>
            <Link
              href="/dashboard/models/new"
              className="text-primary-600 hover:text-primary-500 font-medium"
            >
              Create your first model →
            </Link>
          </div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {models.map((model: any) => (
                <li key={model.id}>
                  <Link
                    href={`/dashboard/models/${model.id}`}
                    className="block hover:bg-gray-50 transition-colors"
                  >
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <p className="text-sm font-medium text-primary-600 truncate">
                            {model.name}
                          </p>
                          <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            {model.type}
                          </span>
                        </div>
                        <div className="ml-2 flex-shrink-0 flex">
                          {model.versions && model.versions.length > 0 && (
                            <StatusBadge
                              status={model.versions[0].status || 'Pending'}
                            />
                          )}
                        </div>
                      </div>
                      <div className="mt-2 sm:flex sm:justify-between">
                        <div className="sm:flex">
                          <p className="flex items-center text-sm text-gray-500">
                            {model.versions?.length || 0} version
                            {(model.versions?.length || 0) !== 1 ? 's' : ''}
                          </p>
                        </div>
                        <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                          <p>
                            Created {format(new Date(model.created_at), 'MMM d, yyyy')}
                          </p>
                        </div>
                      </div>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}


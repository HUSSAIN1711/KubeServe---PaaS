'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { use } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { modelsApi } from '@/lib/api';
import { DashboardLayout } from '@/components/Layout/DashboardLayout';

export default function NewVersionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();
  const modelId = parseInt(id);

  const [versionTag, setVersionTag] = useState('');
  const [s3Path, setS3Path] = useState('');
  const [error, setError] = useState('');

  const createVersionMutation = useMutation({
    mutationFn: (data: { versionTag: string; s3Path: string }) =>
      modelsApi.createVersion(modelId, data.versionTag, data.s3Path),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['versions', modelId] });
      queryClient.invalidateQueries({ queryKey: ['model', modelId] });
      router.push(`/dashboard/models/${modelId}/versions/${data.id}`);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create version');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!versionTag.trim()) {
      setError('Version tag is required');
      return;
    }

    createVersionMutation.mutate({
      versionTag: versionTag.trim(),
      s3Path: s3Path.trim() || `s3://kubeserve-models/user-1/model/${versionTag}/model.joblib`,
    });
  };

  return (
    <DashboardLayout>
      <div className="px-4 py-6 sm:px-0">
        <div className="max-w-2xl mx-auto">
          <div className="mb-6">
            <button
              onClick={() => router.back()}
              className="text-primary-600 hover:text-primary-500 text-sm font-medium"
            >
              ← Back
            </button>
          </div>

          <h1 className="text-3xl font-bold text-gray-900 mb-6">Create New Version</h1>

          <div className="bg-white shadow sm:rounded-lg">
            <form onSubmit={handleSubmit} className="px-4 py-5 sm:p-6">
              {error && (
                <div className="mb-4 rounded-md bg-red-50 p-4">
                  <div className="text-sm text-red-800">{error}</div>
                </div>
              )}

              <div className="space-y-6">
                <div>
                  <label
                    htmlFor="versionTag"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Version Tag
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      name="versionTag"
                      id="versionTag"
                      required
                      className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="e.g., v1.0.0"
                      value={versionTag}
                      onChange={(e) => setVersionTag(e.target.value)}
                    />
                  </div>
                  <p className="mt-2 text-sm text-gray-500">
                    A unique identifier for this version (e.g., v1.0.0, v2.1.3)
                  </p>
                </div>

                <div>
                  <label
                    htmlFor="s3Path"
                    className="block text-sm font-medium text-gray-700"
                  >
                    S3 Path (Optional)
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      name="s3Path"
                      id="s3Path"
                      className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="s3://bucket/path/to/model.joblib"
                      value={s3Path}
                      onChange={(e) => setS3Path(e.target.value)}
                    />
                  </div>
                  <p className="mt-2 text-sm text-gray-500">
                    S3 path where the model file will be stored. If not provided, a default path will be generated.
                  </p>
                </div>
              </div>

              <div className="mt-6 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => router.back()}
                  className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createVersionMutation.isPending}
                  className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {createVersionMutation.isPending ? 'Creating...' : 'Create Version'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}


'use client';

import { use } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { modelsApi } from '@/lib/api';
import { DashboardLayout } from '@/components/Layout/DashboardLayout';
import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
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

export default function VersionDetailPage({
  params,
}: {
  params: Promise<{ id: string; versionId: string }>;
}) {
  const { id, versionId } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();
  const modelId = parseInt(id);
  const vId = parseInt(versionId);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);

  const { data: version, isLoading } = useQuery({
    queryKey: ['version', vId],
    queryFn: () => modelsApi.getVersions(modelId).then((versions) => 
      versions.find((v: any) => v.id === vId)
    ),
    refetchInterval: 30000,
  });

  const { data: deployments } = useQuery({
    queryKey: ['deployments', vId],
    queryFn: () => modelsApi.getDeployments(vId),
    enabled: !!vId,
    refetchInterval: 30000,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => modelsApi.uploadModelFile(vId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['version', vId] });
      queryClient.invalidateQueries({ queryKey: ['versions', modelId] });
      setUploadProgress(null);
    },
    onError: () => {
      setUploadProgress(null);
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: (status: string) => modelsApi.updateVersionStatus(vId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['version', vId] });
      queryClient.invalidateQueries({ queryKey: ['versions', modelId] });
    },
  });

  const createDeploymentMutation = useMutation({
    mutationFn: (replicas: number) => modelsApi.createDeployment(vId, replicas),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments', vId] });
    },
  });

  const deleteDeploymentMutation = useMutation({
    mutationFn: (deploymentId: number) => modelsApi.deleteDeployment(deploymentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments', vId] });
    },
  });

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/octet-stream': ['.joblib', '.pkl', '.pickle'],
    },
    maxFiles: 1,
    onDrop: async (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setUploadProgress(0);
        // Simulate upload progress
        const interval = setInterval(() => {
          setUploadProgress((prev) => (prev !== null && prev < 90 ? prev + 10 : prev));
        }, 200);
        
        try {
          await uploadMutation.mutateAsync(acceptedFiles[0]);
          clearInterval(interval);
          setUploadProgress(100);
        } catch (error) {
          clearInterval(interval);
        }
      }
    },
  });

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Loading version...</div>
        </div>
      </DashboardLayout>
    );
  }

  if (!version) {
    return (
      <DashboardLayout>
        <div className="rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-800">Version not found</div>
        </div>
      </DashboardLayout>
    );
  }

  const canDeploy = version.status === 'Ready' && version.s3_path;

  return (
    <DashboardLayout>
      <div className="px-4 py-6 sm:px-0">
        <div className="mb-6">
          <button
            onClick={() => router.back()}
            className="text-primary-600 hover:text-primary-500 text-sm font-medium"
          >
            ← Back
          </button>
        </div>

        <div className="bg-white shadow sm:rounded-lg mb-6">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Version {version.version_tag}
                </h1>
                <div className="mt-2">
                  <StatusBadge status={version.status || 'Pending'} />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 mt-6">
              <div>
                <label className="text-sm font-medium text-gray-500">S3 Path</label>
                <p className="mt-1 text-sm text-gray-900">
                  {version.s3_path || (
                    <span className="text-gray-400">Not uploaded</span>
                  )}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Created</label>
                <p className="mt-1 text-sm text-gray-900">
                  {format(new Date(version.created_at), 'MMM d, yyyy HH:mm')}
                </p>
              </div>
            </div>

            {/* Upload Section */}
            {!version.s3_path && (
              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Model File
                </label>
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                    isDragActive
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <input {...getInputProps()} />
                  <div className="space-y-2">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      stroke="currentColor"
                      fill="none"
                      viewBox="0 0 48 48"
                    >
                      <path
                        d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    {uploadProgress !== null ? (
                      <div>
                        <p className="text-sm text-gray-600">
                          Uploading... {uploadProgress}%
                        </p>
                        <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-primary-600 h-2 rounded-full transition-all"
                            style={{ width: `${uploadProgress}%` }}
                          />
                        </div>
                      </div>
                    ) : (
                      <>
                        <p className="text-sm text-gray-600">
                          {isDragActive
                            ? 'Drop the file here'
                            : 'Drag and drop a model file here, or click to select'}
                        </p>
                        <p className="text-xs text-gray-500">
                          Supports .joblib, .pkl, .pickle files
                        </p>
                      </>
                    )}
                  </div>
                </div>
                {uploadMutation.isError && (
                  <p className="mt-2 text-sm text-red-600">
                    Upload failed. Please try again.
                  </p>
                )}
              </div>
            )}

            {/* Status Update */}
            {version.s3_path && version.status !== 'Ready' && (
              <div className="mt-6">
                <button
                  onClick={() => updateStatusMutation.mutate('Ready')}
                  disabled={updateStatusMutation.isPending}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50"
                >
                  {updateStatusMutation.isPending ? 'Updating...' : 'Mark as Ready'}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Deployments Section */}
        <div className="bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-medium text-gray-900">Deployments</h2>
              {canDeploy && (
                <button
                  onClick={() => {
                    if (confirm('Deploy this version with 1 replica?')) {
                      createDeploymentMutation.mutate(1);
                    }
                  }}
                  disabled={createDeploymentMutation.isPending}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50"
                >
                  {createDeploymentMutation.isPending ? 'Deploying...' : 'Deploy'}
                </button>
              )}
            </div>

            {!canDeploy && version.status !== 'Ready' && (
              <p className="text-sm text-gray-500 mb-4">
                Version must be Ready and have an uploaded model file to deploy.
              </p>
            )}

            {!deployments || deployments.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No deployments yet.</p>
                {canDeploy && (
                  <button
                    onClick={() => {
                      if (confirm('Deploy this version with 1 replica?')) {
                        createDeploymentMutation.mutate(1);
                      }
                    }}
                    className="mt-2 text-primary-600 hover:text-primary-500 font-medium"
                  >
                    Deploy now →
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {deployments.map((deployment: any) => (
                  <div
                    key={deployment.id}
                    className="border border-gray-200 rounded-lg p-4"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">
                          Deployment #{deployment.id}
                        </h3>
                        <p className="mt-1 text-sm text-gray-500">
                          Replicas: {deployment.replicas}
                        </p>
                        {deployment.url && (
                          <a
                            href={deployment.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-1 text-sm text-primary-600 hover:text-primary-500"
                          >
                            {deployment.url}
                          </a>
                        )}
                      </div>
                      <button
                        onClick={() => {
                          if (confirm('Are you sure you want to delete this deployment?')) {
                            deleteDeploymentMutation.mutate(deployment.id);
                          }
                        }}
                        disabled={deleteDeploymentMutation.isPending}
                        className="text-sm text-red-600 hover:text-red-700 disabled:opacity-50"
                      >
                        {deleteDeploymentMutation.isPending ? 'Deleting...' : 'Delete'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}


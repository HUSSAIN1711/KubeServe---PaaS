'use client';

import { use } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { modelsApi } from '@/lib/api';
import { DashboardLayout } from '@/components/Layout/DashboardLayout';
import { format } from 'date-fns';

const GRAFANA_URL = process.env.NEXT_PUBLIC_GRAFANA_URL || 'http://localhost:30091';

export default function DeploymentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();
  const deploymentId = parseInt(id);

  // Note: We need to find the deployment by iterating through models/versions
  // In a real app, you'd have a GET /deployments/{id} endpoint
  const { data: models } = useQuery({
    queryKey: ['models'],
    queryFn: modelsApi.getModels,
  });

  // Find deployment across all models
  const [deployment, setDeployment] = useState<any>(null);
  const [version, setVersion] = useState<any>(null);
  const [model, setModel] = useState<any>(null);

  useEffect(() => {
    const findDeployment = async () => {
      if (!models) return;

      for (const m of models) {
        try {
          const versions = await modelsApi.getVersions(m.id);
          for (const v of versions) {
            const deployments = await modelsApi.getDeployments(v.id);
            const found = deployments.find((d: any) => d.id === deploymentId);
            if (found) {
              setDeployment(found);
              setVersion(v);
              setModel(m);
              return;
            }
          }
        } catch (error) {
          console.error('Error fetching versions:', error);
        }
      }
    };

    findDeployment();
  }, [models, deploymentId]);

  const deleteDeploymentMutation = useMutation({
    mutationFn: () => modelsApi.deleteDeployment(deploymentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
      router.push('/dashboard/models');
    },
  });

  if (!deployment) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Loading deployment...</div>
        </div>
      </DashboardLayout>
    );
  }

  // Construct Grafana dashboard URL
  // Assuming we're using the deployment dashboard with namespace and deployment variables
  const grafanaDashboardUrl = `${GRAFANA_URL}/d/kubeserve-deployment/kubeserve-deployment-dashboard?orgId=1&var-namespace=user-1&var-deployment=${deployment.k8s_service_name}`;

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

        {/* Deployment Info */}
        <div className="bg-white shadow sm:rounded-lg mb-6">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Deployment #{deployment.id}
                </h1>
                <p className="mt-1 text-sm text-gray-500">
                  Model: {model?.name} - Version: {version?.version_tag}
                </p>
              </div>
              <button
                onClick={() => {
                  if (confirm('Are you sure you want to delete this deployment?')) {
                    deleteDeploymentMutation.mutate();
                  }
                }}
                disabled={deleteDeploymentMutation.isPending}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 disabled:opacity-50"
              >
                {deleteDeploymentMutation.isPending ? 'Deleting...' : 'Delete Deployment'}
              </button>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="text-sm font-medium text-gray-500">Live URL</label>
                {deployment.url ? (
                  <div className="mt-1">
                    <a
                      href={deployment.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary-600 hover:text-primary-500 break-all"
                    >
                      {deployment.url}
                    </a>
                    <p className="mt-1 text-xs text-gray-500">
                      Use this URL to make predictions
                    </p>
                  </div>
                ) : (
                  <p className="mt-1 text-sm text-gray-400">Not available</p>
                )}
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Replicas</label>
                <p className="mt-1 text-sm text-gray-900">{deployment.replicas}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">K8s Service Name</label>
                <p className="mt-1 text-sm text-gray-900 font-mono">
                  {deployment.k8s_service_name}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Created</label>
                <p className="mt-1 text-sm text-gray-900">
                  {format(new Date(deployment.created_at), 'MMM d, yyyy HH:mm')}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Grafana Dashboard Embed */}
        {deployment.url && (
          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Real-time Metrics
              </h2>
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <iframe
                  src={grafanaDashboardUrl}
                  width="100%"
                  height="800"
                  frameBorder="0"
                  className="w-full"
                  title="Grafana Dashboard"
                />
              </div>
              <p className="mt-4 text-sm text-gray-500">
                <a
                  href={grafanaDashboardUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:text-primary-500"
                >
                  Open in Grafana →
                </a>
              </p>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}


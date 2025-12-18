# Phase 7: Frontend Dashboard

## Overview

Phase 7 implements a modern Next.js frontend application for the KubeServe ML Inference Platform. The frontend provides a user-friendly interface for managing models, deployments, and monitoring metrics.

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS framework
- **React Query (TanStack Query)** - Server state management and caching
- **Axios** - HTTP client with interceptors
- **js-cookie** - JWT token storage
- **react-dropzone** - Drag-and-drop file uploads
- **date-fns** - Date formatting

## Project Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── login/                   # Login page
│   ├── register/                # Registration page
│   ├── dashboard/               # Dashboard pages
│   │   ├── page.tsx             # Main dashboard (model list)
│   │   ├── models/              # Model management
│   │   │   ├── page.tsx         # Models list
│   │   │   ├── new/             # Create model
│   │   │   └── [id]/            # Model detail
│   │   │       ├── page.tsx     # Model detail view
│   │   │       └── versions/    # Version management
│   │   │           ├── new/     # Create version
│   │   │           └── [versionId]/  # Version detail
│   │   └── deployments/         # Deployment views
│   │       └── [id]/            # Deployment detail with Grafana
│   ├── layout.tsx               # Root layout
│   ├── providers.tsx            # React Query provider
│   └── globals.css              # Global styles
├── components/                   # React components
│   └── Layout/                  # Layout components
│       └── DashboardLayout.tsx  # Dashboard layout with nav
├── lib/                         # Utilities
│   ├── api.ts                   # API client (axios)
│   └── auth.ts                  # Authentication utilities
└── package.json                 # Dependencies
```

## Features Implemented

### 7.1 Authentication (Login/Register)

**Pages**: `/login`, `/register`

**Features**:
- Login form with email/password
- Registration form with password confirmation
- JWT token stored in HTTP-only cookie
- Automatic redirect to dashboard on success
- Error handling and validation
- Link between login and register pages

**Implementation**:
- `app/login/page.tsx` - Login page component
- `app/register/page.tsx` - Registration page component
- `lib/auth.ts` - Authentication utilities (login, register, logout, token management)
- `lib/api.ts` - Axios interceptors for automatic token injection

### 7.2 Model Hub

**Pages**: `/dashboard`, `/dashboard/models`

**Features**:
- List all user's models with status badges
- Real-time status polling (every 30 seconds)
- Model cards showing:
  - Model name and type
  - Version count
  - Latest version status
  - Creation date
- Create new models
- View model details
- Delete models

**Status Badges**:
- **Ready** (green) - Version is ready to deploy
- **Building** (yellow) - Version is being processed
- **Failed** (red) - Version creation/upload failed
- **Pending** (gray) - Version is pending

**Implementation**:
- `app/dashboard/page.tsx` - Main dashboard with model grid
- `app/dashboard/models/page.tsx` - Models list page
- `app/dashboard/models/new/page.tsx` - Create model form
- `app/dashboard/models/[id]/page.tsx` - Model detail with versions table
- React Query for data fetching and caching
- Automatic refetching for real-time updates

### 7.3 Version Management

**Pages**: `/dashboard/models/[id]/versions/new`, `/dashboard/models/[id]/versions/[versionId]`

**Features**:
- Create new model versions
- Upload model files via drag-and-drop
- View version details and status
- Update version status to Ready
- View deployments for a version
- Deploy versions to Kubernetes

**File Upload**:
- Drag-and-drop interface using `react-dropzone`
- Supports `.joblib`, `.pkl`, `.pickle` files
- Upload progress indicator
- Automatic status updates after upload

**Implementation**:
- `app/dashboard/models/[id]/versions/new/page.tsx` - Create version form
- `app/dashboard/models/[id]/versions/[versionId]/page.tsx` - Version detail with upload
- File upload with progress tracking
- Status update functionality

### 7.4 Deployment View

**Pages**: `/dashboard/deployments/[id]`

**Features**:
- View deployment details
- Show live prediction URL
- Display deployment metadata (replicas, service name, created date)
- **Embed Grafana dashboard** for real-time metrics
- Delete deployments

**Grafana Integration**:
- Embedded Grafana dashboard using iframe
- Pre-configured with deployment variables (namespace, deployment name)
- Link to open dashboard in new tab
- Shows real-time metrics:
  - Request rate
  - Prediction latency (P50, P95, P99)
  - CPU/Memory usage
  - Pod replicas
  - Success/error rates

**Implementation**:
- `app/dashboard/deployments/[id]/page.tsx` - Deployment detail page
- Grafana dashboard URL construction with variables
- iframe embedding with proper sizing
- Fallback if Grafana is not available

### 7.5 Upload UI

**Features**:
- Drag-and-drop file upload
- Click to select file
- Visual feedback during drag
- Upload progress bar
- File type validation
- Error handling

**Implementation**:
- Uses `react-dropzone` library
- Integrated into version detail page
- Progress tracking during upload
- Automatic status refresh after upload

## API Integration

The frontend communicates with the KubeServe API:

**Base URL**: `http://localhost:8000/api/v1` (configurable via `NEXT_PUBLIC_API_URL`)

**Endpoints Used**:
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /me` - Get current user
- `GET /models` - List models
- `POST /models` - Create model
- `GET /models/{id}` - Get model
- `DELETE /models/{id}` - Delete model
- `GET /models/{id}/versions` - List versions
- `POST /models/{id}/versions` - Create version
- `POST /versions/{id}/upload` - Upload model file
- `PATCH /versions/{id}/status` - Update version status
- `GET /versions/{id}/deployments` - List deployments
- `POST /versions/{id}/deployments` - Create deployment
- `DELETE /deployments/{id}` - Delete deployment

## Authentication Flow

1. User logs in via `/login`
2. JWT token received from API
3. Token stored in cookie (`auth_token`)
4. Axios interceptor adds token to all requests
5. On 401 response, token cleared and user redirected to login
6. Token persists across page refreshes

## State Management

**React Query** is used for:
- Server state management
- Automatic caching
- Background refetching
- Optimistic updates
- Error handling

**Configuration**:
- Stale time: 60 seconds
- Refetch interval: 30 seconds (for models/versions)
- Automatic refetch on window focus: disabled

## Styling

**Tailwind CSS** for:
- Utility-first styling
- Responsive design
- Consistent color scheme (primary blue)
- Component styling

**Custom Colors**:
- Primary: Blue shades (500-700)
- Status colors: Green (Ready), Yellow (Building), Red (Failed), Gray (Pending)

## Getting Started

### Installation

```bash
cd frontend
npm install
```

### Environment Setup

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GRAFANA_URL=http://localhost:30091
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build

```bash
npm run build
npm start
```

## Usage Guide

### 1. Login/Register

- Navigate to `/login` or `/register`
- Create account or login with existing credentials
- Automatically redirected to dashboard

### 2. Create a Model

- Click "Create Model" button
- Enter model name and select type
- Model is created and you're redirected to model detail

### 3. Add Version

- Navigate to model detail page
- Click "Add Version"
- Enter version tag (e.g., v1.0.0)
- Version is created

### 4. Upload Model File

- Navigate to version detail page
- Drag and drop model file or click to select
- File uploads to S3
- Status updates automatically

### 5. Mark Version as Ready

- After upload, click "Mark as Ready"
- Version status changes to Ready
- Version can now be deployed

### 6. Deploy Model

- On version detail page, click "Deploy"
- Deployment is created in Kubernetes
- Deployment URL is displayed
- Can view deployment details

### 7. View Metrics

- Navigate to deployment detail page
- Grafana dashboard is embedded
- View real-time metrics:
  - Request rate
  - Latency percentiles
  - Resource usage
  - Pod status

## Future Enhancements

- [ ] Add toast notifications for actions
- [ ] Add loading skeletons
- [ ] Add error boundaries
- [ ] Add dark mode support
- [ ] Add model prediction testing UI
- [ ] Add deployment scaling controls
- [ ] Add bulk operations
- [ ] Add search and filtering
- [ ] Add export/import functionality

## Troubleshooting

### API Connection Issues

**Error**: Cannot connect to API

**Solution**:
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Verify API server is running: `curl http://localhost:8000/health`
- Check CORS settings in backend

### Authentication Issues

**Error**: Token not persisting

**Solution**:
- Check browser cookie settings
- Verify cookie name matches (`auth_token`)
- Check API response includes token

### Grafana Dashboard Not Loading

**Error**: Grafana iframe not displaying

**Solution**:
- Check `NEXT_PUBLIC_GRAFANA_URL` in `.env.local`
- Verify Grafana is running: `curl http://localhost:30091`
- Check Grafana allows embedding (configured in kube-prometheus-stack)
- Verify deployment variables match actual deployment

### File Upload Fails

**Error**: Upload fails or times out

**Solution**:
- Check file size (max 500MB)
- Verify file type is supported (.joblib, .pkl, .pickle)
- Check Minio is accessible
- Verify API endpoint is correct

## Next Steps

The frontend is now functional with:
- ✅ Authentication (login/register)
- ✅ Model Hub with status badges and polling
- ✅ Version management with file upload
- ✅ Deployment view with Grafana embedding
- ✅ Drag-and-drop upload UI

Additional features can be added incrementally based on user needs.


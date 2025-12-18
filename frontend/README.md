# KubeServe Frontend

Next.js frontend application for the KubeServe ML Inference Platform.

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS framework
- **React Query (TanStack Query)** - Server state management
- **Axios** - HTTP client
- **js-cookie** - Cookie management for JWT tokens

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- KubeServe API server running (default: http://localhost:8000)

### Installation

```bash
# Install dependencies
npm install
# or
yarn install
# or
pnpm install
```

### Environment Variables

Create a `.env.local` file in the `frontend` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GRAFANA_URL=http://localhost:30091
```

### Development

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── login/             # Login page
│   ├── register/          # Registration page
│   ├── dashboard/         # Main dashboard
│   └── models/            # Model management pages
├── components/            # React components
│   ├── Layout/           # Layout components
│   ├── Models/           # Model-related components
│   └── Deployments/      # Deployment components
├── lib/                   # Utilities and API client
│   ├── api.ts            # API client with axios
│   └── auth.ts           # Authentication utilities
└── hooks/                 # Custom React hooks
```

## Features

### Authentication
- Login page with JWT token storage
- Registration page
- Protected routes
- Automatic token refresh handling

### Model Hub
- List all user's models
- Create new models
- View model details and versions
- Status badges (Ready, Building, Failed)
- Real-time status polling

### Deployment View
- View deployment details
- Show live prediction URL
- Embed Grafana dashboards for metrics
- Deploy/undeploy models

### Upload UI
- Drag-and-drop file upload
- Model file validation
- Upload progress tracking

## API Integration

The frontend communicates with the KubeServe API at `/api/v1`:

- **Auth**: `/auth/register`, `/auth/login`, `/me`
- **Models**: `/models`, `/models/{id}`, `/models/{id}/versions`
- **Versions**: `/versions/{id}/upload`, `/versions/{id}/status`
- **Deployments**: `/versions/{id}/deployments`, `/deployments/{id}`

## Authentication Flow

1. User logs in via `/login`
2. JWT token stored in HTTP-only cookie
3. Token included in all API requests via axios interceptor
4. On 401 response, user redirected to login
5. Token persists across page refreshes

## Development Guidelines

- Use TypeScript for all new files
- Follow Next.js App Router conventions
- Use React Query for all server state
- Use Tailwind CSS for styling
- Keep components small and focused
- Use custom hooks for reusable logic

## Next Steps

- [ ] Complete Model Hub UI
- [ ] Add Deployment View with Grafana embedding
- [ ] Implement drag-and-drop upload
- [ ] Add error boundaries
- [ ] Add loading states
- [ ] Add toast notifications
- [ ] Add dark mode support


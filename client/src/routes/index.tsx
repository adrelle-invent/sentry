import { lazy, Suspense } from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { routes } from "./manifest";
import Layout from "@/components/Layout";
import { RefreshCw } from "lucide-react";

// Lazy-load page modules
const Dashboard = lazy(() => import("@/pages/dashboard/Index"));
const LogsExplorer = lazy(() => import("@/pages/logs/Index"));
const IssuesList = lazy(() => import("@/pages/issues/Index"));
const AlertsList = lazy(() => import("@/pages/alerts/Index"));
const ReportsList = lazy(() => import("@/pages/reports/Index"));
const Welcome = lazy(() => import("@/pages/welcome/Index"));
const Login = lazy(() => import("@/pages/auth/Login"));
const Signup = lazy(() => import("@/pages/auth/Signup"));
const VerifyEmail = lazy(() => import("@/pages/auth/VerifyEmail"));
const ForgotPassword = lazy(() => import("@/pages/auth/ForgotPassword"));
const ResetPassword = lazy(() => import("@/pages/auth/ResetPassword"));

const LoadingFallback = () => (
  <div className="flex h-64 w-full items-center justify-center">
    <RefreshCw className="h-8 w-8 animate-spin text-accent" />
  </div>
);

const router = createBrowserRouter(
  [
    {
      path: routes.welcome.path,
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <Welcome />
        </Suspense>
      ),
    },
    {
      path: routes.login.path,
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <Login />
        </Suspense>
      ),
    },
    {
      path: routes.signup.path,
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <Signup />
        </Suspense>
      ),
    },
    {
      path: routes.verifyEmail.path,
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <VerifyEmail />
        </Suspense>
      ),
    },
    {
      path: routes.forgotPassword.path,
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <ForgotPassword />
        </Suspense>
      ),
    },
    {
      path: routes.resetPassword.path,
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <ResetPassword />
        </Suspense>
      ),
    },
    {
      element: <Layout />,
      children: [
        {
          path: routes.dashboard.path,
          element: (
            <Suspense fallback={<LoadingFallback />}>
              <Dashboard />
            </Suspense>
          ),
        },
        {
          path: routes.events.path,
          element: (
            <Suspense fallback={<LoadingFallback />}>
              <LogsExplorer />
            </Suspense>
          ),
        },
        {
          path: routes.issues.path,
          element: (
            <Suspense fallback={<LoadingFallback />}>
              <IssuesList />
            </Suspense>
          ),
        },
        {
          path: routes.alerts.path,
          element: (
            <Suspense fallback={<LoadingFallback />}>
              <AlertsList />
            </Suspense>
          ),
        },
        {
          path: routes.reports.path,
          element: (
            <Suspense fallback={<LoadingFallback />}>
              <ReportsList />
            </Suspense>
          ),
        },
      ],
    },
  ],
  {
    basename: import.meta.env.BASE_URL,
  },
);

export function AppRouter() {
  return <RouterProvider router={router} />;
}

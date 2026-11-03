export const routes = {
  welcome: {
    name: "welcome",
    path: "/",
  },
  home: {
    name: "home",
    path: "/",
  },
  dashboard: {
    name: "dashboard",
    path: "/dashboard",
  },
  events: {
    name: "events.index",
    path: "/events",
  },
  issues: {
    name: "issues.index",
    path: "/issues",
  },
  alerts: {
    name: "alerts.index",
    path: "/alerts",
  },
  reports: {
    name: "reports.index",
    path: "/reports",
  },
  login: {
    name: "auth.login",
    path: "/login",
  },
  signup: {
    name: "auth.signup",
    path: "/signup",
  },
  verifyEmail: {
    name: "auth.verify-email",
    path: "/verify-email",
  },
  forgotPassword: {
    name: "auth.forgot-password",
    path: "/forgot-password",
  },
  resetPassword: {
    name: "auth.reset-password",
    path: "/reset-password",
  },
} as const;

export type RouteName = keyof typeof routes;

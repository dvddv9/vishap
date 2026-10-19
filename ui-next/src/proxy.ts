import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import { IS_DESKTOP } from "./lib/desktop";

/**
 * Clerk auth gate.
 *
 * Next.js 16 renamed the `middleware` file convention to `proxy` (same API,
 * the old name logs a deprecation warning), so this lives in `src/proxy.ts`.
 */
const isProtectedRoute = createRouteMatcher(["/analyze(.*)", "/report(.*)"]);

const webMiddleware = clerkMiddleware(async (auth, request) => {
  if (isProtectedRoute(request)) {
    // Redirects unauthenticated users to NEXT_PUBLIC_CLERK_SIGN_IN_URL ("/").
    await auth.protect();
  }
});

/**
 * Desktop build: the app is single-user and talks to `127.0.0.1:5001`, so there
 * is no Clerk session to protect. Left as a pass-through instead of deleting the
 * file so one source tree still serves the hosted deployment.
 */
const desktopMiddleware = () => NextResponse.next();

export default IS_DESKTOP ? desktopMiddleware : webMiddleware;

export const config = {
  matcher: [
    // Skip Next.js internals and static files unless they are found in search params.
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    // Always run for API routes.
    "/(api|trpc)(.*)",
  ],
};

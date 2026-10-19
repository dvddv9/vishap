"use client";

import { Suspense } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { SignInButton, UserButton, useUser } from "@clerk/nextjs";
import { ExternalLink, LayoutDashboard, Search } from "lucide-react";
import HarnessBadge from "@/components/HarnessBadge";
import { IS_DESKTOP } from "@/lib/desktop";

/** What the account slot should show. `local` = desktop build, no auth at all. */
type AuthState = "loading" | "signed-in" | "signed-out" | "local";

const NAV_LINKS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/analyze", label: "Analyze", icon: Search },
];

const DOCS_URL = "https://dvddv9.github.io/vishap/";

function NavbarInner({ auth }: { auth: AuthState }) {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/85 backdrop-blur">
      <nav className="mx-auto flex h-14 w-full max-w-6xl items-center gap-1 px-4">
        <Link
          href="/"
          className="mr-3 flex items-center gap-2 text-base font-semibold tracking-tight text-slate-100 transition-colors hover:text-white"
        >
          <span aria-hidden="true">🐉</span>
          <span>Vishap</span>
        </Link>

        {NAV_LINKS.map(({ href, label, icon: Icon }) => {
          const isActive = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              aria-current={isActive ? "page" : undefined}
              className={`flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm transition-colors ${
                isActive
                  ? "bg-slate-800/80 text-slate-100"
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
              }`}
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">{label}</span>
            </Link>
          );
        })}

        <a
          href={DOCS_URL}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-slate-400 transition-colors hover:bg-slate-800/50 hover:text-slate-200"
        >
          <ExternalLink className="h-4 w-4" aria-hidden="true" />
          <span className="hidden sm:inline">Docs</span>
        </a>

        <div className="ml-auto flex items-center gap-2">
          <HarnessBadge />
          {auth === "loading" ? (
            <span className="h-8 w-8" aria-hidden="true" />
          ) : auth === "signed-in" ? (
            <UserButton />
          ) : auth === "signed-out" ? (
            <SignInButton mode="modal">
              <button
                type="button"
                className="rounded-md bg-sky-500 px-3 py-1.5 text-sm font-medium text-slate-950 transition-colors hover:bg-sky-400"
              >
                Sign in
              </button>
            </SignInButton>
          ) : (
            // Desktop: no session, nothing to sign in to. A quiet badge keeps the
            // layout stable and tells the user which build they are running.
            <span className="rounded-md border border-slate-800 px-2 py-1 text-[0.7rem] font-medium uppercase tracking-wide text-slate-500">
              Local
            </span>
          )}
        </div>
      </nav>
    </header>
  );
}

/** Web build: the session comes from Clerk. */
function WebNavbar() {
  const { isLoaded, isSignedIn } = useUser();

  if (!isLoaded) return <NavbarInner auth="loading" />;
  return <NavbarInner auth={isSignedIn ? "signed-in" : "signed-out"} />;
}

export default function Navbar() {
  // Desktop build: ClerkProvider is not mounted, so its hooks must never run.
  if (IS_DESKTOP) return <NavbarInner auth="local" />;

  return (
    <Suspense fallback={<nav className="p-4">Loading...</nav>}>
      <WebNavbar />
    </Suspense>
  );
}

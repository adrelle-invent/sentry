import AppLogoIcon from "@/components/AppLogoIcon";

export default function Footer() {
    return (
        <footer className="mt-auto border-t border-border bg-background py-8">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                {/* Navigation */}
                <div className="flex flex-col items-center justify-between gap-6 pb-6 text-xs text-neutral-foreground md:flex-row">
                    <div className="flex items-center gap-2.5">
                        <div
                            className="flex aspect-square size-7 items-center justify-center rounded-lg text-white shadow-xs"
                            style={{ backgroundColor: "var(--primary)" }}
                        >
                            <AppLogoIcon className="size-4 fill-current text-white" />
                        </div>

                        <span className="text-sm font-bold text-foreground">
                            AD. Sentry
                        </span>

                        <span className="text-neutral-foreground">
                            | Observability Platform
                        </span>
                    </div>

                    <nav className="flex flex-wrap items-center justify-center gap-6 font-medium text-neutral-foreground">
                        <a
                            href="#hero"
                            className="transition-colors hover:text-foreground"
                        >
                            Overview
                        </a>

                        <a
                            href="#demo"
                            className="transition-colors hover:text-foreground"
                        >
                            Interactive Demo
                        </a>

                        <a
                            href="#how-it-works"
                            className="transition-colors hover:text-foreground"
                        >
                            How It Works
                        </a>

                        <a
                            href="#reliability"
                            className="transition-colors hover:text-foreground"
                        >
                            Reliability
                        </a>

                        <a
                            href="#deep-dive"
                            className="transition-colors hover:text-foreground"
                        >
                            Engineering Notes
                        </a>
                    </nav>
                </div>

                {/* Copyright & Tagline */}
                <div className="flex flex-col items-center justify-between gap-4 border-t border-border pt-6 text-xs text-neutral-foreground sm:flex-row">
                    <div className="flex items-center gap-2">
                        <span className="font-semibold text-neutral-foreground">
                            AD. Sentry
                        </span>

                        <span>
                            &copy; {new Date().getFullYear()} AD. Sentry Observability Systems
                        </span>
                    </div>

                    <p className="text-center text-neutral-foreground sm:text-right">
                        <em>
                            Built for stability. Designed for scale. Engineered
                            for reliability.
                        </em>
                    </p>
                </div>
            </div>
        </footer>
    );
}
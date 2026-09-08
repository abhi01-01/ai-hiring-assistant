import { DashboardClient } from "./components/DashboardClient";
import { ReachoutClient } from "./components/ReachoutClient";

// Force Next.js to dynamically render this page to avoid caching stale candidate lists
export const dynamic = "force-dynamic";

async function getCandidates() {
    try {
        const res = await fetch("/api/candidates/", {
            cache: "no-store",
        });

        if (!res.ok) {
            return [];
        }
        return res.json();
    } catch (error) {
        // Fails silently on the server if FastAPI is still booting,
        // returning an empty array so the UI can still render.
        console.error("Backend not ready yet.");
        return [];
    }
}

export default async function Page() {
  const initialCandidates = await getCandidates();

  return (
      <main className="container mx-auto py-10 space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Hiring Assistant</h1>
          <p className="text-muted-foreground">Manage outbound Voice AI outreach campaigns.</p>
        </div>

        <DashboardClient initialCandidates={initialCandidates} />
          <ReachoutClient />
      </main>
  );
}
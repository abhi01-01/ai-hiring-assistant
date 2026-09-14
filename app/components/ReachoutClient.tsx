"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type SearchCandidate = {
    apollo_id: string | null;
    name: string;
    email: string | null;
    phone_number: string | null;
    linkedin_url: string | null;
    title: string | null;
    company: string | null;
    skills: string[];
    metadata: {
        provider?: string;
        matched_keywords?: string[];
        apollo?: {
            person_id?: string;
        };
    };
};

export function ReachoutClient() {
    const [jd, setJd] = useState("");
    const [company, setCompany] = useState("Hunar AI");
    const [jobRole, setJobRole] = useState("Backend Engineer");
    const [candidates, setCandidates] = useState<SearchCandidate[]>([]);
    const [phoneOverrides, setPhoneOverrides] = useState<Record<string, string>>({});
    const [isSearching, setIsSearching] = useState(false);
    const [isCalling, setIsCalling] = useState<string | null>(null);
    const provider =
        candidates[0]?.metadata?.provider ?? "unknown";

    async function handleSearch() {
        setIsSearching(true);
        try {
            const res = await fetch("/api/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    job_description: jd,
                    company: company || null,
                    job_role: jobRole || null,
                    per_page: 10,
                }),
            });
            const body = await res.json();
            if (!res.ok) throw new Error(body?.detail?.message || body?.detail || "Search failed");
            setCandidates(body);
        } catch (error) {
            alert(error instanceof Error ? error.message : "Search failed");
        } finally {
            setIsSearching(false);
        }
    }

    async function handleReachout(candidate: SearchCandidate) {
        const phone = (phoneOverrides[candidate.apollo_id ?? candidate.name] || candidate.phone_number || "").trim();
        if (!phone) {
            alert("Enter the candidate's E.164 phone number before dialing.");
            return;
        }

        const key = candidate.apollo_id ?? candidate.name;
        setIsCalling(key);
        try {
            const res = await fetch("/api/candidates", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: candidate.name,
                    phone_number: phone,
                    email: candidate.email || null,
                    linkedin_url: candidate.linkedin_url || null,
                    skills: candidate.skills || [],
                    job_description: jd,
                    company: company || null,
                    job_role: jobRole || null,
                }),
            });
            const body = await res.json();
            if (!res.ok) throw new Error(body?.detail?.message || body?.detail || "Voice AI dispatch failed");
            alert(`Voice AI dispatched to ${candidate.name}. Call status: ${body.call?.status ?? "CREATED"}`);
        } catch (error) {
            alert(error instanceof Error ? error.message : "Voice AI dispatch failed");
        } finally {
            setIsCalling(null);
        }
    }

    return (
        <Card className="mt-8 border-dashed border-2">
            <CardHeader>
                <CardTitle>People Search & AI Reachout</CardTitle>
                <div className="text-sm text-muted-foreground">
                    Data source:{" "}
                    {provider === "apollo" ? "Apollo.io" : "Demo Dataset"}
                </div>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                    <input className="w-full p-3 border rounded-md bg-background" placeholder="Company name or domain (e.g. hunar.ai" value={company} onChange={(e) => setCompany(e.target.value)} />
                    <p className="mt-1 text-xs text-muted-foreground">A domain filters precisely; a plain name is only a best-effort hint.</p>
                    <input className="w-full p-3 border rounded-md bg-background" placeholder="Job role" value={jobRole} onChange={(e) => setJobRole(e.target.value)} />
                </div>
                <textarea
                    className="w-full min-h-[120px] p-3 border rounded-md bg-background"
                    placeholder="Paste the job description..."
                    value={jd}
                    onChange={(e) => setJd(e.target.value)}
                />
                <Button onClick={handleSearch} disabled={isSearching || jd.trim().length < 10}>
                    {isSearching ? "Finding Candidates..." : "Search Candidates"}
                </Button>

                {candidates.length > 0 && (
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Candidate</TableHead>
                                <TableHead>Role</TableHead>
                                <TableHead>LinkedIn</TableHead>
                                <TableHead>Phone</TableHead>
                                <TableHead>Action</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {candidates.map((candidate) => {
                                const key = candidate.apollo_id ?? candidate.name;
                                const phone = phoneOverrides[key] ?? candidate.phone_number ?? "";
                                return (
                                    <TableRow key={key}>
                                        <TableCell className="font-medium">
                                            <div>{candidate.name}</div>
                                            <div className="text-xs text-muted-foreground">
                                                {candidate.company || ""}
                                            </div>
                                        </TableCell>
                                        <TableCell>{candidate.title || "-"}</TableCell>
                                        <TableCell>
                                            {candidate.linkedin_url ? (
                                                <a href={candidate.linkedin_url} target="_blank" rel="noreferrer" className="text-blue-500 underline">Profile</a>
                                            ) : "-"}
                                        </TableCell>
                                        <TableCell>
                                            <input
                                                className="w-44 p-2 border rounded-md bg-background"
                                                placeholder="+919876543210"
                                                value={phone}
                                                onChange={(e) => setPhoneOverrides((current) => ({ ...current, [key]: e.target.value }))}
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Button size="sm" onClick={() => handleReachout(candidate)} disabled={isCalling === key || !phone}>
                                                {isCalling === key ? "Dialing..." : "Trigger Voice AI"}
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                )}
            </CardContent>
        </Card>
    );
}

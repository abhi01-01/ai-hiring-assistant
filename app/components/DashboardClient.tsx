"use client";

import { useEffect, useState, type SubmitEvent } from "react";
import { Candidate } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function DashboardClient({ initialCandidates }: { initialCandidates: Candidate[] }) {
    const [candidates, setCandidates] = useState<Candidate[]>(initialCandidates);
    const [isLoading, setIsLoading] = useState(false);

    async function refresh() {
        try {
            const response = await fetch("/api/candidates?limit=100", { cache: "no-store" });
            if (!response.ok) return;
            setCandidates(await response.json());
        } catch {
            // Keep the last known state when the API is temporarily unavailable.
        }
    }

    useEffect(() => {
        refresh();

        const interval = setInterval(() => {
            refresh();
        }, 10000);

        return () => {
            clearInterval(interval);
        };
    }, []);

    async function onSubmit(event: SubmitEvent<HTMLFormElement>) {
        event.preventDefault();

        const formElement = event.currentTarget;
        const form = new FormData(formElement);

        setIsLoading(true);

        try {
            const response = await fetch("/api/candidates", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: form.get("name"),
                    phone_number: form.get("phone_number"),
                    email: form.get("email") || null,
                    skills: [],
                }),
            });

            const body = await response.json();

            if (!response.ok) {
                throw new Error(
                    body?.detail?.message ||
                    body?.detail ||
                    "Unable to initiate outreach"
                );
            }

            formElement.reset();
            await refresh();
        } catch (error) {
            alert(
                error instanceof Error
                    ? error.message
                    : "Unable to initiate outreach"
            );
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="col-span-1 h-fit">
                <CardHeader>
                    <CardTitle>Initiate Outreach</CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={onSubmit} className="space-y-4">
                        <Input name="name" placeholder="Candidate Name" required disabled={isLoading} />
                        <Input name="phone_number" placeholder="Phone (+919988776655)" required disabled={isLoading} />
                        <Input name="email" placeholder="Email (Optional)" type="email" disabled={isLoading} />
                        <Button type="submit" className="w-full" disabled={isLoading}>
                            {isLoading ? "Initiating..." : "Call Candidate"}
                        </Button>
                    </form>
                </CardContent>
            </Card>

            <Card className="col-span-2">
                <CardHeader>
                    <CardTitle>Campaign Telemetry</CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Name</TableHead>
                                <TableHead>Contact</TableHead>
                                <TableHead>Call Status</TableHead>
                                <TableHead>Duration</TableHead>
                                <TableHead>Result</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {candidates.map((candidate) => {
                                const latestCall = candidate.calls?.[0];
                                return (
                                    <TableRow key={candidate.id}>
                                        <TableCell className="font-medium">{candidate.name}</TableCell>
                                        <TableCell>{candidate.phone_number}</TableCell>
                                        <TableCell>
                                            <Badge variant={latestCall?.status === "COMPLETED" ? "default" : "secondary"}>
                                                {latestCall?.status || "PENDING"}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>{latestCall?.duration_seconds ?? 0}s</TableCell>
                                        <TableCell>{latestCall?.result || "-"}</TableCell>
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}

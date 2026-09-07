export interface CallLog {
    id: string;
    external_call_id: string | null;
    status: string;
    transcript: string | null;
    summary: string | null;
    duration_seconds: number | null;
    result: string | null;
    recording_url: string | null;
    created_at: string;
}

export interface Candidate {
    id: string;
    name: string;
    phone_number: string;
    email: string | null;
    linkedin_url: string | null;
    skills: string[];
    created_at: string;
    calls: CallLog[];
}

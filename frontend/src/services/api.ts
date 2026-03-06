const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function toJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export type ScrapedJob = {
  title?: string | null;
  company?: string | null;
  location?: string | null;
  experience?: string | null;
  skills?: string[];
  job_url?: string | null;
  description?: string | null;
  ai_mentions?: string[];
  query_role?: string;
  query_city?: string;
};

export async function getHiringTrendsApi(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/dashboard/hiring-trends`);
  return toJson<any[]>(res);
}

export async function getSkillGapApi(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/dashboard/skill-gap`);
  return toJson<any[]>(res);
}

export async function getSkillTrendsApi(): Promise<{ rising_skills: any[], declining_skills: any[] }> {
  const res = await fetch(`${API_BASE}/dashboard/skill-trends`);
  return toJson<{ rising_skills: any[], declining_skills: any[] }>(res);
}

export async function getVulnerabilityApi(): Promise<Record<string, number>> {
  const res = await fetch(`${API_BASE}/dashboard/vulnerability`);
  return toJson<Record<string, number>>(res);
}

export async function getDashboardStatsApi(): Promise<{ total_jobs: number, top_city: string, most_in_demand_skill: string, most_common_role: string }> {
  const res = await fetch(`${API_BASE}/dashboard/stats`);
  return toJson<{ total_jobs: number, top_city: string, most_in_demand_skill: string, most_common_role: string }>(res);
}

export async function getLatestJobsApi(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/dashboard/latest-jobs`);
  return toJson<any[]>(res);
}

export async function getTopCitiesApi(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/dashboard/top-cities`);
  return toJson<any[]>(res);
}

export async function getIndustryDistributionApi(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/dashboard/industry-distribution`);
  return toJson<any[]>(res);
}

export async function getTopRolesApi(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/dashboard/top-roles`);
  return toJson<any[]>(res);
}

export async function getRoleDistributionApi(city: string): Promise<any[]> {
  const res = await fetch(`${API_BASE}/dashboard/city-role-distribution?city=${encodeURIComponent(city)}`);
  return toJson<any[]>(res);
}

export async function getCitySpreadApi(role: string): Promise<any[]> {
  const res = await fetch(`${API_BASE}/dashboard/role-city-distribution?role=${encodeURIComponent(role)}`);
  return toJson<any[]>(res);
}

export async function getScrapedJobsApi(
  refresh = true
): Promise<{
  total: number;
  jobs: ScrapedJob[];
  scrape_error?: string | null;
  scrape_stats?: Record<string, unknown> | null;
}> {
  const res = await fetch(`${API_BASE}/dashboard/scraped-jobs?refresh=${refresh ? 'true' : 'false'}`);
  return toJson<{
    total: number;
    jobs: ScrapedJob[];
    scrape_error?: string | null;
    scrape_stats?: Record<string, unknown> | null;
  }>(res);
}

export type WorkerAnalyzePayload = {
  job_title: string;
  city: string;
  experience_years: number;
  writeup: string;
};

export type WorkerAnalyzeResponse = {
  parsed_profile: {
    role: string;
    city: string;
    experience: number;
    skills: string[];
  };
  risk_score: number;
  reskilling_path: {
    target_role: string;
    plan: string[];
  };
};

export async function analyzeWorkerApi(data: WorkerAnalyzePayload): Promise<WorkerAnalyzeResponse> {
  const res = await fetch(`${API_BASE}/worker/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return toJson<WorkerAnalyzeResponse>(res);
}

export type ChatbotQueryPayload = {
  worker_profile: Record<string, unknown>;
  question: string;
};

export async function chatbotQueryApi(data: ChatbotQueryPayload): Promise<{ response: string }> {
  const res = await fetch(`${API_BASE}/chatbot/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return toJson<{ response: string }>(res);
}

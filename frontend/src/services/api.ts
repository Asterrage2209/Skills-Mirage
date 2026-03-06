const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem('token');
  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return fetch(url, { ...options, headers });
}

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
  const res = await fetchWithAuth(`${API_BASE}/dashboard/hiring-trends`);
  return toJson<any[]>(res);
}

export async function getSkillGapApi(): Promise<any[]> {
  const res = await fetchWithAuth(`${API_BASE}/dashboard/skill-gap`);
  return toJson<any[]>(res);
}

export async function getSkillTrendsApi(year?: number): Promise<{ rising_skills: any[], declining_skills: any[] }> {
  const query = typeof year === 'number' ? `?year=${year}` : '';
  const res = await fetchWithAuth(`${API_BASE}/dashboard/skill-trends${query}`);
  return toJson<{ rising_skills: any[], declining_skills: any[] }>(res);
}

export async function getSkillTrendYearsApi(): Promise<number[]> {
  const res = await fetchWithAuth(`${API_BASE}/dashboard/skill-trend-years`);
  const payload = await toJson<{ years: number[] }>(res);
  return payload.years || [];
}

export async function getVulnerabilityApi(): Promise<any[]> {
  const res = await fetchWithAuth(`${API_BASE}/dashboard/vulnerability`);
  return toJson<any[]>(res);
}

export async function getVulnerabilityRegionsApi(): Promise<any> {
  const res = await fetchWithAuth(`${API_BASE}/dashboard/vulnerability-regions`);
  return toJson<any>(res);
}

export async function getDashboardStatsApi(): Promise<{ total_jobs: number, top_city: string, most_in_demand_skill: string, most_common_role: string }> {
  const res = await fetchWithAuth(`${API_BASE}/dashboard/stats`);
  return toJson<{ total_jobs: number, top_city: string, most_in_demand_skill: string, most_common_role: string }>(res);
}

export async function getLatestJobsApi(): Promise<any[]> {
  const res = await fetchWithAuth(`${API_BASE}/dashboard/latest-jobs`);
  return toJson<any[]>(res);
}

export async function getTopCitiesApi(): Promise<any[]> {
  const res = await fetchWithAuth(`${API_BASE}/dashboard/top-cities`);
  return toJson<any[]>(res);
}

export async function getIndustryDistributionApi(): Promise<any[]> {
  const res = await fetchWithAuth(`${API_BASE}/dashboard/industry-distribution`);
  return toJson<any[]>(res);
}

export async function getTopRolesApi(): Promise<any[]> {
  const res = await fetchWithAuth(`${API_BASE}/dashboard/top-roles`);
  return toJson<any[]>(res);
}

export async function getRoleDistributionApi(city: string): Promise<any[]> {
  const res = await fetchWithAuth(`${API_BASE}/dashboard/city-role-distribution?city=${encodeURIComponent(city)}`);
  return toJson<any[]>(res);
}

export async function getCitySpreadApi(role: string): Promise<any[]> {
  const res = await fetchWithAuth(`${API_BASE}/dashboard/role-city-distribution?role=${encodeURIComponent(role)}`);
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
  const res = await fetchWithAuth(`${API_BASE}/dashboard/scraped-jobs?refresh=${refresh ? 'true' : 'false'}`);
  return toJson<{
    total: number;
    jobs: ScrapedJob[];
    scrape_error?: string | null;
    scrape_stats?: Record<string, unknown> | null;
  }>(res);
}

export type WorkerAnalyzePayload = {
  job_role: string;
  city: string;
  years_of_experience: number;
  role_description: string;
  skills: string[];
};

export type WorkerProfileResponse = {
  job_role: string | null;
  city: string | null;
  years_of_experience: number | null;
  role_description: string | null;
  skills: string[];
  risk_score: number | null;
  ai_vulnerability: number | null;
  reskilling_path: {
    target_role: string;
    plan: string[];
  } | null;
}

export async function getWorkerProfileApi(): Promise<WorkerProfileResponse> {
  const res = await fetchWithAuth(`${API_BASE}/worker/profile`);
  return toJson<WorkerProfileResponse>(res);
}

export type WorkerAnalyzeResponse = {
  parsed_profile: {
    role: string;
    city: string;
    experience: number;
    skills: string[];
  };
  risk_score: number;
  ai_vulnerability: number;
  reskilling_path: {
    target_role: string;
    plan: string[];
  };
};

export async function analyzeWorkerApi(data: WorkerAnalyzePayload): Promise<WorkerAnalyzeResponse> {
  const res = await fetchWithAuth(`${API_BASE}/worker/profile`, {
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
  const res = await fetchWithAuth(`${API_BASE}/chatbot/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return toJson<{ response: string }>(res);
}

export async function signupApi(data: any): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return toJson<{ message: string }>(res);
}

export async function loginApi(data: any): Promise<{ access_token: string, token_type: string }> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return toJson<{ access_token: string, token_type: string }>(res);
}

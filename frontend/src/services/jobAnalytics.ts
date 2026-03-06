import {
  getScrapedJobsApi,
  getVulnerabilityApi,
  getVulnerabilityRegionsApi,
  getHiringTrendsApi,
  getSkillTrendsApi,
  getSkillTrendYearsApi,
  getDashboardStatsApi,
  getLatestJobsApi,
  getTopCitiesApi,
  getIndustryDistributionApi,
  getTopRolesApi,
  getRoleDistributionApi,
  getCitySpreadApi,
  getSkillGapApi
} from './api';


export const refreshJobsData = async () => {
  // Can just trigger a scrape or just return true, handled by generic refresh now
  await getScrapedJobsApi(true);
};

export const getDashboardSummary = async () => {
  const stats = await getDashboardStatsApi();
  return {
    totalJobs: stats.total_jobs,
    topCity: stats.top_city,
    topSkill: stats.most_in_demand_skill,
    topRole: stats.most_common_role,
  };
};

export const getHiringTrends = async () => {
  const trends = await getHiringTrendsApi();
  // Map from backend { month, job_count } to { name, value }
  return trends.map((t: any) => ({
    name: t.month,
    value: t.job_count
  }));
};

export const getTopSkills = async (year?: number) => {
  const trends = await getSkillTrendsApi(year);
  // We can combine rising_skills for top skills display, or just use rising
  return trends.rising_skills.map((s: any) => ({
    name: s.name,
    dev: parseInt(s.growth.replace('+', '')) || 0,
  }));
};

export const getSkillTrends = async (year?: number) => {
  return await getSkillTrendsApi(year);
};

export const getSkillTrendYears = async () => {
  return await getSkillTrendYearsApi();
};

export const getSkillGapApiWrapper = async () => {
  return await getSkillGapApi();
};

export const getVulnerabilityRows = async () => {
  return await getVulnerabilityApi();
};

export const getVulnerabilityRegions = async () => {
  const vulnerability = await getVulnerabilityRegionsApi();
  return Object.entries(vulnerability.region_risks || {})
    .map(([city, score]) => ({
      name: city,
      risk: Number(score)
    }))
    .sort((a, b) => b.risk - a.risk);
};

export const getLatestJobs = async () => {
  return await getLatestJobsApi();
};

export const getTopCities = async () => {
  return await getTopCitiesApi();
};

export const getIndustryDistribution = async () => {
  return await getIndustryDistributionApi();
};

export const getTopRoles = async () => {
  return await getTopRolesApi();
};

export const getRoleDistribution = async (city: string) => {
  return await getRoleDistributionApi(city);
};

export const getCitySpread = async (role: string) => {
  return await getCitySpreadApi(role);
};

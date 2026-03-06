import Papa from 'papaparse';
// @ts-ignore
import jobsCsvUrl from '../data/naukri_jobs.csv?url';

export interface JobRecord {
    jobtitle: string;
    skills: string[];
    city: string;
    industry: string;
    experience: string;
    company: string;
    postdate: Date;
    month: string;
    year: string;
}

export const loadJobs = (): Promise<JobRecord[]> => {
    return new Promise((resolve, reject) => {
        Papa.parse(jobsCsvUrl, {
            download: true,
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
                const rawData = results.data as any[];

                const processJobs: JobRecord[] = rawData.map((row): JobRecord => {
                    const jobtitle = (row.jobtitle || '').toLowerCase().trim();
                    const loc = row.joblocation_address || '';
                    const city = loc.split(',')[0].trim();
                    const rawSkills = row.skills || '';
                    const skills = Array.from<string>(new Set(
                        rawSkills.split(',')
                            .map((s: string) => s.toLowerCase().trim())
                            .filter((s: string) => s.length > 0)
                    ));
                    const dateStr = row.postdate || '';
                    let postdate = new Date(0);
                    let month = '';
                    let year = '';
                    if (dateStr) {
                        const parsedDate = new Date(dateStr);
                        if (!isNaN(parsedDate.getTime())) {
                            postdate = parsedDate;
                            month = postdate.toLocaleString('default', { month: 'short' });
                            year = postdate.getFullYear().toString();
                        }
                    }
                    return {
                        jobtitle,
                        skills,
                        city,
                        industry: (row.industry || '').trim(),
                        experience: row.experience || '',
                        company: row.company || '',
                        postdate,
                        month,
                        year
                    };
                }).filter(job => job.jobtitle && job.city);

                resolve(processJobs);
            },
            error: (error) => {
                console.error("Error parsing CSV:", error);
                reject(error);
            }
        });
    });
};

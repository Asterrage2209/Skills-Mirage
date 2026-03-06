import { useState, useEffect } from 'react';
import { getLatestJobs } from '../../services/jobAnalytics';
import { Clock } from 'lucide-react';

const LatestJobs = ({ refreshTrigger = 0 }: { refreshTrigger?: number }) => {
    const [jobs, setJobs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let mounted = true;
        const load = async () => {
            if (mounted) setLoading(true); // show loader when triggered
            try {
                const data = await getLatestJobs();
                if (mounted) {
                    setJobs(data);
                    setLoading(false);
                }
            } catch (err) {
                console.error("Failed to load latest jobs:", err);
                if (mounted) setLoading(false);
            }
        };
        load();
        return () => { mounted = false; };
    }, [refreshTrigger]);

    if (loading) {
        return <div className="card mt-8 p-4 text-center text-textSecondary">Loading jobs...</div>;
    }

    return (
        <div className="card mt-8">
            <div className="flex items-center gap-2 mb-6">
                <div className="p-2 rounded-lg bg-blue-500/10">
                    <Clock className="w-5 h-5 text-blue-400" />
                </div>
                <h3 className="text-lg font-bold text-white">Latest Scraped Jobs</h3>
            </div>

            <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
                <table className="w-full text-left border-collapse relative">
                    <thead className="sticky top-0 bg-secondary z-10">
                        <tr className="border-b border-gray-800 text-textSecondary text-sm font-medium">
                            <th className="pb-3 pr-4 whitespace-nowrap bg-secondary">Job Title</th>
                            <th className="pb-3 pr-4 whitespace-nowrap bg-secondary">Company</th>
                            <th className="pb-3 pr-4 whitespace-nowrap bg-secondary">Location</th>
                            <th className="pb-3 pr-4 whitespace-nowrap bg-secondary">Experience</th>
                            <th className="pb-3 pr-4 whitespace-nowrap bg-secondary">Skills</th>
                            <th className="pb-3 whitespace-nowrap bg-secondary">Posted Date</th>
                        </tr>
                    </thead>
                    <tbody className="text-sm">
                        {jobs.map((job, idx) => (
                            <tr key={idx} className="border-b border-gray-800/50 hover:bg-gray-800/20 transition-colors">
                                <td className="py-4 pr-4 text-white font-medium max-w-[200px] truncate" title={job.jobtitle}>
                                    {job.jobtitle}
                                </td>
                                <td className="py-4 pr-4 text-gray-300 max-w-[150px] truncate" title={job.company}>
                                    {job.company}
                                </td>
                                <td className="py-4 pr-4 text-gray-400 capitalize whitespace-nowrap">
                                    {job.location || job.city || 'Unknown'}
                                </td>
                                <td className="py-4 pr-4 text-gray-400 whitespace-nowrap">
                                    {job.experience || 'N/A'}
                                </td>
                                <td className="py-4 pr-4 text-gray-400 max-w-[200px] truncate" title={job.skills}>
                                    {job.skills || 'N/A'}
                                </td>
                                <td className="py-4 text-gray-500 whitespace-nowrap">
                                    {job.postdate?.split(' ')[0] || job.postdate}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {jobs.length === 0 && (
                    <div className="text-center py-8 text-gray-500">No scraped jobs available yet</div>
                )}
            </div>
        </div>
    );
};

export default LatestJobs;

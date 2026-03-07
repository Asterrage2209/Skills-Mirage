import { useState, useEffect } from 'react';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    BarChart, Bar
} from 'recharts';
import { Users, Building2, BrainCircuit, ShieldAlert, ArrowUpRight, ArrowDownRight, RefreshCw } from 'lucide-react';
import { getHiringTrends, getTopSkills, getDashboardSummary, refreshJobsData, getSkillTrendYears } from '../../services/jobAnalytics';
import LatestJobs from './LatestJobs';
import DynamicInsights from './DynamicInsights';

// Helper function to format strings to Title Case for display
const formatDisplayName = (name: string) => {
    if (!name) return name;
    // Keep IT or AI uppercased if they appear as words
    return name.split(' ')
        .map(word => {
            const upper = word.toUpperCase();
            if (upper === 'IT' || upper === 'AI' || upper === 'ERP' || upper === 'QA') return upper;
            return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
        })
        .join(' ');
};

const CustomOverviewTick = (props: any) => {
    const { x, y, payload } = props;
    const value = payload.value || "";
    const truncated = value.length > 15 ? value.substring(0, 15) + "..." : value;

    return (
        <g transform={`translate(${x},${y})`}>
            <text
                x={0}
                y={0}
                dy={16}
                textAnchor="end"
                fill="#9ca3af"
                fontSize={12}
                transform="rotate(-90)"
            >
                {truncated}
            </text>
        </g>
    );
};

const StatCard = ({ title, value, trend, trendValue, icon: Icon, color }: any) => {
    const isUp = trend === 'up';

    return (
        <div className="card flex flex-col h-full">
            <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-xl bg-${color}-500/10`}>
                    <Icon className={`w-6 h-6 text-${color}-400`} />
                </div>
                <div className={`flex items-center gap-1 text-sm font-medium px-2 py-1 rounded-full ${isUp ? 'text-green-400 bg-green-400/10' : 'text-red-400 bg-red-400/10'}`}>
                    {isUp ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                    {trendValue}
                </div>
            </div>
            <h4 className="text-textSecondary text-sm font-medium mb-1">{title}</h4>
            <div className="flex-1 flex items-center">
                <p className="text-3xl font-bold text-white tracking-tight break-words line-clamp-2 overflow-hidden" title={value}>
                    {value}
                </p>
            </div>
        </div>
    );
};

const Overview = () => {
    const [summary, setSummary] = useState({ totalJobs: 0, topCity: '-', topSkill: '-', topRole: '-' });
    const [hiringData, setHiringData] = useState<any[]>([]);
    const [skillsData, setSkillsData] = useState<any[]>([]);
    const [skillYears, setSkillYears] = useState<number[]>([]);
    const [selectedSkillYear, setSelectedSkillYear] = useState<number | 'all' | null>(null);
    const [loading, setLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [refreshTrigger, setRefreshTrigger] = useState(0);

    useEffect(() => {
        let mounted = true;
        const loadData = async () => {
            try {
                const [sum, hire, years] = await Promise.all([
                    getDashboardSummary(),
                    getHiringTrends(),
                    getSkillTrendYears(),
                ]);

                if (mounted) {
                    setSummary(sum);
                    setHiringData(hire);
                    setSkillYears(years);
                    setSelectedSkillYear(years.length > 0 ? years[0] : 'all');
                    setLoading(false);
                }
            } catch (err) {
                console.error("Error loading data:", err);
                if (mounted) setLoading(false);
            }
        };
        loadData();
        return () => { mounted = false; };
    }, []);

    useEffect(() => {
        let mounted = true;

        const loadSkills = async () => {
            if (selectedSkillYear === null) return;
            try {
                const year = selectedSkillYear === 'all' ? undefined : selectedSkillYear;
                const skills = await getTopSkills(year);
                if (mounted) {
                    setSkillsData(skills);
                }
            } catch (err) {
                console.error('Error loading top skills:', err);
            }
        };

        loadSkills();
        return () => { mounted = false; };
    }, [selectedSkillYear]);

    const handleRefresh = async () => {
        setIsRefreshing(true);
        try {
            await refreshJobsData();
            const [sum, hire, years] = await Promise.all([
                getDashboardSummary(),
                getHiringTrends(),
                getSkillTrendYears(),
            ]);

            const nextYear =
                selectedSkillYear !== null && selectedSkillYear !== 'all' && years.includes(selectedSkillYear)
                    ? selectedSkillYear
                    : (years.length > 0 ? years[0] : 'all');

            const skills = await getTopSkills(nextYear === 'all' ? undefined : nextYear);

            setSummary(sum);
            setHiringData(hire);
            setSkillYears(years);
            setSelectedSkillYear(nextYear);
            setSkillsData(skills);
            setRefreshTrigger(prev => prev + 1);
        } catch (err) {
            console.error("Error refreshing data:", err);
        } finally {
            setIsRefreshing(false);
        }
    };

    if (loading) {
        return <div className="p-8 text-center text-white">Loading data from dataset...</div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-1">Dashboard</h1>
                    <p className="text-textSecondary text-sm">Welcome to your workspace. Here's what's happening today.</p>
                </div>
                <button
                    onClick={handleRefresh}
                    disabled={isRefreshing || loading}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                    {isRefreshing ? 'Refreshing Data...' : 'Refresh Data'}
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard title="Total Jobs Scraped" value={summary.totalJobs.toLocaleString()} trend="up" trendValue="Active" icon={Users} color="blue" />
                <StatCard title="Top Hiring City" value={formatDisplayName(summary.topCity)} trend="up" trendValue="Leading" icon={Building2} color="purple" />
                <StatCard title="Most In Demand Skill" value={formatDisplayName(summary.topSkill)} trend="up" trendValue="Rising" icon={BrainCircuit} color="green" />
                <StatCard title="Most Common Role" value={formatDisplayName(summary.topRole)} trend="up" trendValue="Popular" icon={ShieldAlert} color="red" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
                <div className="card">
                    <h3 className="text-lg font-bold text-white mb-6">Hiring Trends Over Time</h3>
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={hiringData}>
                                <defs>
                                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                                <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#111827', borderColor: '#ffffff10', borderRadius: '8px' }}
                                    itemStyle={{ color: '#e5e7eb' }}
                                    labelFormatter={(label) => `Month: ${label}`}
                                    formatter={(value) => [value, 'Job Postings']}
                                />
                                <Area type="monotone" dataKey="value" name="Job Postings" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorValue)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="card">
                    <div className="flex items-center justify-between mb-6 gap-3">
                        <h3 className="text-lg font-bold text-white">Top Skills Demand</h3>
                        <select
                            className="bg-secondary border border-white/10 text-white text-sm rounded-lg px-3 py-2 appearance-none focus:outline-none focus:ring-2 focus:ring-accent/50 cursor-pointer"
                            value={selectedSkillYear === null ? 'all' : selectedSkillYear}
                            onChange={(e) => {
                                const value = e.target.value;
                                setSelectedSkillYear(value === 'all' ? 'all' : Number(value));
                            }}
                        >
                            <option value="all">All years</option>
                            {skillYears.map((year) => (
                                <option key={year} value={year}>{year}</option>
                            ))}
                        </select>
                    </div>
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={skillsData} margin={{ bottom: 85 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                                <XAxis
                                    dataKey="name"
                                    stroke="#9ca3af"
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                    interval={0}
                                    tick={<CustomOverviewTick />}
                                />
                                <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                                <Tooltip
                                    cursor={{ fill: '#ffffff05' }}
                                    contentStyle={{ backgroundColor: '#111827', borderColor: '#ffffff10', borderRadius: '8px' }}
                                    labelFormatter={(label) => `Skill: ${label}`}
                                    formatter={(value, _name, props) => [value, props.payload.name]}
                                />
                                <Bar dataKey="dev" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            <LatestJobs refreshTrigger={refreshTrigger} />
            <DynamicInsights refreshTrigger={refreshTrigger} />
        </div>
    );
};

export default Overview;

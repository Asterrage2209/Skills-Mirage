import { useState, useEffect } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
    BarChart, Bar, PieChart, Pie, Cell
} from 'recharts';
import { Filter } from 'lucide-react';
import { getHiringTrends, getTopCities, getIndustryDistribution } from '../../services/jobAnalytics';

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f43f5e', '#facc15'];
const CITY_OPTIONS = [
    'all',
    'bangalore',
    'hyderabad',
    'pune',
    'mumbai',
    'delhi',
    'chennai',
    'ahmedabad',
    'indore',
    'jaipur',
    'lucknow',
    'kolkata',
    'noida',
    'gurgaon',
    'coimbatore',
    'kochi',
    'trivandrum',
    'nagpur',
    'bhopal',
    'surat',
    'vadodara',
    'patna',
    'chandigarh',
    'bhubaneswar',
    'visakhapatnam',
    'vijayawada',
    'nashik',
    'mysore',
    'madurai',
    'raipur',
    'dehradun',
];

const formatCityName = (city: string) => {
    if (!city) return '';
    // Handle cases like "ncr/bangalore" by taking just the primary token
    let mainCity = city.split('/')[0].split(',')[0].trim();
    if (mainCity.toLowerCase() === 'delhi ncr' || mainCity.toLowerCase() === 'ncr') return 'Delhi NCR';
    return mainCity.charAt(0).toUpperCase() + mainCity.slice(1).toLowerCase();
};

const HiringTrends = () => {
    const [timeRange, setTimeRange] = useState('30days');
    const [city, setCity] = useState('all');

    const [trendData, setTrendData] = useState<any[]>([]);
    const [cityData, setCityData] = useState<any[]>([]);
    const [sectorData, setSectorData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let mounted = true;
        const loadData = async () => {
            try {
                // In a real app we would pass `timeRange` and `city` to filtering
                const trends = await getHiringTrends();
                const cities = await getTopCities();
                const sectors = await getIndustryDistribution();

                if (mounted) {
                    const filteredTrends = city === 'all'
                        ? trends
                        : trends.filter((t) => t.name.toLowerCase() === city);
                    const filteredCities = city === 'all'
                        ? cities
                        : cities.filter((c) => c.name.toLowerCase() === city);

                    // Adapt the trends to include 'active' if needed, or just map 'value' to 'jobs'
                    const mappedTrends = filteredTrends.map(t => ({ name: t.name, jobs: t.value, active: Math.round(t.value * 0.8) }));

                    // Format city display names right before setting state
                    const displayCities = filteredCities.map(c => ({ name: formatCityName(c.name), demand: c.demand }));

                    setTrendData(mappedTrends);
                    setCityData(displayCities);
                    setSectorData(sectors);
                    setLoading(false);
                }
            } catch (err) {
                console.error("Error loading hiring trends:", err);
                if (mounted) setLoading(false);
            }
        };
        loadData();
        return () => { mounted = false; };
    }, [city, timeRange]);

    if (loading) {
        return <div className="p-8 text-center text-white">Loading hiring trends...</div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-1">Hiring Trends</h1>
                    <p className="text-textSecondary text-sm">Analyze job posting frequency across regions and sectors.</p>
                </div>

                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Filter className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" />
                        <select
                            className="bg-secondary border border-white/10 text-white text-sm rounded-lg pl-9 pr-4 py-2 appearance-none focus:outline-none focus:ring-2 focus:ring-accent/50 cursor-pointer"
                            value={city}
                            onChange={(e) => setCity(e.target.value)}
                        >
                            {CITY_OPTIONS.map((c) => (
                                <option key={c} value={c}>
                                    {c === 'all' ? 'All Cities' : formatCityName(c)}
                                </option>
                            ))}
                        </select>
                    </div>

                    <select
                        className="bg-secondary border border-white/10 text-white text-sm rounded-lg px-4 py-2 appearance-none focus:outline-none focus:ring-2 focus:ring-accent/50 cursor-pointer"
                        value={timeRange}
                        onChange={(e) => setTimeRange(e.target.value)}
                    >
                        <option value="7days">Past 7 days</option>
                        <option value="30days">Past 30 days</option>
                        <option value="90days">Past 90 days</option>
                        <option value="1year">Past 1 year</option>
                    </select>
                </div>
            </div>

            <div className="card mb-6">
                <h3 className="text-lg font-bold text-white mb-6">Aggregate Job Postings</h3>
                <div className="h-[350px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={trendData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                            <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis yAxisId="left" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis yAxisId="right" orientation="right" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                            <RechartsTooltip
                                contentStyle={{ backgroundColor: '#111827', borderColor: '#ffffff10', borderRadius: '8px' }}
                                itemStyle={{ color: '#e5e7eb' }}
                            />
                            <Line yAxisId="left" type="monotone" dataKey="jobs" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                            <Line yAxisId="right" type="monotone" dataKey="active" stroke="#8b5cf6" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="card">
                    <h3 className="text-lg font-bold text-white mb-6">City Demand Comparison</h3>
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={cityData} layout="vertical" margin={{ left: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" horizontal={false} />
                                <XAxis type="number" stroke="#9ca3af" fontSize={11} tickLine={false} axisLine={false} />
                                <YAxis dataKey="name" type="category" stroke="#9ca3af" fontSize={11} tickLine={false} axisLine={false} width={85} />
                                <RechartsTooltip
                                    cursor={{ fill: '#ffffff05' }}
                                    contentStyle={{ backgroundColor: '#111827', borderColor: '#ffffff10', borderRadius: '8px' }}
                                />
                                <Bar dataKey="demand" fill="#10b981" radius={[0, 4, 4, 0]} barSize={24} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="card">
                    <h3 className="text-lg font-bold text-white mb-6">Sector Distribution</h3>

                    <div className="h-[300px] w-full flex items-center justify-between">

                        {/* Pie Chart */}
                        <div className="w-[60%] h-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={sectorData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={80}
                                        outerRadius={110}
                                        paddingAngle={5}
                                        dataKey="value"
                                        stroke="none"
                                    >
                                        {sectorData.map((_, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>

                                    <RechartsTooltip
                                        contentStyle={{
                                            backgroundColor: '#111827',
                                            borderColor: '#ffffff10',
                                            borderRadius: '8px',
                                            color: '#fff'
                                        }}
                                        itemStyle={{ color: '#e5e7eb' }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Legend */}
                        <div className="flex flex-col gap-3 w-[40%] pl-4">
                            {sectorData.map((entry, index) => (
                                <div key={entry.name} className="flex items-center gap-2">
                                    <div
                                        className="w-3 h-3 rounded-full"
                                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                                    />
                                    <span className="text-sm text-textSecondary">{entry.name}</span>
                                </div>
                            ))}
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
};

export default HiringTrends;

import { useState, useEffect } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
    BarChart, Bar
} from 'recharts';
import { getHiringTrends, getTopCities } from '../../services/jobAnalytics';

const formatCityName = (city: string) => {
    if (!city) return '';
    // Handle cases like "ncr/bangalore" by taking just the primary token
    let mainCity = city.split('/')[0].split(',')[0].trim();
    if (mainCity.toLowerCase() === 'delhi ncr' || mainCity.toLowerCase() === 'ncr') return 'Delhi NCR';
    return mainCity.charAt(0).toUpperCase() + mainCity.slice(1).toLowerCase();
};

const HiringTrends = () => {

    const [trendData, setTrendData] = useState<any[]>([]);
    const [cityData, setCityData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let mounted = true;
        const loadData = async () => {
            try {
                // In a real app we would pass `timeRange` and `city` to filtering
                const trends = await getHiringTrends();
                const cities = await getTopCities();

                if (mounted) {
                    // Adapt the trends to include 'active' if needed, or just map 'value' to 'jobs'
                    const mappedTrends = trends.map((t: any) => ({ name: t.name, jobs: t.value, active: Math.round(t.value * 0.8) }));

                    // Format city display names right before setting state
                    const displayCities = cities.map((c: any) => ({ name: formatCityName(c.name), demand: c.demand }));

                    setTrendData(mappedTrends);
                    setCityData(displayCities);
                    setLoading(false);
                }
            } catch (err) {
                console.error("Error loading hiring trends:", err);
                if (mounted) setLoading(false);
            }
        };
        loadData();
        return () => { mounted = false; };
    }, []);

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

                <div>
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
                                labelFormatter={(label) => `Period: ${label}`}
                                formatter={(value, name) => {
                                    if (name === 'jobs') return [value, 'Job Postings'];
                                    if (name === 'active') return [value, 'Estimated Active Roles'];
                                    return [value, String(name)];
                                }}
                            />
                            <Line yAxisId="left" type="monotone" dataKey="jobs" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                            <Line yAxisId="right" type="monotone" dataKey="active" stroke="#8b5cf6" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="card mb-6">
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
                                labelFormatter={(label) => `City: ${label}`}
                                formatter={(value) => [value, 'Job Demand']}
                            />
                            <Bar dataKey="demand" fill="#10b981" radius={[0, 4, 4, 0]} barSize={24} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default HiringTrends;

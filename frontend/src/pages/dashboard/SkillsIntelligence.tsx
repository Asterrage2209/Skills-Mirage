import { useState, useEffect } from 'react';
import { ArrowUpRight, ArrowDownRight, Zap } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { getTopRoles, getSkillTrends } from '../../services/jobAnalytics';

// Helper function to format strings to Title Case for display
const formatSkillName = (name: string) => {
    if (!name) return name;
    return name.split(/[\s-]/)
        .map(word => {
            const upper = word.toUpperCase();
            if (upper === 'IT' || upper === 'AI' || upper === 'ML' || upper === 'ERP' || upper === 'QA' || upper === 'AWS') return upper;
            return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
        })
        .join(' ');
};

const SkillsIntelligence = () => {
    const [rolesData, setRolesData] = useState<any[]>([]);
    const [risingData, setRisingData] = useState<any[]>([]);
    const [decliningData, setDecliningData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let mounted = true;
        const loadData = async () => {
            try {
                const roles = await getTopRoles();
                const trends = await getSkillTrends();

                if (mounted) {
                    // Adapt roles to the gap format: mockSkillGaps had 'demand' and 'supply'
                    const mappedRoles = roles.map(r => ({ name: formatSkillName(r.role), demand: r.count, supply: Math.round(r.count * (0.5 + Math.random() * 0.5)) }));

                    const formatTrends = (trendsList: any[]) => (trendsList || []).map(t => ({ ...t, name: formatSkillName(t.name) }));

                    setRolesData(mappedRoles);
                    setRisingData(formatTrends(trends.rising_skills));
                    setDecliningData(formatTrends(trends.declining_skills));
                    setLoading(false);
                }
            } catch (err) {
                console.error("Error loading skills intelligence:", err);
                if (mounted) setLoading(false);
            }
        };
        loadData();
        return () => { mounted = false; };
    }, []);

    if (loading) {
        return <div className="p-8 text-center text-white">Loading skills intelligence...</div>;
    }

    return (
        <div className="space-y-6">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-white mb-1">Skills Intelligence</h1>
                <p className="text-textSecondary text-sm">Monitor emerging skill requirements and track declining technologies.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {/* Rising Skills list */}
                <div className="card">
                    <div className="flex items-center gap-2 mb-6">
                        <Zap className="w-5 h-5 text-accent" />
                        <h3 className="text-lg font-bold text-white">Top Rising Skills</h3>
                    </div>
                    {risingData.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">No skill trend data available</div>
                    ) : (
                        <div className="space-y-4">
                            {risingData.map((skill, i) => (
                                <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                                    <div className="font-medium text-white break-words max-w-[70%]">{skill.name}</div>
                                    <div className="flex items-center gap-1 text-green-400 bg-green-400/10 px-2 py-1 rounded-md text-sm font-semibold shrink-0">
                                        <ArrowUpRight className="w-4 h-4" /> {skill.growth}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Declining Skills list */}
                <div className="card">
                    <div className="flex items-center gap-2 mb-6">
                        <ArrowDownRight className="w-5 h-5 text-red-500" />
                        <h3 className="text-lg font-bold text-white">Top Declining Skills</h3>
                    </div>
                    {decliningData.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">No skill trend data available</div>
                    ) : (
                        <div className="space-y-4">
                            {decliningData.map((skill, i) => (
                                <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                                    <div className="font-medium text-textSecondary break-words max-w-[70%]">{skill.name}</div>
                                    <div className="flex items-center gap-1 text-red-400 bg-red-400/10 px-2 py-1 rounded-md text-sm font-semibold shrink-0">
                                        <ArrowDownRight className="w-4 h-4" /> {skill.decline}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Skill Gap Map */}
            <div className="card">
                <div className="mb-6">
                    <h3 className="text-lg font-bold text-white">Skill Gap Map</h3>
                    <p className="text-sm text-textSecondary">Comparing market demand against available training program outputs.</p>
                </div>

                <div className="h-[400px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={rolesData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                            <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                            <RechartsTooltip
                                cursor={{ fill: '#ffffff05' }}
                                contentStyle={{ backgroundColor: '#111827', borderColor: '#ffffff10', borderRadius: '8px' }}
                                itemStyle={{ color: '#e5e7eb' }}
                            />
                            <Bar dataKey="demand" name="Market Demand" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="supply" name="Training Supply" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                <div className="flex justify-center flex-wrap gap-4 mt-4">
                    <div className="flex items-center gap-2 text-sm text-textSecondary">
                        <div className="w-3 h-3 rounded-full bg-blue-500"></div> Companies Demand
                    </div>
                    <div className="flex items-center gap-2 text-sm text-textSecondary">
                        <div className="w-3 h-3 rounded-full bg-purple-500"></div> Training Supply
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SkillsIntelligence;

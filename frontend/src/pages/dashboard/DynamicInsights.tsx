import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { getTopCities, getTopRoles, getRoleDistribution, getCitySpread } from '../../services/jobAnalytics';
import { MapPin, Briefcase } from 'lucide-react';

const DynamicInsights = ({ refreshTrigger = 0 }: { refreshTrigger?: number }) => {
    // Dropdown options
    const [cities, setCities] = useState<any[]>([]);
    const [roles, setRoles] = useState<any[]>([]);

    // Selected state
    const [selectedCity, setSelectedCity] = useState<string>('');
    const [selectedRole, setSelectedRole] = useState<string>('');

    // Chart Data
    const [roleDistribution, setRoleDistribution] = useState<any[]>([]);
    const [citySpread, setCitySpread] = useState<any[]>([]);

    const [loadingOpt, setLoadingOpt] = useState(true);

    // Initial Load of Dropdown Options
    useEffect(() => {
        let mounted = true;
        const loadOptions = async () => {
            try {
                const [citiesRes, rolesRes] = await Promise.all([
                    getTopCities(),
                    getTopRoles()
                ]);

                if (mounted) {
                    setCities(citiesRes);
                    setRoles(rolesRes);

                    if (citiesRes.length > 0) setSelectedCity(citiesRes[0].name);
                    if (rolesRes.length > 0) setSelectedRole(rolesRes[0].role);
                    setLoadingOpt(false);
                }
            } catch (err) {
                console.error("Failed to load generic dropdown options", err);
                if (mounted) setLoadingOpt(false);
            }
        };
        loadOptions();
        return () => { mounted = false; };
    }, [refreshTrigger]);


    // Effect for handling City selection & Graph 1
    useEffect(() => {
        let mounted = true;
        if (!selectedCity) return;

        const fetchGraph1 = async () => {
            try {
                const distribution = await getRoleDistribution(selectedCity);
                if (mounted) {
                    setRoleDistribution(distribution);
                }
            } catch (err) {
                console.error("Error fetching role distribution", err);
            }
        };
        fetchGraph1();
        return () => { mounted = false; };
    }, [selectedCity, refreshTrigger]);


    // Effect for handling Role selection & Graph 2
    useEffect(() => {
        let mounted = true;
        if (!selectedRole) return;

        const fetchGraph2 = async () => {
            try {
                const spread = await getCitySpread(selectedRole);
                if (mounted) {
                    setCitySpread(spread);
                }
            } catch (err) {
                console.error("Error fetching city spread", err);
            }
        };
        fetchGraph2();
        return () => { mounted = false; };
    }, [selectedRole, refreshTrigger]);


    if (loadingOpt) {
        return <div className="card mt-8 p-4 text-center text-textSecondary">Loading market insights...</div>;
    }

    return (
        <div className="card mt-8">
            <h3 className="text-xl font-bold text-white mb-6 border-b border-gray-800 pb-4">Dynamic Market Insights</h3>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                {/* Graph 1: Role Distribution For Selected City */}
                <div className="flex flex-col space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <MapPin className="w-5 h-5 text-purple-400" />
                            <h4 className="text-md font-semibold text-white">Role Distribution</h4>
                        </div>
                        <select
                            value={selectedCity}
                            onChange={(e) => setSelectedCity(e.target.value)}
                            className="bg-secondary text-sm text-white px-3 py-1.5 rounded-md border border-gray-700 outline-none focus:border-purple-500 transition-colors"
                        >
                            {cities.map((cityObj, idx) => (
                                <option key={idx} value={cityObj.name}>{cityObj.name}</option>
                            ))}
                        </select>
                    </div>

                    <div className="h-[300px] w-full bg-secondary/30 rounded-lg p-2">
                        {roleDistribution.length === 0 ? (
                            <div className="w-full h-full flex items-center justify-center text-gray-500">No roles found for this city.</div>
                        ) : (
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={roleDistribution} margin={{ top: 20, right: 20, left: 0, bottom: 20 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                                    <XAxis dataKey="name" stroke="#9ca3af" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(val) => val.length > 10 ? val.substring(0, 10) + '...' : val} />
                                    <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                                    <RechartsTooltip
                                        cursor={{ fill: '#ffffff05' }}
                                        contentStyle={{ backgroundColor: '#111827', borderColor: '#ffffff10', borderRadius: '8px' }}
                                        itemStyle={{ color: '#e5e7eb' }}
                                        labelFormatter={(label) => `Role: ${label}`}
                                        formatter={(value) => [value, 'Openings in Selected City']}
                                    />
                                    <Bar dataKey="value" name="Job Count" fill="#a855f7" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </div>

                {/* Graph 2: City Spread For Selected Role */}
                <div className="flex flex-col space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Briefcase className="w-5 h-5 text-blue-400" />
                            <h4 className="text-md font-semibold text-white">City Spread</h4>
                        </div>
                        <select
                            value={selectedRole}
                            onChange={(e) => setSelectedRole(e.target.value)}
                            className="bg-secondary text-sm text-white px-3 py-1.5 rounded-md border border-gray-700 outline-none focus:border-blue-500 transition-colors max-w-[200px] truncate"
                        >
                            {roles.map((roleObj, idx) => (
                                <option key={idx} value={roleObj.role}>{roleObj.role}</option>
                            ))}
                        </select>
                    </div>

                    <div className="h-[300px] w-full bg-secondary/30 rounded-lg p-2">
                        {citySpread.length === 0 ? (
                            <div className="w-full h-full flex items-center justify-center text-gray-500">No cities found for this role.</div>
                        ) : (
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={citySpread} margin={{ top: 20, right: 20, left: 0, bottom: 20 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                                    <XAxis dataKey="name" stroke="#9ca3af" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(val) => val.length > 10 ? val.substring(0, 10) + '...' : val} />
                                    <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                                    <RechartsTooltip
                                        cursor={{ fill: '#ffffff05' }}
                                        contentStyle={{ backgroundColor: '#111827', borderColor: '#ffffff10', borderRadius: '8px' }}
                                        itemStyle={{ color: '#e5e7eb' }}
                                        labelFormatter={(label) => `City: ${label}`}
                                        formatter={(value) => [value, 'Openings for Selected Role']}
                                    />
                                    <Bar dataKey="value" name="Job Count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
};

export default DynamicInsights;

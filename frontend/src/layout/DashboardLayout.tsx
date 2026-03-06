import { Link, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
    LayoutDashboard,
    TrendingUp,
    BrainCircuit,
    ShieldAlert,
    UserSquare2,
    Route,
    MessageSquare,
    LogOut,
    Settings
} from 'lucide-react';
import { useState } from 'react';

const Sidebar = () => {
    const { logout } = useAuth();

    const layer1Menu = [
        { name: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
        { name: 'Hiring Trends', icon: TrendingUp, path: '/dashboard/hiring-trends' },
        { name: 'Skills Intelligence', icon: BrainCircuit, path: '/dashboard/skills' },
        { name: 'AI Vulnerability Index', icon: ShieldAlert, path: '/dashboard/vulnerability' },
    ];

    const layer2Menu = [
        { name: 'Worker Analysis', icon: UserSquare2, path: '/dashboard/worker' },
        { name: 'Reskilling Paths', icon: Route, path: '/dashboard/reskilling' },
        { name: 'AI Chatbot', icon: MessageSquare, path: '/dashboard/chatbot' },
    ];

    return (
        <aside className="w-64 bg-secondary border-r border-white/5 h-screen flex flex-col">
            <div className="p-6">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <BrainCircuit className="text-accent" /> Skills Mirage
                </h2>
            </div>

            <div className="flex-1 overflow-y-auto py-4">
                {/* Layer 1 */}
                <div className="px-4 mb-6">
                    <p className="text-xs font-semibold text-textSecondary uppercase tracking-wider mb-2 ml-2">Core Intelligence</p>
                    <ul className="space-y-1">
                        {layer1Menu.map((item) => (
                            <li key={item.name}>
                                <Link to={item.path} className="flex items-center gap-3 px-3 py-2 text-textSecondary hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                                    <item.icon className="w-5 h-5" />
                                    <span>{item.name}</span>
                                </Link>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Layer 2 */}
                <div className="px-4 mb-6">
                    <p className="text-xs font-semibold text-textSecondary uppercase tracking-wider mb-2 ml-2">Worker Action</p>
                    <ul className="space-y-1">
                        {layer2Menu.map((item) => (
                            <li key={item.name}>
                                <Link to={item.path} className="flex items-center gap-3 px-3 py-2 text-textSecondary hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                                    <item.icon className="w-5 h-5" />
                                    <span>{item.name}</span>
                                </Link>
                            </li>
                        ))}
                    </ul>
                </div>
            </div>

            <div className="p-4 border-t border-white/5">
                <ul className="space-y-1">
                    <li>
                        <button className="w-full flex items-center gap-3 px-3 py-2 text-textSecondary hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                            <Settings className="w-5 h-5" />
                            <span>Settings</span>
                        </button>
                    </li>
                    <li>
                        <button onClick={logout} className="w-full flex items-center gap-3 px-3 py-2 text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded-lg transition-colors">
                            <LogOut className="w-5 h-5" />
                            <span>Logout</span>
                        </button>
                    </li>
                </ul>
            </div>
        </aside>
    );
};

const TopBar = () => {
    const { user } = useAuth();
    return (
        <header className="h-16 bg-background/80 backdrop-blur-md border-b border-white/5 flex items-center justify-between px-6 sticky top-0 z-20">
            <div className="text-textSecondary">
                {/* Breadcrumb replacement / Status */}
                <span className="bg-accent/10 text-accent text-xs px-2 py-1 rounded-full border border-accent/20">System Live</span>
            </div>
            <div className="flex items-center gap-4">
                <div className="text-sm text-right">
                    <p className="text-white font-medium">{user?.name || 'Administrator'}</p>
                    <p className="text-textSecondary text-xs">Hackathon Demo</p>
                </div>
                <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-accent to-purple-500 overflow-hidden border border-white/20"></div>
            </div>
        </header>
    );
};

const DashboardLayout = () => {
    return (
        <div className="flex h-screen bg-background text-textPrimary overflow-hidden">
            <Sidebar />
            <div className="flex-1 flex flex-col h-screen overflow-hidden">
                <TopBar />
                <main className="flex-1 overflow-y-auto p-6 scroll-smooth">
                    <div className="max-w-7xl mx-auto">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
};

export default DashboardLayout;

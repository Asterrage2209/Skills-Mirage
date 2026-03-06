import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ArrowRight, Activity, ShieldAlert, BookOpen } from 'lucide-react';

const LandingPage = () => {
    const { isAuthenticated } = useAuth();

    return (
        <div className="min-h-screen bg-background relative overflow-hidden">
            {/* Animated Subtle Gradient Background */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
                <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] bg-accent/20 rounded-full blur-[120px]" />
                <div className="absolute top-[40%] -right-[10%] w-[40%] h-[40%] bg-purple-500/10 rounded-full blur-[120px]" />
            </div>

            {/* Navigation */}
            <nav className="relative z-10 flex items-center justify-between p-6 max-w-7xl mx-auto">
                <div className="flex items-center gap-2">
                    <Activity className="h-8 w-8 text-accent" />
                    <span className="text-xl font-bold tracking-tight text-white">Skills Mirage</span>
                </div>
                <div className="flex gap-4">
                    {isAuthenticated ? (
                        <Link to="/dashboard" className="btn-primary">Go to Dashboard</Link>
                    ) : (
                        <>
                            <Link to="/login" className="btn-secondary">Login</Link>
                            <Link to="/register" className="btn-primary">Sign Up</Link>
                        </>
                    )}
                </div>
            </nav>

            {/* Hero Section */}
            <main className="relative z-10 flex flex-col items-center justify-center text-center px-4 pt-32 pb-20 max-w-5xl mx-auto">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 text-accent text-sm font-medium mb-8 border border-accent/20">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
                    </span>
                    India’s first open workforce intelligence system
                </div>

                <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-white mb-6 leading-tight">
                    Navigate the future of <br /> <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent to-purple-400">Workforce Intelligence</span>
                </h1>

                <p className="text-xl text-textSecondary max-w-2xl mb-10 leading-relaxed">
                    Analyze job market signals, measure AI risk for specific roles, and discover personalized reskilling paths in real-time.
                </p>

                <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
                    <Link to={isAuthenticated ? "/dashboard" : "/register"} className="btn-primary flex justify-center items-center gap-2 text-lg px-8 py-3">
                        Get Started <ArrowRight className="w-5 h-5" />
                    </Link>
                    <a href="#features" className="btn-secondary flex justify-center items-center text-lg px-8 py-3">
                        Learn More
                    </a>
                </div>
            </main>

            {/* Features Section */}
            <section id="features" className="relative z-10 max-w-7xl mx-auto px-6 py-20 grid md:grid-cols-3 gap-8">
                <div className="card">
                    <Activity className="w-10 h-10 text-accent mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">Market Signals</h3>
                    <p className="text-textSecondary">Real-time analysis of hiring trends and shifting skill demands across cities and sectors.</p>
                </div>
                <div className="card">
                    <ShieldAlert className="w-10 h-10 text-red-400 mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">AI Vulnerability Index</h3>
                    <p className="text-textSecondary">Measure the automation risk for any job role based on changing market dynamics.</p>
                </div>
                <div className="card">
                    <BookOpen className="w-10 h-10 text-green-400 mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">Reskilling Paths</h3>
                    <p className="text-textSecondary">Personalized timeline UI guiding workers from vulnerable roles to high-demand careers.</p>
                </div>
            </section>
        </div>
    );
};

export default LandingPage;

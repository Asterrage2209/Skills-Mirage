import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Activity, ArrowRight, Lock, Mail } from 'lucide-react';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { login } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            // Mock login for Hackathon without actual backend ping if backend is not started/connected
            // Wait 1s
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Simulate real auth context using dummy data to satisfy demo
            login('mock-jwt-token-12345', { name: 'Demo User', email });
            navigate('/dashboard');
        } catch (err: any) {
            setError(err.message || 'Failed to login');
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4 relative overflow-hidden">
            <div className="absolute top-[20%] right-[10%] w-[30%] h-[30%] bg-accent/20 rounded-full blur-[100px] pointer-events-none" />
            <div className="absolute bottom-[20%] left-[10%] w-[30%] h-[30%] bg-purple-500/10 rounded-full blur-[100px] pointer-events-none" />

            <div className="w-full max-w-md relative z-10">
                <div className="text-center mb-10">
                    <Link to="/" className="inline-flex items-center gap-2 mb-6">
                        <Activity className="h-6 w-6 text-accent" />
                        <span className="text-lg font-bold tracking-tight text-white">Skills Mirage</span>
                    </Link>
                    <h2 className="text-3xl font-bold text-white mb-2">Welcome Back</h2>
                    <p className="text-textSecondary">Sign in to access your intelligence dashboard</p>
                </div>

                <form onSubmit={handleSubmit} className="card">
                    <div className="card-glow" />
                    {error && <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-lg mb-6 text-sm">{error}</div>}

                    <div className="space-y-4 relative z-10">
                        <div>
                            <label className="block text-sm font-medium text-textSecondary mb-1">Email</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-textSecondary" />
                                <input
                                    type="email"
                                    autoFocus
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="input-field pl-10"
                                    placeholder="admin@skillsmirage.com"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-textSecondary mb-1">Password</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-textSecondary" />
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="input-field pl-10"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 mt-4">
                            {loading ? 'Authenticating...' : 'Sign In'} <ArrowRight className="w-4 h-4" />
                        </button>
                    </div>

                    <p className="text-center text-sm text-textSecondary mt-6 relative z-10">
                        Don't have an account? <Link to="/register" className="text-accent hover:underline">Register here</Link>
                    </p>
                </form>
            </div>
        </div>
    );
};

export default Login;

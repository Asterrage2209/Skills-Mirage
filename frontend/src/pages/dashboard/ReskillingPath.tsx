import { BookOpen, CheckCircle, Code, FastForward, Play, Settings } from 'lucide-react';

const mockReskillingPath = [
    {
        week: "Weeks 1–3",
        title: "NPTEL Data Basics",
        description: "Foundational statistics and Python for data manipulation.",
        status: "completed",
        icon: BookOpen
    },
    {
        week: "Weeks 4–5",
        title: "AI Fundamentals",
        description: "Understanding LLMs, prompt engineering, and basic integration.",
        status: "in-progress",
        icon: FastForward
    },
    {
        week: "Weeks 6–8",
        title: "Digital Marketing Analytics",
        description: "Applying AI models to marketing datasets for ROI optimization.",
        status: "upcoming",
        icon: Settings
    },
];

const ReskillingPath = () => {
    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <div>
                <h1 className="text-2xl font-bold text-white mb-2">Reskilling Path</h1>
                <p className="text-textSecondary text-sm">Your customized learning roadmap to transition to lower-risk, higher-value roles.</p>

                <div className="mt-4 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 text-accent text-sm font-medium border border-accent/20">
                    Target Role: AI Marketing Ops Specialist
                </div>
            </div>

            <div className="card">
                <h3 className="text-lg font-bold text-white mb-8">Guided Timeline</h3>

                <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-white/10 before:to-transparent">
                    {mockReskillingPath.map((step, index) => {
                        const isCompleted = step.status === 'completed';
                        const isInProgress = step.status === 'in-progress';

                        return (
                            <div key={index} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-4 border-background shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow flex-col ${isCompleted ? 'bg-green-500' : isInProgress ? 'bg-accent' : 'bg-secondary'
                                    }`}>
                                    {isCompleted ? <CheckCircle className="w-4 h-4 text-white" /> :
                                        isInProgress ? <Play className="w-4 h-4 text-white" /> :
                                            <div className="w-2 h-2 rounded-full bg-white/50" />}
                                </div>

                                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] card p-4 pt-5 transition-transform hover:-translate-y-1">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-sm font-semibold text-accent">{step.week}</span>
                                        {isInProgress && <span className="text-xs px-2 py-0.5 rounded-full bg-accent/20 text-accent font-medium animate-pulse">Current</span>}
                                    </div>
                                    <h4 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                                        <step.icon className="w-5 h-5 text-textSecondary" /> {step.title}
                                    </h4>
                                    <p className="text-sm text-textSecondary leading-relaxed">{step.description}</p>

                                    {isInProgress && (
                                        <div className="mt-4">
                                            <div className="flex justify-between text-xs text-textSecondary mb-1">
                                                <span>Progress</span>
                                                <span>45%</span>
                                            </div>
                                            <div className="w-full bg-background rounded-full h-1.5">
                                                <div className="bg-accent h-1.5 rounded-full" style={{ width: '45%' }}></div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="card hover:border-white/20 transition-colors cursor-pointer group">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-3 rounded-lg bg-blue-500/10">
                            <Code className="w-6 h-6 text-blue-400" />
                        </div>
                        <span className="text-xs font-semibold text-textSecondary px-2 py-1 bg-white/5 rounded">Optional Module</span>
                    </div>
                    <h4 className="text-white font-bold mb-2 group-hover:text-accent transition-colors">Python Scripting Basics</h4>
                    <p className="text-sm text-textSecondary">Boost your automation capabilities with simple local scripts.</p>
                </div>

                <div className="card bg-accent/5 border-accent/20 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-accent/20 rounded-full blur-3xl pointer-events-none" />
                    <div className="p-3 rounded-lg bg-accent/10 w-fit mb-4">
                        <CheckCircle className="w-6 h-6 text-accent" />
                    </div>
                    <h4 className="text-white font-bold mb-2">Certification Ready</h4>
                    <p className="text-sm text-textSecondary mb-4">Complete your current timeline to unlock the NASSCOM endorsed AI certification exam.</p>
                    <button className="btn-primary text-sm px-4 py-1.5">View Details</button>
                </div>
            </div>
        </div>
    );
};

export default ReskillingPath;

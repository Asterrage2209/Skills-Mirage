import { useState, useEffect } from 'react';
import {
    BookOpen, CheckCircle, Play, Sparkles, TrendingUp,
    ArrowRightCircle, Briefcase, MapPin, ExternalLink,
    RefreshCw, AlertTriangle, Layers
} from 'lucide-react';
import {
    getReskillingApi, generateReskillingApi,
    ReskillingResponse, RecommendedSkill, RecommendedCourse,
    RecommendedJob, LearningStep
} from '../../services/api';

const ReskillingPath = () => {
    const [data, setData] = useState<ReskillingResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [error, setError] = useState('');

    // Load cached reskilling data on mount
    useEffect(() => {
        async function load() {
            setLoading(true);
            try {
                const res = await getReskillingApi();
                if (res.recommendation_type) {
                    setData(res);
                }
            } catch {
                // Silent — user may not have a profile yet
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    const handleGenerate = async () => {
        setGenerating(true);
        setError('');
        try {
            const res = await generateReskillingApi();
            setData(res);
            if (res.error) setError(res.error);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to generate reskilling path');
        } finally {
            setGenerating(false);
        }
    };

    const isUpskilling = data?.recommendation_type === 'upskilling';

    // Icon for each timeline step
    const stepIcons = [BookOpen, Layers, TrendingUp, Sparkles, CheckCircle];

    return (
        <div className="max-w-5xl mx-auto space-y-8">

            {/* ── Header ────────────────────────────────────────────────────── */}
            <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-2">Reskilling Path</h1>
                    <p className="text-textSecondary text-sm">
                        Your personalized learning roadmap based on market hiring trends,
                        your skills, and AI-powered recommendations.
                    </p>
                </div>
                <button
                    onClick={handleGenerate}
                    disabled={generating}
                    className="btn-primary flex items-center gap-2 shrink-0"
                >
                    {generating ? (
                        <>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            Generating...
                        </>
                    ) : (
                        <>
                            <Sparkles className="w-4 h-4" />
                            {data?.recommendation_type ? 'Regenerate' : 'Generate Reskilling Path'}
                        </>
                    )}
                </button>
            </div>

            {error && (
                <div className="flex items-center gap-2 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl text-sm text-red-400">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    {error}
                </div>
            )}

            {/* ── Loading state ─────────────────────────────────────────────── */}
            {loading && !data && (
                <div className="flex items-center justify-center h-64 text-textSecondary">
                    <RefreshCw className="w-6 h-6 animate-spin mr-2" />
                    Loading your reskilling data...
                </div>
            )}

            {/* ── Empty state ───────────────────────────────────────────────── */}
            {!loading && !data && !generating && (
                <div className="h-64 flex flex-col items-center justify-center text-center border-2 border-dashed border-white/10 rounded-2xl p-8">
                    <BookOpen className="w-12 h-12 text-textSecondary mb-4 opacity-50" />
                    <p className="text-textSecondary text-sm max-w-sm">
                        No reskilling path generated yet. Make sure you have filled in your <b className="text-white">Worker Analysis</b> profile, then click <b className="text-accent">"Generate Reskilling Path"</b> above.
                    </p>
                </div>
            )}

            {/* ── Results ───────────────────────────────────────────────────── */}
            {data?.recommendation_type && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-8">

                    {/* ── Recommendation badge + summary ───────────────────────── */}
                    <div className="card">
                        <div className="flex items-center gap-3 mb-4">
                            <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wide border ${isUpskilling
                                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                    : 'bg-purple-500/10 text-purple-400 border-purple-500/20'
                                }`}>
                                {isUpskilling ? <TrendingUp className="w-3.5 h-3.5" /> : <ArrowRightCircle className="w-3.5 h-3.5" />}
                                {data.recommendation_type}
                            </div>
                        </div>
                        {data.summary && (
                            <p className="text-textSecondary text-sm leading-relaxed">{data.summary}</p>
                        )}
                    </div>

                    {/* ── Recommended Skills ────────────────────────────────────── */}
                    {data.recommended_skills.length > 0 && (
                        <div className="card">
                            <div className="flex items-center gap-2 mb-5">
                                <TrendingUp className="w-5 h-5 text-emerald-400" />
                                <h3 className="text-lg font-bold text-white">Recommended Skills</h3>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                {data.recommended_skills.map((s: RecommendedSkill, i: number) => (
                                    <div key={i} className="p-3 bg-secondary rounded-xl border border-white/5">
                                        <span className="inline-block px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-2">
                                            {s.skill}
                                        </span>
                                        <p className="text-xs text-textSecondary leading-relaxed">{s.reason}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* ── Learning Path Timeline ────────────────────────────────── */}
                    {data.learning_path.length > 0 && (
                        <div className="card">
                            <h3 className="text-lg font-bold text-white mb-8">Learning Timeline</h3>
                            <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-white/10 before:to-transparent">
                                {data.learning_path.map((step: LearningStep, index: number) => {
                                    const isFirst = index === 0;
                                    const isLast = index === data.learning_path.length - 1;
                                    const StepIcon = stepIcons[index % stepIcons.length];

                                    return (
                                        <div key={index} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                                            <div className={`flex items-center justify-center w-10 h-10 rounded-full border-4 border-background shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow ${isFirst ? 'bg-accent' : isLast ? 'bg-emerald-500' : 'bg-secondary'
                                                }`}>
                                                {isFirst ? <Play className="w-4 h-4 text-white" /> :
                                                    isLast ? <CheckCircle className="w-4 h-4 text-white" /> :
                                                        <StepIcon className="w-4 h-4 text-textSecondary" />}
                                            </div>

                                            <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] card p-4 pt-5 transition-transform hover:-translate-y-1">
                                                <div className="flex items-center justify-between mb-1">
                                                    <span className="text-sm font-semibold text-accent">{step.week}</span>
                                                    {isFirst && <span className="text-xs px-2 py-0.5 rounded-full bg-accent/20 text-accent font-medium animate-pulse">Start Here</span>}
                                                </div>
                                                <h4 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                                                    <StepIcon className="w-5 h-5 text-textSecondary" /> {step.title}
                                                </h4>
                                                <p className="text-sm text-textSecondary leading-relaxed">{step.description}</p>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* ── Recommended Courses ──────────────────────────────────── */}
                    {data.recommended_courses.length > 0 && (
                        <div className="card">
                            <div className="flex items-center gap-2 mb-5">
                                <BookOpen className="w-5 h-5 text-blue-400" />
                                <h3 className="text-lg font-bold text-white">Recommended Courses</h3>
                            </div>
                            <div className="space-y-3">
                                {data.recommended_courses.map((c: RecommendedCourse, i: number) => (
                                    <div key={i} className="p-4 bg-secondary rounded-xl border border-white/5 flex flex-col sm:flex-row sm:items-center gap-3">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="font-semibold text-white text-sm">{c.name}</span>
                                                {c.source && (
                                                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">{c.source}</span>
                                                )}
                                            </div>
                                            {c.duration && <p className="text-xs text-textSecondary mb-1">Duration: {c.duration}</p>}
                                            {c.matched_skills?.length > 0 && (
                                                <div className="flex flex-wrap gap-1 mt-1">
                                                    {c.matched_skills.map((sk, j) => (
                                                        <span key={j} className="px-2 py-0.5 text-[10px] rounded-full bg-accent/10 text-accent border border-accent/20">{sk}</span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                        {c.url && (
                                            <a href={c.url} target="_blank" rel="noopener noreferrer"
                                                className="shrink-0 flex items-center gap-1 text-xs text-accent hover:text-white transition-colors">
                                                Open <ExternalLink className="w-3 h-3" />
                                            </a>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* ── Recommended Jobs ─────────────────────────────────────── */}
                    {data.recommended_jobs.length > 0 && (
                        <div className="card">
                            <div className="flex items-center gap-2 mb-5">
                                <Briefcase className="w-5 h-5 text-yellow-400" />
                                <h3 className="text-lg font-bold text-white">Recommended Jobs</h3>
                            </div>
                            <div className="space-y-3">
                                {data.recommended_jobs.map((j: RecommendedJob, i: number) => (
                                    <div key={i} className="p-4 bg-secondary rounded-xl border border-white/5">
                                        <div className="flex items-start justify-between gap-2 mb-2">
                                            <div>
                                                <h4 className="font-semibold text-white text-sm">{j.title}</h4>
                                                <div className="flex items-center gap-2 text-xs text-textSecondary mt-0.5">
                                                    {j.company && <span>{j.company}</span>}
                                                    {j.location && (
                                                        <span className="flex items-center gap-0.5"><MapPin className="w-3 h-3" />{j.location}</span>
                                                    )}
                                                </div>
                                            </div>
                                            <span className="flex-shrink-0 w-7 h-7 rounded-full bg-yellow-500/20 text-yellow-400 flex items-center justify-center text-xs font-bold">{i + 1}</span>
                                        </div>
                                        {j.match_reason && (
                                            <p className="text-xs text-textSecondary mb-2">{j.match_reason}</p>
                                        )}
                                        {j.required_skills?.length > 0 && (
                                            <div className="flex flex-wrap gap-1">
                                                {j.required_skills.map((sk, k) => (
                                                    <span key={k} className="px-2 py-0.5 text-[10px] rounded-full bg-white/5 text-textSecondary border border-white/10">{sk}</span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                </div>
            )}
        </div>
    );
};

export default ReskillingPath;

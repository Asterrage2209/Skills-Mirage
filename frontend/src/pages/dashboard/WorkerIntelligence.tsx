import { useState, useEffect } from 'react';
import { User, Briefcase, MapPin, Search, Layers, Sparkles, TrendingUp, ShieldAlert, ShieldCheck, ArrowRightCircle, Info } from 'lucide-react';
import { analyzeWorkerApi, getWorkerProfileApi, GeminiAnalysis } from '../../services/api';

type FormState = {
  title: string;
  city: string;
  experience: string;
  description: string;
  skills: string;
};

const riskLevelConfig: Record<string, { color: string; bg: string; border: string; icon: typeof ShieldAlert }> = {
  high: { color: 'text-red-400', bg: 'from-card to-red-500/10', border: 'border-red-500/30', icon: ShieldAlert },
  moderate: { color: 'text-yellow-400', bg: 'from-card to-yellow-500/10', border: 'border-yellow-500/30', icon: TrendingUp },
  low: { color: 'text-emerald-400', bg: 'from-card to-emerald-500/10', border: 'border-emerald-500/30', icon: ShieldCheck },
};

const WorkerIntelligence = () => {
  const [formState, setFormState] = useState<FormState>(() => {
    const saved = localStorage.getItem('worker_form_draft');
    return saved ? JSON.parse(saved) : {
      title: '',
      city: '',
      experience: '',
      description: '',
      skills: ''
    };
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [geminiAnalysis, setGeminiAnalysis] = useState<GeminiAnalysis | null>(null);

  // Persist form state to localStorage
  useEffect(() => {
    localStorage.setItem('worker_form_draft', JSON.stringify(formState));
  }, [formState]);

  // Auto-fill form data from Backend
  useEffect(() => {
    async function loadProfile() {
      try {
        const profile = await getWorkerProfileApi();
        setFormState(prev => ({
          ...prev,
          title: profile.job_role || '',
          city: profile.city || '',
          experience: profile.years_of_experience?.toString() || '',
          description: profile.role_description || '',
          skills: profile.skills ? profile.skills.join(', ') : ''
        }));

        if (profile.gemini_analysis) {
          setGeminiAnalysis(profile.gemini_analysis);
        }
      } catch (err) {
        // Silent catch unless it's a critical unauthenticated fault
      }
    }
    loadProfile();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      console.log("Submitting worker profile", formState);

      const res = await analyzeWorkerApi({
        job_role: formState.title,
        city: formState.city,
        years_of_experience: Number(formState.experience || 0),
        role_description: formState.description,
        skills: formState.skills ? formState.skills.split(',').map(s => s.trim()).filter(Boolean) : []
      });
      setGeminiAnalysis(res.gemini_analysis || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze worker profile');
    } finally {
      setLoading(false);
    }
  };

  const riskLevel = geminiAnalysis?.risk_level || 'unknown';
  const cfg = riskLevelConfig[riskLevel] || riskLevelConfig.moderate;
  const RiskIcon = cfg.icon;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-1">Worker Analysis</h1>
        <p className="text-textSecondary text-sm">Input profile details to generate AI risk assessment and reskilling path.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="card">
          <h3 className="text-lg font-bold text-white mb-6">Profile Details</h3>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">Current Job Title</label>
              <div className="relative">
                <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textSecondary" />
                <input
                  type="text"
                  required
                  className="input-field pl-9"
                  placeholder="e.g. BPO Agent"
                  value={formState.title}
                  onChange={(e) => setFormState({ ...formState, title: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-textSecondary mb-1">City</label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textSecondary" />
                  <input
                    type="text"
                    required
                    className="input-field pl-9"
                    placeholder="Pune"
                    value={formState.city}
                    onChange={(e) => setFormState({ ...formState, city: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-textSecondary mb-1">Years of Exp.</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textSecondary" />
                  <input
                    type="number"
                    required
                    className="input-field pl-9"
                    placeholder="2"
                    value={formState.experience}
                    onChange={(e) => setFormState({ ...formState, experience: e.target.value })}
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">Role Description (Key Tasks)</label>
              <textarea
                required
                className="input-field min-h-[120px] resize-y"
                placeholder="Briefly describe daily responsibilities..."
                value={formState.description}
                onChange={(e) => setFormState({ ...formState, description: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">Known Skills (Comma Separated)</label>
              <div className="relative">
                <Layers className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textSecondary" />
                <input
                  type="text"
                  className="input-field pl-9"
                  placeholder="Python, React, AWS..."
                  value={formState.skills}
                  onChange={(e) => setFormState({ ...formState, skills: e.target.value })}
                />
              </div>
            </div>

            {error ? <p className="text-sm text-red-400">{error}</p> : null}

            <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 mt-2">
              {loading ? 'Analyzing Profile...' : 'Analyze Risk & Opportunities'} <Search className="w-4 h-4" />
            </button>
          </form>
        </div>

        <div className="space-y-6">
          {geminiAnalysis ? (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">

              {/* ── Gemini AI Analysis Card ──────────────────────────────── */}
              <div className={`card ${cfg.border} bg-gradient-to-b ${cfg.bg}`}>
                <div className="flex items-center gap-2 mb-4 border-b border-white/5 pb-4">
                  <Sparkles className="w-5 h-5 text-purple-400" />
                  <h3 className="text-lg font-bold text-white">AI Risk Assessment</h3>
                  <span className={`ml-auto inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${cfg.color} bg-white/5 border ${cfg.border}`}>
                    <RiskIcon className="w-3.5 h-3.5" />
                    {riskLevel.toUpperCase()}
                  </span>
                </div>

                {geminiAnalysis.risk_score !== null && (
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-textSecondary">Gemini Risk Score</h3>
                    <div className={`text-2xl font-black ${cfg.color}`}>
                      {Math.round(geminiAnalysis.risk_score)}
                      <span className="text-sm text-textSecondary font-normal">/100</span>
                    </div>
                  </div>
                )}

                <div className="w-full bg-secondary h-2 rounded-full overflow-hidden mb-4">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${riskLevel === 'high' ? 'bg-red-500' : riskLevel === 'moderate' ? 'bg-yellow-500' : 'bg-emerald-500'
                      }`}
                    style={{ width: `${Math.min(100, Math.max(0, geminiAnalysis.risk_score ?? 0))}%` }}
                  />
                </div>

                {geminiAnalysis.explanation && (
                  <p className="text-textSecondary text-sm leading-relaxed">{geminiAnalysis.explanation}</p>
                )}
              </div>

              {/* ── New Skills to Learn (shown when risk moderate or high) ─ */}
              {geminiAnalysis.new_skills && geminiAnalysis.new_skills.length > 0 && (
                <div className="card">
                  <div className="flex items-center gap-2 mb-4">
                    <TrendingUp className="w-5 h-5 text-emerald-400" />
                    <h3 className="text-lg font-bold text-white">Recommended New Skills</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {geminiAnalysis.new_skills.map((skill, i) => (
                      <span key={i} className="px-3 py-1.5 text-xs font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* ── Pivot Roles (shown when risk is high) ────────────────── */}
              {geminiAnalysis.pivot_roles && geminiAnalysis.pivot_roles.length > 0 && (
                <div className="card">
                  <div className="flex items-center gap-2 mb-4">
                    <ArrowRightCircle className="w-5 h-5 text-accent" />
                    <h3 className="text-lg font-bold text-white">Suggested Pivot Roles</h3>
                  </div>
                  <div className="space-y-2">
                    {geminiAnalysis.pivot_roles.map((role, i) => (
                      <div key={i} className="p-3 bg-secondary rounded-xl border border-white/5 flex items-center gap-3">
                        <span className="flex-shrink-0 w-7 h-7 rounded-full bg-accent/20 text-accent flex items-center justify-center text-xs font-bold">{i + 1}</span>
                        <span className="font-semibold text-white text-sm">{role}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── Methodology ────────────────────────────────────────────── */}
              <div className="card">
                <div className="flex items-center gap-2 mb-4 text-white">
                  <Info className="w-5 h-5 text-accent" />
                  <h3 className="text-lg font-bold">Methodology</h3>
                </div>
                <div className="space-y-4">
                  <div className="p-3 bg-secondary/50 rounded-xl border border-white/5">
                    <p className="text-xs font-semibold text-accent uppercase mb-2">Risk Score Formula</p>
                    <code className="text-[10px] text-textSecondary block leading-relaxed whitespace-pre-line">
                      Risk Score =
                      (Automation Probability × 0.4)
                      + (Skill Replaceability × 0.3)
                      + (Task Repetition Level × 0.2)
                      + (AI Tool Adoption Rate × 0.1)
                    </code>
                    <ul className="mt-2 space-y-1 text-[10px] text-textSecondary/80">
                      <li>• Automation Probability → likelihood that job tasks can be automated</li>
                      <li>• Skill Replaceability → how easily the required skills can be replaced by AI tools</li>
                      <li>• Task Repetition Level → how repetitive the role's tasks are</li>
                      <li>• AI Tool Adoption Rate → current adoption of AI tools in that domain</li>
                    </ul>
                    <p className="mt-2 text-[10px] text-accent/80 font-medium">Scores are normalized to a 0–100 scale.</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-accent uppercase mb-1">Pivot Role Logic</p>
                    <p className="text-[11px] text-textSecondary leading-relaxed">
                      Our engine identifies transition paths by mapping current operational fatigue to AI-resilient growth roles using the latest LLM intelligence from Google Gemini.
                    </p>
                  </div>
                </div>
              </div>

            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 border-2 border-dashed border-white/10 rounded-2xl">
              <User className="w-12 h-12 text-textSecondary mb-4 opacity-50" />
              <p className="text-textSecondary text-sm max-w-[250px]">
                Submit profile details to generate an intelligence report tailored to your role history.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WorkerIntelligence;

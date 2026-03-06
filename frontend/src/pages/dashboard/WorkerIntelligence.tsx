import { useState, useEffect } from 'react';
import { User, Briefcase, MapPin, Search, Layers } from 'lucide-react';
import { analyzeWorkerApi, getWorkerProfileApi, WorkerAnalyzeResponse } from '../../services/api';

type FormState = {
  title: string;
  city: string;
  experience: string;
  description: string;
  skills: string;
};

const WorkerIntelligence = () => {
  const [formState, setFormState] = useState<FormState>({
    title: '',
    city: '',
    experience: '',
    description: '',
    skills: ''
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState<WorkerAnalyzeResponse | null>(null);
  const [riskScore, setRiskScore] = useState<number | null>(null);
  const [aiVulnerability, setAiVulnerability] = useState<number | null>(null);

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

        if (profile.risk_score !== null && profile.risk_score !== undefined) {
          setRiskScore(profile.risk_score);
        }
        if (profile.ai_vulnerability !== null && profile.ai_vulnerability !== undefined) {
          setAiVulnerability(profile.ai_vulnerability);
        }
        // Optionally fetch an implicit calculation if risk_score exists? (Ignored per prompt requirements)
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
      setResults(res);
      setRiskScore(res.risk_score);
      setAiVulnerability(res.ai_vulnerability);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze worker profile');
    } finally {
      setLoading(false);
    }
  };

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
          {(results || riskScore !== null) ? (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">
              <div className="card border-red-500/30 bg-gradient-to-b from-card to-red-500/5">
                <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-4">
                  <h3 className="text-lg font-bold text-white">AI Vulnerability Index</h3>
                  <div className="text-3xl font-black text-orange-400">
                    {Math.round(aiVulnerability ?? (results?.ai_vulnerability || 0))}
                  </div>
                </div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold text-textSecondary">Risk Score</h3>
                  <div className="text-xl font-bold text-red-500">
                    {Math.round(riskScore ?? (results?.risk_score || 0))}
                    <span className="text-sm text-textSecondary font-normal">/100</span>
                  </div>
                </div>

                {results && (
                  <p className="text-textSecondary text-sm leading-relaxed mb-4">
                    Parsed skills: {results.parsed_profile.skills.join(', ') || 'none detected'}
                  </p>
                )}
                <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
                  <div className="bg-red-500 h-full" style={{ width: `${Math.min(100, Math.max(0, riskScore ?? (results?.risk_score || 0)))}%` }}></div>
                </div>
              </div>

              {results && (
                <div className="card">
                  <h3 className="text-lg font-bold text-white mb-4">Suggested Pivot Role</h3>
                  <div className="p-3 bg-secondary rounded-xl border border-white/5 mb-4">
                    <div className="font-semibold text-white text-sm">{results.reskilling_path.target_role}</div>
                  </div>
                  <ul className="space-y-2">
                    {results.reskilling_path.plan.map((step) => (
                      <li key={step} className="text-sm text-textSecondary">• {step}</li>
                    ))}
                  </ul>
                </div>
              )}
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

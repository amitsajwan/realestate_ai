import React, { useEffect, useState } from 'react';
import { applyBrandTheme, defaultBrandTheme, BrandTheme } from '../theme';

type SuggestResponse = {
  brand_name_options: string[];
  tagline: string;
  colors: BrandTheme;
  notes?: string;
};

export default function Onboarding() {
  const [businessName, setBusinessName] = useState('');
  const [tags, setTags] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestion, setSuggestion] = useState<SuggestResponse | null>(null);

  useEffect(() => {
    applyBrandTheme(defaultBrandTheme());
  }, []);

  async function suggestBranding() {
    if (!businessName.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/branding/suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ business_name: businessName.trim(), tags: tags.split(',').map(t => t.trim()).filter(Boolean) })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: SuggestResponse = await res.json();
      setSuggestion(data);
      applyBrandTheme(data.colors);
    } catch (e: any) {
      setError(e?.message || 'Failed to get branding');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col p-4 gap-4">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-bold" style={{ color: 'var(--brand-secondary)' }}>Agent Onboarding</h1>
      </header>

      <section className="bg-white rounded-xl shadow p-4 space-y-3">
        <div className="space-y-1">
          <label className="text-sm text-gray-600">Business / Agent Name</label>
          <input className="w-full p-3 border rounded-md focus:ring-2 focus:ring-blue-500" placeholder="e.g. WorldGlass Realty"
                 value={businessName} onChange={e => setBusinessName(e.target.value)} />
        </div>
        <div className="space-y-1">
          <label className="text-sm text-gray-600">Tags (comma separated)</label>
          <input className="w-full p-3 border rounded-md focus:ring-2 focus:ring-blue-500" placeholder="luxury, pune, waterfront"
                 value={tags} onChange={e => setTags(e.target.value)} />
        </div>
        <button onClick={suggestBranding} disabled={loading || !businessName.trim()} className="btn-brand px-4 py-3 rounded-md font-semibold">
          {loading ? 'Generating...' : 'Get Branding Suggestions'}
        </button>
        {error && <p className="text-red-600 text-sm">{error}</p>}
      </section>

      {suggestion && (
        <section className="bg-white rounded-xl shadow p-4 space-y-4">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-full" style={{ background: suggestion.colors.primary }} />
            <div className="w-5 h-5 rounded-full" style={{ background: suggestion.colors.secondary }} />
            <div className="w-5 h-5 rounded-full" style={{ background: suggestion.colors.accent }} />
          </div>
          <div>
            <p className="text-gray-700 text-sm">Suggested brand names:</p>
            <ul className="list-disc ml-6 text-gray-900">
              {suggestion.brand_name_options.map((b) => (
                <li key={b} className="text-sm">{b}</li>
              ))}
            </ul>
          </div>
          <div className="p-3 rounded-md border-brand border">
            <p className="font-medium" style={{ color: 'var(--brand-secondary)' }}>Tagline</p>
            <p className="text-gray-800">{suggestion.tagline}</p>
          </div>
          {suggestion.notes && <p className="text-xs text-gray-500">{suggestion.notes}</p>}
        </section>
      )}
    </div>
  );
}


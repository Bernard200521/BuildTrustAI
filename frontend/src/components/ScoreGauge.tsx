import React from 'react';

interface Props {
  score?: number | null;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const ScoreGauge: React.FC<Props> = ({ score, size = 'md', showLabel = true }) => {
  if (score === undefined || score === null) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-slate-500 font-mono text-sm">--</span>
        {showLabel && <span className="text-xs text-slate-500">Unscored</span>}
      </div>
    );
  }

  const getScoreColor = (val: number) => {
    if (val >= 85) return { bg: 'bg-emerald-500', text: 'text-emerald-400', border: 'border-emerald-500/30' };
    if (val >= 60) return { bg: 'bg-amber-500', text: 'text-amber-400', border: 'border-amber-500/30' };
    return { bg: 'bg-rose-500', text: 'text-rose-400', border: 'border-rose-500/30' };
  };

  const colors = getScoreColor(score);

  if (size === 'sm') {
    return (
      <div className="flex items-center gap-2">
        <div className="w-16 bg-slate-800 rounded-full h-2 overflow-hidden">
          <div className={`h-full ${colors.bg}`} style={{ width: `${Math.min(100, Math.max(0, score))}%` }} />
        </div>
        <span className={`font-mono text-xs font-semibold ${colors.text}`}>{score.toFixed(1)}</span>
      </div>
    );
  }

  if (size === 'lg') {
    return (
      <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="text-4xl font-extrabold font-mono tracking-tight text-white mb-1">
          <span className={colors.text}>{score.toFixed(1)}</span>
          <span className="text-slate-500 text-xl font-normal"> / 100</span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-3 mt-2 overflow-hidden">
          <div className={`h-full transition-all duration-500 ${colors.bg}`} style={{ width: `${score}%` }} />
        </div>
        {showLabel && (
          <div className="flex justify-between w-full text-[10px] text-slate-500 mt-1 font-mono">
            <span>0 Block</span>
            <span>60 Review</span>
            <span>85 Approve</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2.5">
      <div className="w-24 bg-slate-800 rounded-full h-2.5 overflow-hidden">
        <div className={`h-full transition-all duration-500 ${colors.bg}`} style={{ width: `${score}%` }} />
      </div>
      <span className={`font-mono text-sm font-bold ${colors.text}`}>{score.toFixed(1)}</span>
    </div>
  );
};

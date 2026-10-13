import React from 'react';
import { DecisionType } from '../types';
import { CheckCircle2, AlertTriangle, XCircle, Clock, FileQuestion } from 'lucide-react';

interface Props {
  decision: DecisionType | string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<Props> = ({ decision, size = 'md' }) => {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs font-medium',
    lg: 'px-3 py-1.5 text-sm font-semibold'
  }[size];

  switch (decision) {
    case 'APPROVE':
      return (
        <span className={`inline-flex items-center gap-1.5 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-500/30 ${sizeClasses}`}>
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          APPROVE
        </span>
      );
    case 'REVIEW':
      return (
        <span className={`inline-flex items-center gap-1.5 rounded-full bg-amber-950/80 text-amber-400 border border-amber-500/30 ${sizeClasses}`}>
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          REVIEW
        </span>
      );
    case 'BLOCK':
      return (
        <span className={`inline-flex items-center gap-1.5 rounded-full bg-rose-950/80 text-rose-400 border border-rose-500/30 ${sizeClasses}`}>
          <XCircle className="w-3.5 h-3.5 text-rose-400" />
          BLOCK
        </span>
      );
    case 'INSUFFICIENT_EVIDENCE':
      return (
        <span className={`inline-flex items-center gap-1.5 rounded-full bg-indigo-950/80 text-indigo-400 border border-indigo-500/30 ${sizeClasses}`}>
          <FileQuestion className="w-3.5 h-3.5 text-indigo-400" />
          INSUFFICIENT EVIDENCE
        </span>
      );
    case 'PENDING_ASSESSMENT':
    default:
      return (
        <span className={`inline-flex items-center gap-1.5 rounded-full bg-slate-900 text-slate-400 border border-slate-700 ${sizeClasses}`}>
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          {decision}
        </span>
      );
  }
};

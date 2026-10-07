import React, { useState } from 'react';
import { ArrowRight, Layers, Eye, Sparkles, HelpCircle, CheckCircle2, Info, AlertTriangle, ShieldCheck } from 'lucide-react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { ExplainabilityResult, LesionFinding, RetinalStructure } from '../../types';

interface ExplainabilityViewProps {
  imageUrl: string;
  enhancedImageUrl?: string;
  structures?: RetinalStructure;
  lesions?: LesionFinding[];
  explainability: ExplainabilityResult;
  predictionConfidence: number;
  onNext: () => void;
  onBack: () => void;
}

export const ExplainabilityView: React.FC<ExplainabilityViewProps> = ({
  imageUrl,
  enhancedImageUrl,
  structures,
  lesions = [],
  explainability,
  predictionConfidence,
  onNext,
  onBack,
}) => {
  const [activeTab, setActiveTab] = useState<'original' | 'attention' | 'evidence'>('attention');
  const [attentionOpacity, setAttentionOpacity] = useState(0.60);

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-navy-950">Step 8 — Explainable AI (Model Attention Visualization)</h2>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
              Grad-CAM Saliency
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Visual explanation of convolutional and vision-transformer attention layers highlighting salient regions of interest.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onBack}>
            Back
          </Button>
          <Button variant="teal" size="sm" onClick={onNext} rightIcon={<ArrowRight className="w-4 h-4" />}>
            Proceed to Clinical Review
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: 3-Tab Image Comparison Viewport (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <Card
            title="Visual Evidence & Attention Viewport"
            headerAction={
              /* 3 Tabs: Original / Model Attention / Evidence */
              <div className="flex gap-1 text-xs bg-slate-100 p-1 rounded-lg border border-slate-200">
                <button
                  type="button"
                  onClick={() => setActiveTab('original')}
                  className={`px-2.5 py-1 rounded-md font-semibold transition-all ${
                    activeTab === 'original' ? 'bg-white text-navy-950 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Original
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('attention')}
                  className={`px-2.5 py-1 rounded-md font-semibold transition-all ${
                    activeTab === 'attention' ? 'bg-white text-navy-950 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Model Attention
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('evidence')}
                  className={`px-2.5 py-1 rounded-md font-semibold transition-all ${
                    activeTab === 'evidence' ? 'bg-white text-navy-950 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Evidence Regions
                </button>
              </div>
            }
          >
            {/* Canvas Viewport */}
            <div className="w-full h-[400px] bg-black rounded-xl overflow-hidden relative flex items-center justify-center select-none">
              <div className="relative w-[360px] h-[360px] rounded-full overflow-hidden flex items-center justify-center bg-black">
                {/* Base Fundus */}
                <img
                  src={imageUrl}
                  alt="Fundus"
                  className="w-full h-full object-contain pointer-events-none"
                />

                {/* Model Attention (Grad-CAM) Heatmap Layer */}
                {activeTab === 'attention' && (
                  <div
                    style={{ opacity: attentionOpacity }}
                    className="absolute inset-0 rounded-full pointer-events-none mix-blend-screen bg-gradient-radial from-amber-400 via-rose-600/60 to-transparent transition-opacity"
                  />
                )}

                {/* Evidence Overlay (Bounding boxes + Hotspots) */}
                {(activeTab === 'evidence' || activeTab === 'attention') && (
                  <svg className="absolute inset-0 w-full h-full pointer-events-none">
                    {explainability.attentionHotspots.map((spot, i) => (
                      <g key={i}>
                        <circle
                          cx={`${spot.x * 100}%`}
                          cy={`${spot.y * 100}%`}
                          r="18"
                          fill="rgba(245, 158, 11, 0.25)"
                          stroke="#F59E0B"
                          strokeWidth="2"
                          strokeDasharray="3 2"
                        />
                        <circle cx={`${spot.x * 100}%`} cy={`${spot.y * 100}%`} r="3" fill="#F59E0B" />
                        <text
                          x={`${spot.x * 100}%`}
                          y={`${spot.y * 100 - 22}%`}
                          fill="#FEF3C7"
                          fontSize="10"
                          fontWeight="bold"
                          textAnchor="middle"
                        >
                          {spot.label}
                        </text>
                      </g>
                    ))}
                  </svg>
                )}
              </div>

              {/* Viewport Badge */}
              <div className="absolute bottom-3 left-4 text-[11px] text-slate-300 bg-slate-900/80 px-3 py-1 rounded-md border border-slate-800">
                {activeTab === 'original'
                  ? 'Raw Fundus View'
                  : activeTab === 'attention'
                  ? `Grad-CAM Attention Heatmap (${Math.round(attentionOpacity * 100)}% opacity)`
                  : 'Evidence Regions & Candidate Hotspots'}
              </div>
            </div>

            {/* Opacity Control for Model Attention */}
            {activeTab === 'attention' && (
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between gap-4 mt-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                  <Layers className="w-4 h-4 text-teal-600" />
                  <span>Heatmap Transparency:</span>
                </div>
                <div className="flex items-center gap-3 flex-1 max-w-xs">
                  <input
                    type="range"
                    min="0.1"
                    max="1.0"
                    step="0.05"
                    value={attentionOpacity}
                    onChange={(e) => setAttentionOpacity(Number(e.target.value))}
                    className="w-full accent-teal-600"
                  />
                  <span className="text-xs font-mono font-bold text-navy-950 w-10 text-right">
                    {Math.round(attentionOpacity * 100)}%
                  </span>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Model Decision Explanation & Feature Weights (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <Card title="Model Decision Rationale & Explanation" subtitle="Natural-language interpretation of model gradient activations">
            <div className="space-y-3">
              {explainability.evidenceRationale.map((rationale, idx) => (
                <div key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 flex items-start gap-2.5">
                  <div className="w-5 h-5 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">
                    {idx + 1}
                  </div>
                  <p className="leading-snug">{rationale}</p>
                </div>
              ))}
            </div>
          </Card>

          {/* Salient Feature Weights */}
          <Card title="Salient Feature Contributions">
            <div className="space-y-3">
              {explainability.salientFeatures.map((feat, idx) => (
                <div key={idx} className="space-y-1 text-xs">
                  <div className="flex justify-between font-medium">
                    <span className="text-navy-950 font-semibold">{feat.name}</span>
                    <span className="font-mono text-teal-700 font-bold">
                      {(feat.importance * 100).toFixed(0)}% Weight
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500">{feat.impact}</div>
                  <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                    <div
                      style={{ width: `${feat.importance * 100}%` }}
                      className="bg-teal-600 h-full"
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Non-causal medical disclaimer */}
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-[11px] text-slate-500 flex items-start gap-2">
            <Info className="w-3.5 h-3.5 text-slate-400 mt-0.5 flex-shrink-0" />
            <span>
              {explainability.modelAttentionDisclaimer ||
                'Model attention visualization reflects spatial gradient correlations inside the neural network and does not assert causal clinical certainty.'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

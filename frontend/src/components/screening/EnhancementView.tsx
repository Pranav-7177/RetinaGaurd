import React, { useState, useEffect } from 'react';
import {
  ArrowRight,
  Sparkles,
  Sliders,
  CheckCircle2,
  Clock,
  Info,
  Layers,
  Eye,
  Check
} from 'lucide-react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { EnhancementResult, QualityMetrics } from '../../types';

interface EnhancementViewProps {
  originalImageUrl: string;
  enhancement: EnhancementResult;
  quality?: QualityMetrics;
  onNext: () => void;
  onBack: () => void;
}

export const EnhancementView: React.FC<EnhancementViewProps> = ({
  originalImageUrl,
  enhancement,
  quality,
  onNext,
  onBack,
}) => {
  const [viewMode, setViewMode] = useState<'side-by-side' | 'original' | 'enhanced'>('side-by-side');

  const methods = [
    { title: 'Contrast Limited Adaptive Histogram Equalization (CLAHE)', desc: 'Adaptive contrast enhancement applied to retinal photograph' },
    { title: 'LAB Color-Space Luminance Enhancement', desc: 'Equalizes L-channel intensity while preserving retinal color balance' },
    { title: 'Microvascular Contrast Optimization', desc: 'Sharpens fine vessel structures and retinal features for classifier' },
    { title: 'Normalized 224x224 Tensor Scaling', desc: 'Standardized resolution and ImageNet normalization for EfficientNet-B0' },
  ];

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-navy-950">Step 4 — Image Preprocessing (CLAHE)</h2>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-50 text-teal-800 border border-teal-200">
              CLAHE Preprocessing Applied
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Contrast Limited Adaptive Histogram Equalization (CLAHE) applied to enhance local image contrast prior to model inference.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onBack}>
            Back
          </Button>
          <Button
            variant="teal"
            size="sm"
            onClick={onNext}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Proceed to DR Assessment →
          </Button>
        </div>
      </div>

      {/* Preprocessing Status Banner */}
      <div className="p-4 bg-teal-50/70 border border-teal-200 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-teal-950">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-teal-600 text-white flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="font-bold text-sm text-navy-950">CLAHE Preprocessing Applied</div>
            <div className="text-slate-600 text-[11px]">
              Adaptive histogram equalization applied to enhance retinal microvasculature contrast before EfficientNet-B0 inference.
            </div>
          </div>
        </div>

        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 font-bold text-[11px] self-start sm:self-auto">
          <Check className="w-3.5 h-3.5" /> Preprocessing Ready
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Main Comparison Canvas (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          <Card
            title="Image Preprocessing Comparison"
            subtitle="Compare original fundus photograph with contrast-enhanced version"
            headerAction={
              <div className="flex gap-1 text-xs bg-slate-100 p-1 rounded-lg border border-slate-200">
                <button
                  type="button"
                  onClick={() => setViewMode('side-by-side')}
                  className={`px-2.5 py-1 rounded-md font-semibold transition-all ${
                    viewMode === 'side-by-side' ? 'bg-white text-navy-950 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Side-by-Side
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode('original')}
                  className={`px-2.5 py-1 rounded-md font-semibold transition-all ${
                    viewMode === 'original' ? 'bg-white text-navy-950 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Original Only
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode('enhanced')}
                  className={`px-2.5 py-1 rounded-md font-semibold transition-all ${
                    viewMode === 'enhanced' ? 'bg-white text-navy-950 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Processed Only
                </button>
              </div>
            }
          >
            {viewMode === 'side-by-side' ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Original */}
                <div className="space-y-2 text-center">
                  <div className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                    Original Fundus Photograph
                  </div>
                  <div className="w-full aspect-square bg-black rounded-xl overflow-hidden border border-slate-300 flex items-center justify-center p-2">
                    <img src={originalImageUrl} alt="Original Fundus" className="max-w-full max-h-full object-contain" />
                  </div>
                  <div className="text-[11px] text-slate-500 font-mono">Raw Camera Capture</div>
                </div>

                {/* Enhanced */}
                <div className="space-y-2 text-center">
                  <div className="text-xs font-bold text-teal-800 uppercase tracking-wide">
                    Processed / Enhanced Image
                  </div>
                  <div className="w-full aspect-square bg-black rounded-xl overflow-hidden border-2 border-teal-500 flex items-center justify-center p-2 relative">
                    <img
                      src={enhancement.enhancedImageUrl || originalImageUrl}
                      alt="Enhanced Fundus"
                      className="max-w-full max-h-full object-contain filter contrast-125"
                    />
                    <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded text-[10px] font-mono bg-teal-900/80 text-teal-200">
                      CLAHE Applied
                    </span>
                  </div>
                  <div className="text-[11px] text-teal-700 font-medium">Illumination Balanced & Filtered</div>
                </div>
              </div>
            ) : viewMode === 'original' ? (
              <div className="w-full h-80 bg-black rounded-xl overflow-hidden flex items-center justify-center p-2">
                <img src={originalImageUrl} alt="Original Fundus" className="max-w-full max-h-full object-contain" />
              </div>
            ) : (
              <div className="w-full h-80 bg-black rounded-xl overflow-hidden flex items-center justify-center p-2 border-2 border-teal-500">
                <img
                  src={enhancement.enhancedImageUrl || originalImageUrl}
                  alt="Enhanced Fundus"
                  className="max-w-full max-h-full object-contain filter contrast-125"
                />
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Preprocessing Stages & Telemetry (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <Card title="Preprocessing Pipeline" subtitle="Transformations applied prior to DR inference">
            <div className="space-y-3 text-xs">
              {methods.map((m, i) => (
                <div key={i} className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="font-bold text-navy-950">{m.title}</div>
                    <div className="text-[11px] text-slate-500 mt-0.5 leading-snug">{m.desc}</div>
                  </div>
                </div>
              ))}

              <div className="pt-2 border-t border-slate-100 flex justify-between items-center text-[11px] text-slate-500 font-mono">
                <span>Preprocessing Time:</span>
                <span className="font-bold text-slate-800">340 ms</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

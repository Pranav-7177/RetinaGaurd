import React, { useState } from 'react';
import { ArrowRight, Target, Eye, Activity, CheckCircle2, Sliders, Layers, Sparkles, AlertCircle } from 'lucide-react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { RetinalStructure } from '../../types';

interface RetinalAnalysisProps {
  imageUrl: string;
  enhancedImageUrl?: string;
  structures: RetinalStructure;
  onNext: () => void;
  onBack: () => void;
}

export const RetinalAnalysis: React.FC<RetinalAnalysisProps> = ({
  imageUrl,
  enhancedImageUrl,
  structures,
  onNext,
  onBack,
}) => {
  const [showOpticDisc, setShowOpticDisc] = useState(true);
  const [showFovea, setShowFovea] = useState(true);
  const [showVessels, setShowVessels] = useState(true);
  const [activeLayer, setActiveLayer] = useState<'original' | 'enhanced'>('original');

  const activeImage = activeLayer === 'enhanced' && enhancedImageUrl ? enhancedImageUrl : imageUrl;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Detected':
      case 'Available':
        return (
          <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 inline-flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            {status}
          </span>
        );
      case 'Pending':
        return (
          <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
            Pending
          </span>
        );
      case 'Unavailable':
      default:
        return (
          <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-rose-50 text-rose-800 border border-rose-200">
            Unavailable
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-navy-950">Step 5 — Retinal Structure & Vascular Analysis</h2>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
              Demo Landmark Scaffolding
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Anatomical localization of the Optic Nerve Head, Foveal Avascular Zone (FAZ), and major vessel tree morphology.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onBack}>
            Back
          </Button>
          <Button variant="teal" size="sm" onClick={onNext} rightIcon={<ArrowRight className="w-4 h-4" />}>
            Proceed to Lesion Analysis
          </Button>
        </div>
      </div>

      {/* 3 Core Analysis Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* 1. Optic Disc */}
        <Card className="border-t-4 border-t-blue-500">
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-bold text-navy-950 text-sm">
                <Target className="w-4 h-4 text-blue-600" />
                <span>Optic Disc</span>
              </div>
              {getStatusBadge(structures.opticDiscStatus || (structures.opticDiscDetected ? 'Detected' : 'Unavailable'))}
            </div>
            <p className="text-[11px] text-slate-500">
              Center coordinates: [{structures.opticDiscCenter.join(', ')}] • Radius: {(structures.opticDiscRadius * 100).toFixed(0)}%
            </p>
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] text-slate-600 font-medium">Visual Overlay:</span>
              <button
                type="button"
                onClick={() => setShowOpticDisc(!showOpticDisc)}
                className={`text-[11px] font-semibold px-2 py-0.5 rounded ${
                  showOpticDisc ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-600'
                }`}
              >
                {showOpticDisc ? 'Visible' : 'Hidden'}
              </button>
            </div>
          </div>
        </Card>

        {/* 2. Fovea */}
        <Card className="border-t-4 border-t-purple-500">
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-bold text-navy-950 text-sm">
                <Eye className="w-4 h-4 text-purple-600" />
                <span>Fovea (Macula)</span>
              </div>
              {getStatusBadge(structures.foveaStatus || (structures.foveaDetected ? 'Detected' : 'Unavailable'))}
            </div>
            <p className="text-[11px] text-slate-500">
              Foveal center: [{structures.foveaCenter.join(', ')}] • Macular Edema Risk: <span className="font-semibold text-slate-800">{structures.macularEdemaRisk}</span>
            </p>
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] text-slate-600 font-medium">Visual Overlay:</span>
              <button
                type="button"
                onClick={() => setShowFovea(!showFovea)}
                className={`text-[11px] font-semibold px-2 py-0.5 rounded ${
                  showFovea ? 'bg-purple-100 text-purple-800' : 'bg-slate-100 text-slate-600'
                }`}
              >
                {showFovea ? 'Visible' : 'Hidden'}
              </button>
            </div>
          </div>
        </Card>

        {/* 3. Retinal Vessels */}
        <Card className="border-t-4 border-t-teal-500">
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-bold text-navy-950 text-sm">
                <Activity className="w-4 h-4 text-teal-600" />
                <span>Retinal Vessels</span>
              </div>
              {getStatusBadge(structures.vesselNetworkStatus || 'Available')}
            </div>
            <p className="text-[11px] text-slate-500">
              Vessel density: {(structures.vesselDensityIndex * 100).toFixed(1)}% • AV Ratio: {structures.arteriovenousRatio.toFixed(2)}
            </p>
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] text-slate-600 font-medium">Visual Overlay:</span>
              <button
                type="button"
                onClick={() => setShowVessels(!showVessels)}
                className={`text-[11px] font-semibold px-2 py-0.5 rounded ${
                  showVessels ? 'bg-teal-100 text-teal-800' : 'bg-slate-100 text-slate-600'
                }`}
              >
                {showVessels ? 'Visible' : 'Hidden'}
              </button>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Retinal Overlay Viewer */}
      <Card
        title="Retinal Structure Overlay Canvas"
        subtitle="Interactive visual landmarks localized on fundus photograph"
        headerAction={
          <div className="flex items-center gap-2 text-xs">
            <button
              type="button"
              onClick={() => setActiveLayer(activeLayer === 'original' ? 'enhanced' : 'original')}
              className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold"
            >
              Background: {activeLayer === 'original' ? 'Original Capture' : 'Enhanced CLAHE'}
            </button>
          </div>
        }
      >
        <div className="w-full h-[420px] bg-black rounded-xl overflow-hidden relative flex items-center justify-center select-none">
          <div className="relative w-[380px] h-[380px] rounded-full overflow-hidden flex items-center justify-center bg-black">
            {/* Fundus Base */}
            <img src={activeImage} alt="Fundus Landmarks" className="w-full h-full object-contain pointer-events-none" />

            {/* Vessel Segmentation Vector Layer Placeholder */}
            {showVessels && (
              <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-80" viewBox="0 0 100 100">
                <path
                  d="M 28 48 Q 35 30 50 25 T 70 22 T 85 28"
                  stroke="#14B8A6"
                  strokeWidth="1.2"
                  fill="none"
                  strokeDasharray="2 1"
                />
                <path
                  d="M 28 52 Q 38 70 52 75 T 72 78 T 88 70"
                  stroke="#14B8A6"
                  strokeWidth="1.3"
                  fill="none"
                  strokeDasharray="2 1"
                />
              </svg>
            )}

            {/* Structure Landmarks SVG Overlays */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              {/* Optic Disc */}
              {showOpticDisc && structures.opticDiscDetected && (
                <g>
                  <circle
                    cx={`${structures.opticDiscCenter[0] * 100}%`}
                    cy={`${structures.opticDiscCenter[1] * 100}%`}
                    r={`${structures.opticDiscRadius * 100}%`}
                    fill="rgba(59, 130, 246, 0.2)"
                    stroke="#3B82F6"
                    strokeWidth="2.5"
                    strokeDasharray="4 2"
                  />
                  <text
                    x={`${structures.opticDiscCenter[0] * 100}%`}
                    y={`${structures.opticDiscCenter[1] * 100 - 12}%`}
                    fill="#93C5FD"
                    fontSize="11"
                    fontWeight="bold"
                    textAnchor="middle"
                  >
                    Optic Disc (Nasal)
                  </text>
                </g>
              )}

              {/* Fovea */}
              {showFovea && structures.foveaDetected && (
                <g>
                  <circle
                    cx={`${structures.foveaCenter[0] * 100}%`}
                    cy={`${structures.foveaCenter[1] * 100}%`}
                    r={`${structures.foveaRadius * 100}%`}
                    fill="rgba(168, 85, 247, 0.25)"
                    stroke="#A855F7"
                    strokeWidth="2"
                  />
                  <text
                    x={`${structures.foveaCenter[0] * 100}%`}
                    y={`${structures.foveaCenter[1] * 100 + 16}%`}
                    fill="#D8B4FE"
                    fontSize="11"
                    fontWeight="bold"
                    textAnchor="middle"
                  >
                    Fovea Center (FAZ)
                  </text>
                </g>
              )}
            </svg>
          </div>

          <div className="absolute bottom-3 left-4 text-[11px] text-slate-400 bg-slate-900/80 px-3 py-1 rounded-md border border-slate-800">
            Optic Disc localized in nasal hemisphere • Foveal avascular zone (FAZ) centered in temporal region
          </div>
        </div>
      </Card>
    </div>
  );
};

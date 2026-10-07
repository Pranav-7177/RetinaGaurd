import React, { useState, useRef } from 'react';
import {
  User,
  Search,
  Eye,
  ArrowRight,
  UserPlus,
  CheckCircle2,
  AlertCircle,
  Calendar,
  MapPin,
  Phone,
  Upload,
  Camera,
  FileImage,
  RefreshCw,
  Trash2,
  Check,
  Info
} from 'lucide-react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { Patient, EyeSide, ImageMetadata } from '../../types';
import { MOCK_PATIENTS } from '../../services/mockData';
import { patientService } from '../../services/patientService';

export interface PatientFormData {
  patientId: string;
  name: string;
  age: number | '';
  sex: 'Male' | 'Female' | 'Other';
  phone?: string;
  screeningLocation: string;
  screeningDate: string;
  eye: EyeSide;
  diabetesType?: string;
  diabetesDurationYears?: number;
}

interface PatientStepProps {
  selectedPatient?: Patient;
  selectedEye: EyeSide;
  patientFormData: PatientFormData;
  imageUrl?: string;
  imageMetadata?: ImageMetadata;
  onUpdatePatientForm: (data: Partial<PatientFormData>) => void;
  onSelectRegisteredPatient: (patient: Patient) => void;
  onImageSelected?: (url: string, metadata: ImageMetadata, file?: File | Blob) => void;
  onRemoveImage?: () => void;
  onNext: (hasImageUploaded?: boolean) => void;
  onSavedPatientLater?: (patientId: string) => void;
  isAnalyzing?: boolean;
  analysisError?: string | null;
}

const PRESET_SAMPLES = [
  {
    id: 'dr2',
    name: 'Sample A: Moderate NPDR (Grade 2)',
    url: '/assets/samples/sample_dr2_fundus.png',
    fileName: 'sample_moderate_npdr_od.png',
    fileSize: '1.9 MB',
    dimensions: '2048 × 1536 px',
    tag: 'Referable DR (Grade 2)'
  },
  {
    id: 'normal',
    name: 'Sample B: Normal Healthy Fundus (Grade 0)',
    url: '/assets/samples/sample_normal_fundus.png',
    fileName: 'sample_normal_healthy_os.png',
    fileSize: '0.9 MB',
    dimensions: '2048 × 1536 px',
    tag: 'Non-Referable (Grade 0)'
  },
  {
    id: 'dr3',
    name: 'Sample C: Severe NPDR (Grade 3)',
    url: '/assets/samples/sample_dr3_fundus.png',
    fileName: 'sample_severe_npdr_421.png',
    fileSize: '1.6 MB',
    dimensions: '2560 × 1920 px',
    tag: 'Urgent Referable (Grade 3)'
  },
  {
    id: 'ungradable',
    name: 'Sample D: Ungradable Low Quality Capture',
    url: '/assets/samples/sample_ungradable.png',
    fileName: 'sample_ungradable_blur.png',
    fileSize: '1.1 MB',
    dimensions: '1920 × 1440 px',
    tag: 'Ungradable (Recapture)'
  },
];

export const PatientStep: React.FC<PatientStepProps> = ({
  selectedPatient,
  selectedEye,
  patientFormData,
  imageUrl,
  imageMetadata,
  onUpdatePatientForm,
  onSelectRegisteredPatient,
  onImageSelected,
  onRemoveImage,
  onNext,
  onSavedPatientLater,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [mode, setMode] = useState<'form' | 'registry'>('form');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [savedSuccessMessage, setSavedSuccessMessage] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const filteredPatients = MOCK_PATIENTS.filter(
    (p) =>
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.district.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!patientFormData.patientId.trim()) {
      errs.patientId = 'Patient ID is required.';
    }
    if (!patientFormData.name.trim()) {
      errs.name = 'Patient name is required.';
    }
    if (patientFormData.age === '' || Number(patientFormData.age) < 1 || Number(patientFormData.age) > 120) {
      errs.age = 'Please enter a valid age (1-120).';
    }
    if (!patientFormData.screeningLocation.trim()) {
      errs.screeningLocation = 'Screening location is required.';
    }
    if (!patientFormData.screeningDate) {
      errs.screeningDate = 'Screening date is required.';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleProcessFile = (file: File) => {
    if (!onImageSelected) return;
    const localUrl = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const dimensions = `${img.naturalWidth} × ${img.naturalHeight} px`;
      const sizeMB = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
      const ext = file.name.split('.').pop()?.toUpperCase() || 'JPG';

      const meta: ImageMetadata = {
        fileName: file.name,
        fileSizeFormatted: sizeMB,
        sizeBytes: file.size,
        dimensions,
        fileFormat: ext,
        uploadedAt: new Date().toLocaleTimeString(),
      };
      onImageSelected(localUrl, meta, file);
    };
    img.src = localUrl;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleProcessFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handleSelectPreset = async (sample: typeof PRESET_SAMPLES[0]) => {
    if (!onImageSelected) return;
    const meta: ImageMetadata = {
      fileName: sample.fileName,
      fileSizeFormatted: sample.fileSize,
      sizeBytes: 2 * 1024 * 1024,
      dimensions: sample.dimensions,
      fileFormat: 'PNG',
      uploadedAt: new Date().toLocaleTimeString(),
    };
    try {
      const resp = await fetch(sample.url);
      const blob = await resp.blob();
      const fileObj = new File([blob], sample.fileName, { type: 'image/png' });
      onImageSelected(sample.url, meta, fileObj);
    } catch {
      onImageSelected(sample.url, meta);
    }
  };

  const handleSaveAndContinue = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    // If image is already attached, advance straight to Quality Assessment
    if (imageUrl) {
      onNext(true);
    } else {
      // If no image, go to step 2 to allow image capture
      onNext(false);
    }
  };

  // Workflow 5: Allow patient creation without image ("Image can be added later")
  const handleSavePatientLater = async () => {
    if (!validate()) return;

    const newPatient: Patient = {
      id: patientFormData.patientId,
      name: patientFormData.name,
      age: Number(patientFormData.age) || 50,
      gender: patientFormData.sex,
      phone: patientFormData.phone || 'N/A',
      district: patientFormData.screeningLocation,
      diabetesType: (patientFormData.diabetesType as any) || 'Type 2',
      diabetesDurationYears: patientFormData.diabetesDurationYears || 5,
      hba1c: undefined,
      hasHypertension: false,
      lastScreeningDate: undefined,
      lastDrGrade: undefined,
      isReferralActive: false,
      screeningsCount: 0,
      registeredAt: new Date().toISOString().split('T')[0]
    };

    try {
      await patientService.createPatient(newPatient);
      setSavedSuccessMessage(
        `Patient ${newPatient.name} (${newPatient.id}) successfully registered. You can upload their fundus image anytime from the Patients registry or Dashboard.`
      );
      if (onSavedPatientLater) {
        onSavedPatientLater(newPatient.id);
      }
    } catch {
      setSavedSuccessMessage(`Patient ${newPatient.name} saved to local session.`);
    }
  };

  const handleSelectFromRegistry = (p: Patient) => {
    onSelectRegisteredPatient(p);
    onUpdatePatientForm({
      patientId: p.id,
      name: p.name,
      age: p.age,
      sex: p.gender as any,
      phone: p.phone,
      screeningLocation: p.district,
      screeningDate: new Date().toISOString().split('T')[0],
      diabetesType: p.diabetesType,
      diabetesDurationYears: p.diabetesDurationYears,
    });
    setErrors({});
    setSavedSuccessMessage(null);
  };

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-navy-950">Step 1 — Patient Details & Fundus Image Intake</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Enter patient demographic information and attach a retinal fundus photograph. You may also register the patient and upload the image later.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={mode === 'form' ? 'teal' : 'outline'}
            size="sm"
            onClick={() => { setMode('form'); setSavedSuccessMessage(null); }}
          >
            New Patient Form
          </Button>
          <Button
            variant={mode === 'registry' ? 'teal' : 'outline'}
            size="sm"
            leftIcon={<Search className="w-3.5 h-3.5" />}
            onClick={() => { setMode('registry'); setSavedSuccessMessage(null); }}
          >
            Select Existing Patient
          </Button>
        </div>
      </div>

      {savedSuccessMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-900 flex items-start gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-bold">Patient Saved Successfully</div>
            <div>{savedSuccessMessage}</div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Form or Registry Selector (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {mode === 'form' ? (
            <Card title="Patient Demographic Details" subtitle="Required fields for clinical screening record">
              <form onSubmit={handleSaveAndContinue} className="space-y-4 text-xs">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Patient ID */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="font-semibold text-slate-700">
                        Patient ID <span className="text-rose-600">*</span>
                      </label>
                      <button
                        type="button"
                        onClick={() => {
                          const randomId = `PT-2026-${Math.floor(1000 + Math.random() * 9000)}`;
                          onUpdatePatientForm({ patientId: randomId });
                          if (errors.patientId) setErrors({ ...errors, patientId: '' });
                        }}
                        className="text-[10px] text-teal-700 hover:text-teal-800 font-semibold"
                      >
                        Auto-generate ID
                      </button>
                    </div>
                    <input
                      type="text"
                      placeholder="e.g. PT-2026-0891"
                      value={patientFormData.patientId}
                      onChange={(e) => {
                        onUpdatePatientForm({ patientId: e.target.value });
                        if (errors.patientId) setErrors({ ...errors, patientId: '' });
                      }}
                      className={`w-full px-3 py-2 rounded-lg border text-xs font-mono transition-colors ${
                        errors.patientId
                          ? 'border-rose-400 bg-rose-50/30 focus:ring-rose-500'
                          : 'border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20'
                      }`}
                    />
                    {errors.patientId && (
                      <p className="text-rose-600 text-[11px] mt-1 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> {errors.patientId}
                      </p>
                    )}
                  </div>

                  {/* Full Name */}
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      Full Name <span className="text-rose-600">*</span>
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Rameshwar Prasad"
                      value={patientFormData.name}
                      onChange={(e) => {
                        onUpdatePatientForm({ name: e.target.value });
                        if (errors.name) setErrors({ ...errors, name: '' });
                      }}
                      className={`w-full px-3 py-2 rounded-lg border text-xs transition-colors ${
                        errors.name
                          ? 'border-rose-400 bg-rose-50/30 focus:ring-rose-500'
                          : 'border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20'
                      }`}
                    />
                    {errors.name && (
                      <p className="text-rose-600 text-[11px] mt-1 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> {errors.name}
                      </p>
                    )}
                  </div>

                  {/* Age */}
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      Age (Years) <span className="text-rose-600">*</span>
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={120}
                      placeholder="e.g. 58"
                      value={patientFormData.age}
                      onChange={(e) => {
                        onUpdatePatientForm({ age: e.target.value === '' ? '' : Number(e.target.value) });
                        if (errors.age) setErrors({ ...errors, age: '' });
                      }}
                      className={`w-full px-3 py-2 rounded-lg border text-xs transition-colors ${
                        errors.age
                          ? 'border-rose-400 bg-rose-50/30 focus:ring-rose-500'
                          : 'border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20'
                      }`}
                    />
                    {errors.age && (
                      <p className="text-rose-600 text-[11px] mt-1 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> {errors.age}
                      </p>
                    )}
                  </div>

                  {/* Sex */}
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      Gender / Sex <span className="text-rose-600">*</span>
                    </label>
                    <select
                      value={patientFormData.sex}
                      onChange={(e) => onUpdatePatientForm({ sex: e.target.value as any })}
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 text-xs text-slate-800"
                    >
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>

                  {/* Contact Phone */}
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      Contact Phone (Optional)
                    </label>
                    <div className="relative">
                      <Phone className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                      <input
                        type="text"
                        placeholder="e.g. +91 98451 22910"
                        value={patientFormData.phone || ''}
                        onChange={(e) => onUpdatePatientForm({ phone: e.target.value })}
                        className="w-full pl-8 pr-3 py-2 rounded-lg border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 text-xs text-slate-800 font-mono"
                      />
                    </div>
                  </div>

                  {/* Screening Location */}
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      Screening Center / Camp <span className="text-rose-600">*</span>
                    </label>
                    <div className="relative">
                      <MapPin className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                      <input
                        type="text"
                        placeholder="e.g. Kurnool Rural Primary Health Center"
                        value={patientFormData.screeningLocation}
                        onChange={(e) => {
                          onUpdatePatientForm({ screeningLocation: e.target.value });
                          if (errors.screeningLocation) setErrors({ ...errors, screeningLocation: '' });
                        }}
                        className={`w-full pl-8 pr-3 py-2 rounded-lg border text-xs transition-colors ${
                          errors.screeningLocation
                            ? 'border-rose-400 bg-rose-50/30 focus:ring-rose-500'
                            : 'border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20'
                        }`}
                      />
                    </div>
                    {errors.screeningLocation && (
                      <p className="text-rose-600 text-[11px] mt-1 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> {errors.screeningLocation}
                      </p>
                    )}
                  </div>

                  {/* Screening Date */}
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      Screening Date <span className="text-rose-600">*</span>
                    </label>
                    <div className="relative">
                      <Calendar className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                      <input
                        type="date"
                        value={patientFormData.screeningDate}
                        onChange={(e) => {
                          onUpdatePatientForm({ screeningDate: e.target.value });
                          if (errors.screeningDate) setErrors({ ...errors, screeningDate: '' });
                        }}
                        className={`w-full pl-8 pr-3 py-2 rounded-lg border text-xs font-mono transition-colors ${
                          errors.screeningDate
                            ? 'border-rose-400 bg-rose-50/30 focus:ring-rose-500'
                            : 'border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20'
                        }`}
                      />
                    </div>
                    {errors.screeningDate && (
                      <p className="text-rose-600 text-[11px] mt-1 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> {errors.screeningDate}
                      </p>
                    )}
                  </div>

                  {/* Eye Selection */}
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1 flex items-center justify-between">
                      <span>Examined Eye <span className="text-slate-400 font-normal text-xs">(Optional)</span></span>
                      <span className="text-[11px] text-slate-400 font-normal">Single image per screening</span>
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      <button
                        type="button"
                        onClick={() => onUpdatePatientForm({ eye: 'OS' })}
                        className={`py-2 px-2.5 rounded-lg border font-semibold text-center transition-all flex items-center justify-center gap-1 text-xs ${
                          patientFormData.eye === 'OS'
                            ? 'bg-navy-900 border-navy-900 text-white shadow-sm'
                            : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                        }`}
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Left Eye</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => onUpdatePatientForm({ eye: 'OD' })}
                        className={`py-2 px-2.5 rounded-lg border font-semibold text-center transition-all flex items-center justify-center gap-1 text-xs ${
                          patientFormData.eye === 'OD'
                            ? 'bg-navy-900 border-navy-900 text-white shadow-sm'
                            : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                        }`}
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Right Eye</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => onUpdatePatientForm({ eye: 'NOT_SPECIFIED' })}
                        className={`py-2 px-2.5 rounded-lg border font-semibold text-center transition-all flex items-center justify-center gap-1 text-xs ${
                          patientFormData.eye === 'NOT_SPECIFIED' || !patientFormData.eye
                            ? 'bg-navy-900 border-navy-900 text-white shadow-sm'
                            : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                        }`}
                      >
                        <span>Not Specified</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Workflow 5: Action buttons supporting both immediate screening and add image later */}
                <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-3">
                  <button
                    type="button"
                    onClick={handleSavePatientLater}
                    className="w-full sm:w-auto px-4 py-2.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 font-semibold transition-colors flex items-center justify-center gap-2"
                  >
                    <Check className="w-4 h-4 text-slate-500" />
                    <span>Save Patient (Add Image Later)</span>
                  </button>

                  <Button
                    type="submit"
                    variant="teal"
                    rightIcon={<ArrowRight className="w-4 h-4" />}
                  >
                    {imageUrl ? 'Save & Analyze →' : 'Continue to Image Capture →'}
                  </Button>
                </div>
              </form>
            </Card>
          ) : (
            <Card title="Select Registered Patient" subtitle="Quickly link this screening to an existing candidate">
              <div className="space-y-3">
                <div className="relative">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    placeholder="Search candidate registry by name, ID, or district..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500 text-xs"
                  />
                </div>

                <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
                  {filteredPatients.map((p) => {
                    const isSelected = patientFormData.patientId === p.id;
                    return (
                      <div
                        key={p.id}
                        onClick={() => {
                          handleSelectFromRegistry(p);
                          setMode('form');
                        }}
                        className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                          isSelected
                            ? 'bg-teal-50 border-teal-500 ring-2 ring-teal-400/30'
                            : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs ${
                            isSelected ? 'bg-teal-600 text-white' : 'bg-slate-100 text-slate-600'
                          }`}>
                            {p.gender === 'Female' ? 'F' : 'M'}
                          </div>
                          <div>
                            <div className="text-xs font-bold text-navy-950 flex items-center gap-2">
                              <span>{p.name}</span>
                              <span className="text-[10px] text-slate-400 font-mono font-normal">{p.id}</span>
                            </div>
                            <div className="text-[11px] text-slate-500">
                              {p.age} yrs • {p.gender} • {p.district}
                            </div>
                          </div>
                        </div>
                        {isSelected && <CheckCircle2 className="w-5 h-5 text-teal-600" />}
                      </div>
                    );
                  })}
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* Right Column: Fundus Image Upload Area (Requirement 4 & 5) (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <Card
            title="Upload Fundus Image"
            subtitle="Upload one fundus image for this screening"
          >
            <div className="space-y-4 text-xs">
              {imageUrl ? (
                <div className="space-y-3">
                  <div className="p-3 bg-slate-900 rounded-xl text-center relative overflow-hidden">
                    <div className="w-48 h-48 rounded-full overflow-hidden mx-auto bg-black border-2 border-teal-500/50 flex items-center justify-center">
                      <img src={imageUrl} alt="Fundus Attached" className="w-full h-full object-contain" />
                    </div>
                    <span className="inline-block mt-2 px-2.5 py-0.5 rounded text-[10px] font-mono text-teal-300 bg-slate-800">
                      {imageMetadata?.dimensions || '2048 × 1536 px'} • {imageMetadata?.fileFormat || 'JPG'}
                    </span>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1 text-[11px]">
                    <div className="flex justify-between font-medium">
                      <span className="text-slate-500">File Name:</span>
                      <span className="font-bold text-navy-950 truncate max-w-[180px]">{imageMetadata?.fileName || 'fundus.jpg'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Examined Eye:</span>
                      <span className="font-bold text-teal-700">
                        {patientFormData.eye === 'OD' ? 'Right Eye (OD)' : patientFormData.eye === 'OS' ? 'Left Eye (OS)' : 'Not Specified'}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    {onRemoveImage && (
                      <button
                        type="button"
                        onClick={onRemoveImage}
                        className="text-xs text-rose-600 hover:text-rose-700 font-semibold inline-flex items-center gap-1"
                      >
                        <Trash2 className="w-3.5 h-3.5" /> Remove Image
                      </button>
                    )}

                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="text-xs text-teal-700 hover:text-teal-800 font-semibold inline-flex items-center gap-1"
                    >
                      <RefreshCw className="w-3.5 h-3.5" /> Replace Image
                    </button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".jpg,.jpeg,.png,.svg"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </div>
                </div>
              ) : (
                /* Dropzone for fundus upload during patient creation */
                <div className="space-y-3">
                  <div
                    onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                    onDragLeave={() => setDragActive(false)}
                    onDrop={handleDrop}
                    className={`border-2 border-dashed rounded-xl p-5 text-center transition-all ${
                      dragActive
                        ? 'border-teal-500 bg-teal-50/50'
                        : 'border-slate-300 bg-slate-50 hover:bg-slate-100/60'
                    }`}
                  >
                    <div className="space-y-2">
                      <div className="w-10 h-10 mx-auto rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center">
                        <Upload className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="font-bold text-navy-950 text-xs">
                          Upload one fundus image for this screening
                        </p>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          JPG, JPEG, or PNG from fundus camera (single eye)
                        </p>
                      </div>
                      <label className="inline-block cursor-pointer pt-1">
                        <span className="px-3 py-1.5 bg-navy-900 text-white rounded-lg text-xs font-semibold hover:bg-navy-800 shadow-sm inline-flex items-center gap-1.5">
                          <FileImage className="w-3.5 h-3.5" /> Browse Image
                        </span>
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept=".jpg,.jpeg,.png,.svg"
                          onChange={handleFileChange}
                          className="hidden"
                        />
                      </label>
                    </div>
                  </div>

                  {/* Requirement 5 Callout: Image can be added later */}
                  <div className="p-3 bg-amber-50/80 border border-amber-200 rounded-xl text-[11px] text-amber-900 flex items-start gap-2">
                    <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold">Image can be added later: </span>
                      If the patient has not been photographed with the fundus camera yet, you can register their details and add the photograph later.
                    </div>
                  </div>

                  {/* Fast testing preset buttons */}
                  <div className="pt-2 border-t border-slate-200">
                    <div className="text-[10px] font-bold text-slate-400 uppercase mb-1.5">
                      Or select calibrated sample image:
                    </div>
                    <div className="space-y-1.5">
                      {PRESET_SAMPLES.slice(0, 3).map((sample) => (
                        <button
                          key={sample.id}
                          type="button"
                          onClick={() => handleSelectPreset(sample)}
                          className="w-full text-left p-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 hover:border-teal-300 transition-colors flex items-center justify-between"
                        >
                          <div className="truncate font-semibold text-slate-800 text-[11px]">
                            {sample.name}
                          </div>
                          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                            {sample.tag}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};


import axios from 'axios';

// Use environment variable in production, localhost in development
const rawApiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').trim();
const API_BASE_URL = rawApiUrl.endsWith('/api') ? rawApiUrl : `${rawApiUrl}/api`;


export const apiClient = axios.create({
    baseURL: API_BASE_URL,
});

// Add interceptor to inject integration credentials if available
apiClient.interceptors.request.use((config) => {
    const apiKey = localStorage.getItem('integration_api_key');
    const provider = localStorage.getItem('integration_provider');

    if (apiKey && provider) {
        config.headers['X-Integration-Api-Key'] = apiKey;
        config.headers['X-Integration-Provider'] = provider;
    }
    return config;
});

export interface VariantStats {
    users: number;
    conversions: number;
    rate: number;
}

export interface PrimaryResult {
    control: VariantStats;
    treatment: VariantStats;
    absolute_lift: number;
    relative_lift: number;
    ci_95: [number, number];
    p_value: number;
    is_significant: boolean;
}

export interface GuardrailResult {
    name: string;
    control_count: number;
    treatment_count: number;
    control_rate: number;
    treatment_rate: number;
    delta: number;
    relative_lift: number | null;
    worsened: boolean;
    severe: boolean;
    p_value: number;
    error?: string;
}

export interface HealthCheckResult {
    status: string;
    result: {
        overall_status: 'Healthy' | 'Warning' | 'Blocked';
        schema: { status: string; issues: string[] };
        srm: { status: string; message: string; p_value: number } | null;
    };
    preview: Record<string, string | number | boolean | null>[];
    columns: string[];
    filename: string;
}

// Multi-variant types
export interface MultiVariantStats {
    users: number;
    conversions: number;
    rate: number;
    absolute_lift: number;
    relative_lift: number | null;
    ci_95: [number, number];
    p_value: number;
    p_value_corrected: number;
    is_significant: boolean;
    is_significant_corrected: boolean;
}

export interface OverallTest {
    chi2_stat: number;
    p_value: number;
    dof: number;
    is_significant: boolean;
}

export interface MultiVariantPrimaryResult {
    is_multivariant: true;
    overall: OverallTest;
    control_stats: VariantStats;
    variants: Record<string, MultiVariantStats>;
    correction_method: string;
    best_variant: string | null;
    all_pairs: Array<{
        variant_a: string;
        variant_b: string;
        absolute_lift: number;
        p_value: number;
        p_value_corrected: number;
        is_significant_corrected: boolean;
    }>;
}

export type PrimaryResultUnion = PrimaryResult | MultiVariantPrimaryResult;

export interface MultiVariantGuardrailEntry {
    name: string;
    variant: string;
    control_count: number;
    treatment_count: number;
    control_rate: number;
    treatment_rate: number;
    delta: number;
    relative_lift: number | null;
    worsened: boolean;
    severe: boolean;
    p_value: number;
    error?: string;
}

export interface MultiVariantGuardrailResults {
    by_variant: Record<string, MultiVariantGuardrailEntry[]>;
    any_severe: boolean;
    any_worsened: boolean;
    summary: Array<{
        name: string;
        worst_variant: string;
        worst_delta: number;
        severe: boolean;
        worsened: boolean;
    }>;
}

export type GuardrailResultUnion = GuardrailResult[] | MultiVariantGuardrailResults;

// Type guards
export function isMultiVariantPrimary(r: PrimaryResultUnion): r is MultiVariantPrimaryResult {
    return 'is_multivariant' in r && r.is_multivariant === true;
}

export function isMultiVariantGuardrails(r: GuardrailResultUnion): r is MultiVariantGuardrailResults {
    return !Array.isArray(r) && 'by_variant' in r;
}

// Multi-variant Bayesian types
export interface MultiVariantBayesianInsights {
    conversion: {
        vs_control: Record<string, {
            prob_beats_control: number;
            expected_loss: number;
            posterior: { alpha: number; beta: number };
        }>;
        prob_being_best: Record<string, number>;
        control_posterior: { alpha: number; beta: number };
    } | null;
    continuous: {
        by_variant: Record<string, Record<string, {
            prob_treatment_beats_control: number;
            expected_loss?: number;
        }>>;
    };
}

export type BayesianInsightsUnion = BayesianInsights | MultiVariantBayesianInsights;

export function isMultiVariantBayesian(r: BayesianInsightsUnion): r is MultiVariantBayesianInsights {
    if (!r || !r.conversion) return false;
    return 'vs_control' in r.conversion;
}

export interface AnalysisResult {
    status: string;
    is_multivariant?: boolean;
    variant_count?: number;
    primary_result: PrimaryResultUnion;
    guardrail_results: GuardrailResultUnion;
}

export interface ContinuousMetricResult {
    metric_name: string;
    control_mean: number;
    treatment_mean: number;
    absolute_lift: number;
    relative_lift: number;
    p_value: number;
    is_significant: boolean;
    is_valid: boolean;
}

export interface BayesianInsights {
    conversion: {
        prob_treatment_beats_control: number;
        expected_loss: number;
        control_posterior?: { alpha: number; beta: number };
        treatment_posterior?: { alpha: number; beta: number };
    } | null;
    continuous: Record<string, {
        prob_treatment_beats_control: number;
    }>;
}

export interface DecisionMemoResponse {
    status: string;
    decision: {
        decision: string;
        reason: string;
        details: string[];
    };
    memo_markdown: string;
    memo_html: string;
}

export const uploadHealthCheck = async (file: File): Promise<HealthCheckResult> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<HealthCheckResult>('/health-check', formData);
    return response.data;
};

export const analyzeData = async (file: File, guardrails?: string[]): Promise<AnalysisResult> => {
    const formData = new FormData();
    formData.append('file', file);
    if (guardrails && guardrails.length > 0) {
        formData.append('guardrails', guardrails.join(','));
    }

    const response = await apiClient.post<AnalysisResult>('/analyze', formData);
    return response.data;
};

export const analyzeContinuousMetrics = async (file: File): Promise<{ status: string; continuous_results: ContinuousMetricResult[] }> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/continuous-metrics', formData);
    return response.data;
};

export const analyzeBayesian = async (file: File): Promise<{ status: string; bayesian_insights: BayesianInsights }> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/bayesian-analysis', formData);
    return response.data;
};

export const generateDecisionMemo = async (data: {
    experiment_name: string;
    health_result: HealthCheckResult['result'];
    primary_result: PrimaryResultUnion;
    guardrail_results: GuardrailResultUnion;
    bayesian_insights?: BayesianInsightsUnion;
}): Promise<DecisionMemoResponse> => {
    const response = await apiClient.post('/decision-memo', data, {
        headers: { 'Content-Type': 'application/json' }
    });
    return response.data;
};

export interface Experiment {
    id: string;
    name: string;
    status: string;
    provider: string;
}

export interface AnalysisResponse extends AnalysisResult {
    experiment_id: string;
    provider: string;
}

export const listExperiments = async (provider: string): Promise<Experiment[]> => {
    const response = await apiClient.get<Experiment[]>(`/integrations/${provider}/experiments`);
    return response.data;
};

// ===== Sequential Testing API =====
import type { SequentialParams, SequentialAnalysisResponse, BoundaryPoint } from '../types';

export const runSequentialAnalysis = async (params: SequentialParams): Promise<SequentialAnalysisResponse> => {
    const response = await apiClient.post<SequentialAnalysisResponse>('/sequential-analysis', {
        control_users: params.controlUsers,
        control_conversions: params.controlConversions,
        treatment_users: params.treatmentUsers,
        treatment_conversions: params.treatmentConversions,
        target_sample_size: params.targetSampleSize,
        current_look: params.currentLook,
        max_looks: params.maxLooks,
        alpha: params.alpha,
        boundary_type: params.boundaryType,
        previous_looks: params.previousLooks,
    });
    return response.data;
};

export const getSequentialBoundaries = async (
    maxLooks: number = 5,
    alpha: number = 0.05,
    boundaryType: string = 'obrien_fleming',
): Promise<{ boundaries: BoundaryPoint[]; config: { max_looks: number; alpha: number; boundary_type: string } }> => {
    const response = await apiClient.get('/sequential-boundaries', {
        params: { max_looks: maxLooks, alpha, boundary_type: boundaryType },
    });
    return response.data;
};

export const analyzeExperiment = async (provider: string, experimentId: string, guardrails?: string[]): Promise<AnalysisResponse> => {
    const params = new URLSearchParams();
    if (guardrails && guardrails.length > 0) {
        params.append('guardrails', guardrails.join(','));
    }

    // Note: The backend endpoint is /api/integrations/{provider}/experiments/{id}/analyze
    // apiClient baseURL already includes /api
    const response = await apiClient.get<AnalysisResponse>(`/integrations/${provider}/experiments/${experimentId}/analyze`, {
        params
    });
    return response.data;
};

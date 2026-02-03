
import axios from 'axios';

// Use environment variable in production, localhost in development
const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_BASE_URL = rawApiUrl.endsWith('/api') ? rawApiUrl : `${rawApiUrl}/api`;


export const apiClient = axios.create({
    baseURL: API_BASE_URL,
});

export interface HealthCheckResult {
    status: string;
    result: {
        overall_status: 'Healthy' | 'Warning' | 'Blocked';
        schema: { status: string; issues: string[] };
        srm: { status: string; message: string } | null;
    };
    preview: any[];
    columns: string[];
    filename: string;
}

export interface AnalysisResult {
    status: string;
    primary_result: any;
    guardrail_results: any[];
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
    primary_result: any;
    guardrail_results: any[];
    bayesian_insights?: BayesianInsights;
}): Promise<DecisionMemoResponse> => {
    const response = await apiClient.post('/decision-memo', data, {
        headers: { 'Content-Type': 'application/json' }
    });
    return response.data;
};

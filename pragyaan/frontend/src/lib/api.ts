import axios from "axios";

export const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("pragyaan_token");
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("pragyaan_token");
      localStorage.removeItem("pragyaan_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// --- Types ---
export interface DocumentItem {
  id: string;
  title: string;
  subject: string;
  page_count: number;
  is_ocr: boolean;
  created_at: string;
}

export interface QuizQuestionItem {
  id: string;
  type: string;
  question_text: string;
  options?: string[] | null;
  source_page?: number | null;
}

export interface QuizItem {
  id: string;
  title: string;
  difficulty: string;
  negative_marking: boolean;
  time_limit_seconds?: number | null;
  questions: QuizQuestionItem[];
}

export interface FlashcardItem {
  id: string;
  front: string;
  back: string;
  next_review_at: string;
}

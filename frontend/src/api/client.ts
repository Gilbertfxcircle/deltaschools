// Axios client with two cross-cutting concerns wired in via interceptors:
//   1. Request: attach the bearer access token and the X-Tenant-ID header so
//      the backend's TenantMiddleware can pin the request to the right schema.
//   2. Response: on a 401, attempt a single refresh using the refresh token,
//      then replay the original request. If refresh fails, clear tokens and
//      surface the error so the app can redirect to login.

import axios, {
  AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";
import { resolveTenant } from "@/api/tenant";
import { tokenStore } from "@/api/tokenStore";
import type { ApiEnvelope, TokenPair } from "@/api/types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean;
}

export const http: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

http.interceptors.request.use((config) => {
  const access = tokenStore.getAccess();
  if (access) {
    config.headers.set("Authorization", `Bearer ${access}`);
  }
  const tenant = resolveTenant();
  if (tenant) {
    config.headers.set("X-Tenant-ID", tenant);
  }
  return config;
});

// Single-flight refresh: concurrent 401s share one refresh promise.
let refreshing: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = tokenStore.getRefresh();
  if (!refresh) {
    return null;
  }
  try {
    // Use a bare axios call to avoid recursive interceptor handling.
    const resp = await axios.post<ApiEnvelope<{ access_token: string }>>(
      `${BASE_URL}/auth/refresh`,
      null,
      { params: { refresh_token: refresh } },
    );
    const newAccess = resp.data.data.access_token;
    tokenStore.set(newAccess);
    return newAccess;
  } catch {
    tokenStore.clear();
    return null;
  }
}

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;
    if (error.response?.status === 401 && original && !original._retried) {
      original._retried = true;
      if (!refreshing) {
        refreshing = refreshAccessToken().finally(() => {
          refreshing = null;
        });
      }
      const newAccess = await refreshing;
      if (newAccess) {
        original.headers.set("Authorization", `Bearer ${newAccess}`);
        return http(original);
      }
    }
    return Promise.reject(error);
  },
);

/** Unwrap the standard envelope, throwing on a non-success payload. */
export function unwrap<T>(env: ApiEnvelope<T>): T {
  if (!env.success) {
    throw new ApiError(env.message, env.errors);
  }
  return env.data;
}

export class ApiError extends Error {
  readonly errors: string[];
  constructor(message: string, errors: string[] = []) {
    super(message);
    this.name = "ApiError";
    this.errors = errors;
  }
}

/** Convenience typed GET that unwraps the envelope. */
export async function apiGet<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const resp = await http.get<ApiEnvelope<T>>(url, config);
  return unwrap(resp.data);
}

/** Convenience typed POST that unwraps the envelope. */
export async function apiPost<T>(
  url: string,
  body?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const resp = await http.post<ApiEnvelope<T>>(url, body, config);
  return unwrap(resp.data);
}

/** Convenience typed PATCH that unwraps the envelope. */
export async function apiPatch<T>(
  url: string,
  body?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const resp = await http.patch<ApiEnvelope<T>>(url, body, config);
  return unwrap(resp.data);
}

export type { TokenPair };

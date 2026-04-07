// ═══════════════════════════════════════════
// PixelMind — API Client (FastAPI Bridge)
// ═══════════════════════════════════════════

const DEFAULT_API_PORT = process.env.NEXT_PUBLIC_API_PORT || '8000';

export function getApiBase(): string {
  const configuredApiBase = process.env.NEXT_PUBLIC_API_URL;
  if (configuredApiBase) {
    return configuredApiBase.replace(/\/$/, '');
  }

  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'https' : 'http';
    return `${protocol}://${window.location.hostname}:${DEFAULT_API_PORT}`;
  }

  return `http://localhost:${DEFAULT_API_PORT}`;
}

interface ApiOptions {
  method?: string;
  body?: FormData | string;
  headers?: Record<string, string>;
  token?: string;
}

async function apiCall<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {}, token } = options;
  const apiBase = getApiBase();

  const requestHeaders: Record<string, string> = { ...headers };

  if (token) {
    requestHeaders['Authorization'] = `Bearer ${token}`;
  }

  if (typeof body === 'string') {
    requestHeaders['Content-Type'] = 'application/json';
  }

  let response: Response;
  try {
    response = await fetch(`${apiBase}${endpoint}`, {
      method,
      headers: requestHeaders,
      body,
    });
  } catch {
    throw new Error(
      `Cannot reach backend at ${apiBase}. Ensure FastAPI is running and CORS allows this origin.`
    );
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// ── Auth ──
export async function registerUser(email: string, password: string, name: string) {
  return apiCall<{ id: string; email: string }>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, name }),
  });
}

export async function loginUser(email: string, password: string) {
  return apiCall<{ access_token: string; user: { id: string; email: string; credits: number } }>(
    '/api/auth/login',
    {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }
  );
}

// ── User ──
export async function getUserProfile(token: string) {
  return apiCall<{ id: string; email: string; name: string; credits: number }>('/api/user/me', {
    token,
  });
}

export async function refillCredits(token: string) {
  return apiCall<{ credits: number; message: string }>('/api/user/credits/refill', {
    method: 'POST',
    token,
  });
}

// ── AI Tools ──
export async function runAITool(
  tool: string,
  formData: FormData,
  token: string,
  onProgress?: (progress: number) => void
): Promise<{
  success: boolean;
  result_url?: string | null;
  remaining_credits: number;
  processing_time: number;
  error?: string | null;
}> {
  // Simulate progress updates
  if (onProgress) {
    const interval = setInterval(() => {
      onProgress(Math.min(90, Math.random() * 30 + 60));
    }, 500);

    try {
      const result = await apiCall<{
        success: boolean;
        result_url?: string | null;
        remaining_credits: number;
        processing_time: number;
        error?: string | null;
      }>(`/api/ai/${tool}`, {
        method: 'POST',
        body: formData,
        token,
      });
      onProgress(100);
      return result;
    } finally {
      clearInterval(interval);
    }
  }

  return apiCall(`/api/ai/${tool}`, {
    method: 'POST',
    body: formData,
    token,
  });
}

// ── Gallery ──
export async function getGallery(token: string) {
  return apiCall<
    {
      id: string;
      title: string;
      imageUrl: string;
      resultUrl: string;
      toolUsed: string;
      createdAt: string;
    }[]
  >('/api/gallery', { token });
}

export async function saveProject(
  token: string,
  data: { title: string; imageUrl: string; resultUrl: string; toolUsed: string; prompt?: string }
) {
  return apiCall<{ id: string }>('/api/gallery', {
    method: 'POST',
    body: JSON.stringify(data),
    token,
  });
}

// ── Ads ──
export async function logAdImpression(
  token: string,
  data: { adType: string; adBrand?: string; clicked?: boolean }
) {
  return apiCall('/api/ads/impression', {
    method: 'POST',
    body: JSON.stringify(data),
    token,
  });
}

export type ContentSnippet = {
  module: string;
  text: string;
  title: string | null;
};

export type TodayData = {
  mood: string;
  bubble_text: string;
  hedgehog_name: string;
  recipient_name: string;
  is_birthday: boolean;
  is_special_date: boolean;
  special_date_label: string | null;
  weather: {
    city: string;
    temp_c: number | null;
    description_hu: string;
    weather_code: number;
    mood_hint: string;
  } | null;
  language: string;
  poem: ContentSnippet | null;
  book_tip: ContentSnippet | null;
  movie_tip: ContentSnippet | null;
};

export type MediaItem = {
  id: number;
  filename: string;
  original_name: string;
  url: string;
  uploaded_by: string;
  created_at: string;
};

export type MediaList = {
  items: MediaItem[];
  total: number;
  page: number;
  limit: number;
};

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(path, {
    credentials: "include",
    ...options,
    headers: {
      ...(options.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(
      typeof err.detail === "string" ? err.detail : "Hiba történt."
    );
  }
  return res.json() as Promise<T>;
}

export async function checkAuth(): Promise<boolean> {
  const data = await request<{ authenticated: boolean }>("/api/auth/me");
  return data.authenticated;
}

export async function login(password: string): Promise<void> {
  await request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ password }),
  });
}

export async function logout(): Promise<void> {
  await request("/api/auth/logout", { method: "POST" });
}

export async function fetchToday(refreshBubble = false): Promise<TodayData> {
  const query = refreshBubble ? "?refresh_bubble=1" : "";
  return request<TodayData>(`/api/today${query}`);
}

export async function fetchMedia(page = 1, limit = 20): Promise<MediaList> {
  return request<MediaList>(`/api/media?page=${page}&limit=${limit}`);
}

export async function uploadMedia(
  file: File,
  uploadedBy: string
): Promise<MediaItem> {
  const form = new FormData();
  form.append("file", file);
  form.append("uploaded_by", uploadedBy);
  return request<MediaItem>("/api/media", {
    method: "POST",
    body: form,
  });
}

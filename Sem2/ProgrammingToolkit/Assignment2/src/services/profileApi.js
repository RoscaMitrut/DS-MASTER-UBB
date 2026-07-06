const API_BASE_URL = "http://127.0.0.1:5000";

async function fetchJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}

export function getPersonalData() {
  return fetchJson("/api/personal");
}

export function getProfessionalData() {
  return fetchJson("/api/professional");
}

export function getHobbiesData() {
  return fetchJson("/api/hobbies");
}
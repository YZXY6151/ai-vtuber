// frontend/src/services/api.ts

// 统一在文件顶部定义后端服务的基础地址，方便后续切换与维护
const ASR_BASE = import.meta.env.VITE_ASR_URL || 'http://localhost:8181';
const NLP_BASE = import.meta.env.VITE_NLP_URL || 'http://localhost:8182';
const TTS_BASE = import.meta.env.VITE_TTS_URL || 'http://localhost:8183';
const TIMEOUT_MS = 30_000; // 请求超时 30 秒

// 通用的 fetch 超时封装
async function fetchWithTimeout(input: RequestInfo, init?: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(input, { signal: controller.signal, ...init });
    return res;
  } finally {
    clearTimeout(id);
  }
}

/** 1. 语音识别（ASR） */
export async function recognizeAudio(file: File): Promise<{ transcription: string; language: string }> {
  const form = new FormData();
  form.append('file', file);

  const res = await fetchWithTimeout(`${ASR_BASE}/api/asr/recognize`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    // 抛出更详细的错误
    throw new Error(`ASR 请求失败：${res.status} ${res.statusText}`);
  }
  try {
    return await res.json();
  } catch {
    throw new Error('ASR 返回解析错误，非有效 JSON');
  }
}

// /** 2. GPT 对话（NLP） */
// export async function chatWithGPT(message: string): Promise<{ reply: string }> {
//   const res = await fetchWithTimeout(`${NLP_BASE}/api/nlp/chat`, {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
//     body: JSON.stringify({ message }),
//   });
//   if (!res.ok) {
//     let errMsg = `NLP 请求失败：${res.status} ${res.statusText}`;
//     try {
//       const errJson = await res.json();
//       if (errJson.error) errMsg += ` - ${errJson.error}`;
//     } catch {}
//     throw new Error(errMsg);
//   }
//   try {
//     return await res.json();
//   } catch {
//     throw new Error('NLP 返回解析错误，非有效 JSON');
//   }
// }

// frontend/src/services/api.ts

/** 2. GPT 对话（NLP） */
export async function chatWithGPT(message: string, persona: string): Promise<{ reply: string }> {
  const res = await fetch("http://localhost:8182/api/nlp/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, persona }),
  });
  if (!res.ok) throw new Error("GPT请求失败");
  return res.json();
}



/** 3. 语音合成（TTS） */
export async function synthesizeSpeech(text: string): Promise<Blob> {
  const res = await fetchWithTimeout(`${TTS_BASE}/api/tts/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'audio/mpeg' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(`TTS 请求失败：${res.status} ${res.statusText}`);
  }
  try {
    return await res.blob();
  } catch {
    throw new Error('TTS 返回解析错误，非有效音频流');
  }
}

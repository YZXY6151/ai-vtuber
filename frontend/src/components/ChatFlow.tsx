import React, { useState } from 'react';
import { chatWithGPT, synthesizeSpeech } from '../services/api';

type Status = 'idle' | 'processing';
type Persona = 'gentle' | 'tsundere' | 'energetic' | 'cool';

const personaMap: Record<Persona, string> = {
  gentle: '温柔主播',
  tsundere: '傲娇主播',
  energetic: '活泼主播',
  cool: '冷静主播',
};

export const ChatFlow: React.FC = () => {
  const [status, setStatus] = useState<Status>('idle');
  const [input, setInput] = useState('');
  const [message, setMessage] = useState('');
  const [reply, setReply] = useState('');
  const [error, setError] = useState('');
  const [persona, setPersona] = useState<Persona>('gentle'); // 默认 persona

  const sendText = async () => {
    const text = input.trim();
    if (!text) return;
    setError('');
    setStatus('processing');
    setMessage(text);
    setInput('');

    try {
      // 1. GPT
      const { reply } = await chatWithGPT(text, persona);
      setReply(reply);

      // 2. TTS
      const blob = await synthesizeSpeech(reply);
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => URL.revokeObjectURL(url);
      audio.play();
    } catch (e: any) {
      setError(e.message || '未知错误');
    } finally {
      setStatus('idle');
    }
  };

  return (
    <div className="p-4 space-y-4">
      {/* 角色选择 */}
      <div className="flex gap-2 items-center">
        <label>角色：</label>
        <select
          className="border rounded px-2 py-1"
          value={persona}
          onChange={e => setPersona(e.target.value as Persona)}
          disabled={status === 'processing'}
        >
          {Object.entries(personaMap).map(([key, label]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
      </div>

      {/* 输入区 */}
      <div className="flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendText()}
          className="flex-1 border rounded px-2"
          placeholder="输入文字后回车或点击发送"
          disabled={status === 'processing'}
        />
        <button
          onClick={sendText}
          disabled={!input.trim() || status === 'processing'}
          className="px-4 py-1 bg-blue-600 text-white rounded"
        >
          发送
        </button>
      </div>

      {/* 展示区 */}
      {error && <p className="text-red-600">{error}</p>}

      {message && (
        <div className="border p-2 rounded space-y-2">
          <p><strong>你：</strong>{message}</p>
          <p><strong>主播：</strong>{reply}</p>
        </div>
      )}
    </div>
  );
};

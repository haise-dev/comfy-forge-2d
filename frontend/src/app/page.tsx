'use client';

import { useState, useEffect, useRef } from 'react';
import { Send, Settings2, Plus } from 'lucide-react';

type Message = {
  id: string;
  sender: 'ai' | 'user';
  text: string;
  assetUrl?: string;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'ai',
      text: 'Greetings, developer. I am the Comfy Forge AI. What asset shall we forge today?',
    },
  ]);
  const [input, setInput] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('blurry, low quality, deformed, realistic, 3d render');
  const [seed, setSeed] = useState('-1');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleNewAsset = () => {
    if (isGenerating) return;
    setMessages([
      {
        id: Date.now().toString(),
        sender: 'ai',
        text: 'Canvas cleared. Ready for the next prompt.',
      },
    ]);
  };

  const sendMessage = async () => {
    if (!input.trim() || isGenerating) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsGenerating(true);

    try {
      const generateRes = await fetch('http://localhost:8000/api/v1/sprites/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          prompt: userMessage.text,
          negative_prompt: negativePrompt,
          seed: parseInt(seed) || -1
        }),
      });

      if (!generateRes.ok) throw new Error('API Error');
      const generateData = await generateRes.json();
      const taskId = generateData.task_id;

      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(`http://localhost:8000/api/v1/tasks/${taskId}`);
          if (!statusRes.ok) return;

          const statusData = await statusRes.json();

          if (statusData.status === 'SUCCESS' || statusData.status === 'FAILED') {
            clearInterval(pollInterval);
            setIsGenerating(false);

            if (statusData.status === 'SUCCESS') {
              const aiMessage: Message = {
                id: Date.now().toString(),
                sender: 'ai',
                text: 'Asset generation complete:',
                assetUrl: `http://localhost:8000${statusData.result.asset_urls[0]}`,
              };
              setMessages((prev) => [...prev, aiMessage]);
            } else {
              const aiMessage: Message = {
                id: Date.now().toString(),
                sender: 'ai',
                text: `Forge failed: ${statusData.error}`,
              };
              setMessages((prev) => [...prev, aiMessage]);
            }
          }
        } catch (pollErr) {
          console.error(pollErr);
        }
      }, 1000);
    } catch (err) {
      console.error(err);
      setIsGenerating(false);
      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString(), sender: 'ai', text: 'Error connecting to the Forge Backend.' },
      ]);
    }
  };

  return (
    <main className="flex h-screen bg-zinc-950 text-zinc-100 overflow-hidden font-sans">
      
      {/* Sidebar */}
      <aside className="hidden md:flex flex-col w-64 bg-zinc-900 border-r border-zinc-800 p-4">
        <h1 className="text-xl font-bold tracking-wide text-zinc-100 flex items-center gap-2 mb-6">
          Comfy Forge 2D ⚔️
        </h1>
        <button
          onClick={handleNewAsset}
          disabled={isGenerating}
          className="flex items-center gap-2 px-4 py-3 bg-zinc-800 hover:bg-zinc-700 transition rounded-xl text-sm font-medium disabled:opacity-50"
        >
          <Plus className="w-4 h-4" /> New Asset
        </button>
      </aside>

      {/* Main Chat Area */}
      <section className="flex-1 flex flex-col h-full relative">
        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 scroll-smooth">
          <div className="max-w-3xl mx-auto w-full space-y-6 pb-32">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex w-full ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] md:max-w-[75%] p-4 rounded-2xl shadow-sm leading-relaxed text-sm ${
                    msg.sender === 'user'
                      ? 'bg-indigo-600 text-zinc-50 rounded-br-sm'
                      : 'bg-zinc-900 text-zinc-300 rounded-bl-sm border border-zinc-800/50'
                  }`}
                >
                  <p>{msg.text}</p>
                  {msg.assetUrl && (
                    <div className="mt-3 overflow-hidden rounded-xl shadow-md border border-zinc-800/50">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={msg.assetUrl}
                        alt="Generated Asset"
                        className="w-full object-cover transition-transform duration-200 hover:scale-[1.02]"
                      />
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {isGenerating && (
              <div className="flex justify-start w-full">
                <div className="bg-zinc-900 p-4 rounded-2xl rounded-bl-sm border border-zinc-800/50 flex flex-col gap-3 max-w-[85%] md:max-w-[75%]">
                  <p className="text-sm text-zinc-400">Forging asset...</p>
                  <div className="animate-pulse bg-zinc-800 h-64 w-64 rounded-lg"></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Panel */}
        <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-zinc-950 via-zinc-950 to-transparent pt-10">
          <div className="max-w-3xl mx-auto">
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl shadow-xl overflow-hidden transition-all">
              
              {showAdvanced && (
                <div className="p-4 border-b border-zinc-800 bg-zinc-900/50 flex gap-4 flex-col md:flex-row text-xs text-zinc-400">
                  <div className="flex-1 flex flex-col gap-1">
                    <label>Negative Prompt</label>
                    <input
                      type="text"
                      className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
                      value={negativePrompt}
                      onChange={(e) => setNegativePrompt(e.target.value)}
                      disabled={isGenerating}
                    />
                  </div>
                  <div className="w-full md:w-32 flex flex-col gap-1">
                    <label>Seed (-1 = Random)</label>
                    <input
                      type="text"
                      className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
                      value={seed}
                      onChange={(e) => setSeed(e.target.value)}
                      disabled={isGenerating}
                    />
                  </div>
                </div>
              )}

              <div className="flex items-end gap-2 p-3">
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className={`p-2 rounded-xl transition ${showAdvanced ? 'text-indigo-400 bg-zinc-800' : 'text-zinc-500 hover:text-zinc-300'}`}
                  title="Advanced Settings"
                >
                  <Settings2 className="w-5 h-5" />
                </button>
                <textarea
                  className="flex-1 max-h-32 min-h-[44px] bg-transparent text-zinc-100 placeholder:text-zinc-600 resize-none focus:outline-none py-3"
                  placeholder="Describe your asset (e.g. glowing magic potion, pixel art)..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                  disabled={isGenerating}
                  rows={1}
                />
                <button
                  onClick={sendMessage}
                  disabled={!input.trim() || isGenerating}
                  className="p-3 bg-indigo-600 text-zinc-50 rounded-xl hover:bg-indigo-500 disabled:bg-zinc-800 disabled:text-zinc-600 transition"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

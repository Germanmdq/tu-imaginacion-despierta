"use client";
import React, { useState, useRef, useEffect } from "react";
import Navbar from "@/components/Navbar/Navbar";

export default function Academia() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hola, soy tu asistente para controlar la imaginación.' }
  ]);
  const [inputText, setInputText] = useState("");
  const [tutor, setTutor] = useState("neville");
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef(null);
  const finalTranscriptRef = useRef(""); 

  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'es-AR';

      recognitionRef.current.onresult = (event) => {
        let interimTranscript = '';
        let finalTrans = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTrans += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }
        if (finalTrans) {
          finalTranscriptRef.current += " " + finalTrans.trim();
          setInputText(prev => (prev + " " + finalTrans).trim());
        }
      };

      recognitionRef.current.onend = () => {
        setIsRecording(false);
        if (finalTranscriptRef.current.trim() !== "") {
           handleAutoSend(finalTranscriptRef.current.trim());
           finalTranscriptRef.current = "";
        }
      };
      
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        setIsRecording(false);
      };
    }
  }, []);

  const toggleRecording = () => {
    if (isRecording) {
      recognitionRef.current?.stop();
    } else {
      finalTranscriptRef.current = "";
      recognitionRef.current?.start();
      setIsRecording(true);
    }
  };

  const handleAutoSend = async (text) => {
    if(!text || isLoading) return;
    
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setInputText("");
    setIsLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text, author: tutor })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer || 'Lo siento, hubo un error procesando tu mensaje.' }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'No me pude conectar con el servidor.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async () => {
    if(!inputText.trim() || isLoading) return;
    
    const userMessage = inputText;
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setInputText("");
    setIsLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMessage, author: tutor })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer || 'Lo siento, hubo un error procesando tu mensaje.' }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'No me pude conectar con el servidor.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-[#F5F5F7] h-screen w-screen text-[#1D1D1F] flex flex-col overflow-hidden font-sans relative">
      
      {/* 1. Navbar */}
      <div className="relative z-20">
        <Navbar />
      </div>

      <div className="flex-grow flex pt-24 px-4 md:px-10 pb-6 gap-8 h-full max-h-screen relative z-10">
        
        {/* 2. Sidebar */}
        <aside className="hidden md:flex flex-col apple-card w-[260px] p-6 flex-shrink-0">
          <div className="flex items-center gap-4 mb-10 pl-2">
            <LogoTID className="h-8 text-[#1d1d1f]" />
          </div>

          <nav className="flex flex-col gap-2 flex-grow">
            <SidebarItem icon={HomeIcon} label="Tu espacio" active />
            <SidebarItem icon={BookIcon} label="Lecturas" />
            <SidebarItem icon={StarIcon} label="Afirmaciones" />
            <SidebarItem icon={BrainIcon} label="Coach" />
            <SidebarItem icon={CalendarIcon} label="Plan" />
            <SidebarItem icon={UserIcon} label="Mi cuenta" />
          </nav>

          <div className="mt-auto pt-6 border-t border-[#d2d2d7]">
            <SidebarItem icon={SettingsIcon} label="Ajustes" />
          </div>
        </aside>

        {/* 3. Main Chat Interface */}
        <main className="flex-grow flex flex-col h-full apple-card p-6 md:p-10 relative overflow-hidden">

          {/* Header */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 relative z-10 flex-shrink-0">
            <div>
              <h1 className="text-4xl font-bold mb-2 tracking-tight">Tu espacio</h1>
              <p className="text-[#86868b]">Hablá. El asistente ordena.</p>
            </div>
            
            <select 
              value={tutor}
              onChange={(e) => setTutor(e.target.value)}
              className="mt-4 md:mt-0 apple-input px-6 py-3 cursor-pointer appearance-none font-medium"
            >
              <option value="neville">Tutor: Neville Goddard</option>
              <option value="murphy">Tutor: Joseph Murphy</option>
              <option value="fox">Tutor: Emmet Fox</option>
              <option value="florence">Tutor: Florence Scovel Shinn</option>
            </select>
          </div>

          {/* Central Mic & Visualizer (LiveKit Style UI) */}
          <div className="flex flex-col items-center justify-center mb-8 relative z-10 flex-shrink-0 min-h-[140px]">
            {isRecording ? (
              <div className="flex items-center justify-center gap-1.5 h-16 mb-4">
                {[...Array(7)].map((_, i) => (
                  <div 
                    key={i}
                    className="w-2 rounded-full bg-[#1d1d1f] animate-visualizer origin-bottom"
                    style={{ 
                      height: '100%',
                      animationDelay: `${i * 0.15}s`,
                      animationDuration: `${0.6 + (i % 3) * 0.2}s`
                    }}
                  />
                ))}
              </div>
            ) : (
              <div className="h-16 mb-4 flex items-center justify-center">
                <p className="text-[#86868b] text-sm font-medium">Presioná para hablar</p>
              </div>
            )}
            
            <button 
              onClick={toggleRecording}
              className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-500 ${
                isRecording 
                ? 'bg-red-500 shadow-[0_0_20px_rgba(239,68,68,0.4)] scale-110' 
                : 'bg-[#1d1d1f] hover:bg-black shadow-[0_8px_30px_rgba(0,0,0,0.15)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.2)] hover:-translate-y-1'
              }`}
            >
              <MicIcon className={`w-8 h-8 ${isRecording ? 'text-white' : 'text-white'}`} />
            </button>
          </div>

          {/* Chat Messages */}
          <div className="flex-grow overflow-y-auto flex flex-col gap-6 mb-6 pr-2 relative z-10 scrollbar-hide">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'assistant' ? 'justify-start' : 'justify-end'}`}>
                {msg.role === 'assistant' && (
                  <div className="w-10 h-10 bg-[#f2f2f7] rounded-full flex items-center justify-center mr-4 text-xl flex-shrink-0 mt-1 shadow-sm">
                    🧠
                  </div>
                )}
                <div className={`max-w-[80%] p-5 rounded-3xl font-medium leading-relaxed ${
                  msg.role === 'assistant' 
                    ? 'bg-[#f2f2f7] text-[#1d1d1f] rounded-tl-sm' 
                    : 'bg-[#007aff] text-white rounded-tr-sm shadow-[0_4px_14px_rgba(0,122,255,0.3)]'
                }`}>
                  {msg.content}
                </div>
              </div>
            ))}
          </div>

          {/* Input Bar */}
          <div className="relative z-10 flex gap-3 flex-shrink-0">
            <button 
              onClick={toggleRecording}
              className={`md:hidden px-4 rounded-2xl flex items-center justify-center transition-colors ${
                isRecording ? 'bg-red-50 text-red-500' : 'bg-white border border-[#d2d2d7] text-[#86868b]'
              }`}
            >
               <MicIcon className="w-6 h-6" />
            </button>
            <textarea 
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={isLoading ? "Ánima está pensando..." : "Escribí o hablá..."}
              disabled={isLoading}
              className="flex-grow apple-input px-6 py-4 resize-none h-[60px]"
            />
            <button 
              onClick={handleSend}
              disabled={isLoading}
              className={`px-8 rounded-2xl font-bold tracking-wide flex items-center justify-center transition-all duration-300 ${
                isLoading 
                ? 'bg-[#e5e5ea] text-[#86868b] cursor-not-allowed' 
                : 'bg-[#1d1d1f] text-white hover:bg-black shadow-[0_4px_14px_rgba(0,0,0,0.1)] hover:shadow-[0_6px_20px_rgba(0,0,0,0.15)] hover:-translate-y-0.5'
              }`}
            >
              {isLoading ? "ENVIANDO..." : "ENVIAR"}
            </button>
          </div>
        </main>
      </div>

      {/* Mobile Bottom Nav */}
      <div className="md:hidden fixed bottom-0 left-0 w-full bg-white flex justify-around p-4 z-50 rounded-t-3xl border-t border-[#d2d2d7] shadow-[0_-10px_20px_rgba(0,0,0,0.03)]">
        <BottomNavItem icon={HomeIcon} label="Espacio" active />
        <BottomNavItem icon={StarIcon} label="Afirmar" />
        <BottomNavItem icon={BrainIcon} label="Coach" />
        <BottomNavItem icon={CalendarIcon} label="Plan" />
      </div>

      <style jsx global>{`
        .scrollbar-hide::-webkit-scrollbar {
            display: none;
        }
        .scrollbar-hide {
            -ms-overflow-style: none;
            scrollbar-width: none;
        }
      `}</style>
    </div>
  );
}

// Subcomponents
function SidebarItem({ icon: Icon, label, active }) {
  return (
    <a href="#" className={`flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 ${active ? 'bg-[#f2f2f7] text-[#1d1d1f] font-bold' : 'text-[#86868b] hover:bg-[#f2f2f7]/50 hover:text-[#1d1d1f]'}`}>
      <Icon className="w-5 h-5" />
      <span>{label}</span>
    </a>
  );
}

function BottomNavItem({ icon: Icon, label, active }) {
  return (
    <a href="#" className={`flex flex-col items-center gap-1 transition-colors ${active ? 'text-[#1d1d1f]' : 'text-[#86868b]'}`}>
      <Icon className="w-6 h-6" />
      <span className="text-[0.65rem] font-bold tracking-wider">{label}</span>
    </a>
  );
}

// SVG Icons
const LogoTID = ({ className }) => (
  <svg viewBox="0 0 145 50" className={className} fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <rect x="0" y="0" width="145" height="10" rx="2" />
    <rect x="25" y="10" width="12" height="40" rx="2" />
    <rect x="70" y="10" width="12" height="40" rx="2" />
    <path d="M 105 10 V 50 H 120 C 140 50, 140 10, 120 10 Z M 117 20 C 127 20, 127 40, 117 40 H 117 V 20 Z" fillRule="evenodd" />
  </svg>
);

const HomeIcon = (props) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>;
const BookIcon = (props) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>;
const StarIcon = (props) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>;
const BrainIcon = (props) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/></svg>;
const CalendarIcon = (props) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>;
const UserIcon = (props) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 0 0-16 0"/></svg>;
const SettingsIcon = (props) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>;
const MicIcon = (props) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>;

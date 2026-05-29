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
  const finalTranscriptRef = useRef(""); // To keep track of transcript without stale state

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
        // Auto-send if we collected text
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
      setMessages(prev => [...prev, { role: 'assistant', content: 'No me pude conectar con el servidor. Revisá que el backend esté corriendo en el puerto 8000.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-[#f3f4f6] h-screen w-screen text-gray-900 flex flex-col overflow-hidden">
      {/* 1. Navbar */}
      <Navbar />

      <div className="flex-grow flex pt-24 px-4 md:px-10 pb-6 gap-8 h-full max-h-screen">
        
        {/* 2. Sidebar */}
        <aside className="hidden md:flex flex-col bg-white w-[260px] rounded-[2.5rem] p-6 border border-gray-200 shadow-xl flex-shrink-0">
          <div className="flex items-center gap-4 mb-10 pl-2">
            <LogoTID className="h-10 text-gray-900" />
          </div>

          <nav className="flex flex-col gap-2 flex-grow">
            <SidebarItem icon={HomeIcon} label="Tu espacio" active />
            <SidebarItem icon={BookIcon} label="Lecturas" />
            <SidebarItem icon={StarIcon} label="Afirmaciones" />
            <SidebarItem icon={BrainIcon} label="Coach" />
            <SidebarItem icon={CalendarIcon} label="Plan" />
            <SidebarItem icon={UserIcon} label="Mi cuenta" />
          </nav>

          <div className="mt-auto pt-6 border-t border-gray-200">
            <SidebarItem icon={SettingsIcon} label="Ajustes" />
          </div>
        </aside>

        {/* 3. Main Chat Interface */}
        <main className="flex-grow flex flex-col h-full bg-white rounded-[3rem] border border-gray-200 p-6 md:p-10 relative overflow-hidden shadow-xl">
          {/* Background Glow */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[40rem] h-[20rem] bg-blue-200/40 rounded-[100%] blur-[80px] pointer-events-none"></div>

          {/* Header */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 relative z-10 flex-shrink-0">
            <div>
              <h1 className="text-4xl font-bold mb-2 text-gray-900 tracking-tight">Tu espacio</h1>
              <p className="text-gray-500">Hablá. El asistente ordena.</p>
            </div>
            
            <select 
              value={tutor}
              onChange={(e) => setTutor(e.target.value)}
              className="mt-4 md:mt-0 bg-gray-100 border border-gray-200 text-gray-700 rounded-2xl px-6 py-3 outline-none focus:border-blue-500 transition-colors cursor-pointer appearance-none"
            >
              <option value="neville">Tutor: Neville Goddard</option>
              <option value="murphy">Tutor: Joseph Murphy</option>
              <option value="fox">Tutor: Emmet Fox</option>
              <option value="florence">Tutor: Florence Scovel Shinn</option>
            </select>
          </div>

          {/* Central Mic */}
          <div className="flex justify-center mb-6 relative z-10 flex-shrink-0">
            <button 
              onClick={toggleRecording}
              className={`w-32 h-32 rounded-full flex flex-col items-center justify-center gap-3 relative transition-all duration-300 ${
                isRecording ? 'bg-red-500 shadow-[0_0_40px_rgba(239,68,68,0.4)] scale-105' : 'bg-white border-2 border-gray-100 hover:bg-gray-50 shadow-[0_0_40px_rgba(37,99,235,0.15)] hover:shadow-[0_0_50px_rgba(37,99,235,0.25)]'
              }`}
            >
              <MicIcon className={`w-8 h-8 ${isRecording ? 'text-white' : 'text-blue-600'}`} />
              <span className={`text-sm font-bold tracking-widest ${isRecording ? 'text-white' : 'text-blue-600'}`}>
                {isRecording ? "ESCUCHANDO" : "HABLAR"}
              </span>
            </button>
          </div>

          {/* Chat Messages */}
          <div className="flex-grow overflow-y-auto flex flex-col gap-4 mb-6 pr-2 relative z-10 scrollbar-hide">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'assistant' ? 'justify-start' : 'justify-end'}`}>
                {msg.role === 'assistant' && (
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-3 text-xl flex-shrink-0 mt-1">
                    🧠
                  </div>
                )}
                <div className={`max-w-[80%] p-4 rounded-3xl ${
                  msg.role === 'assistant' 
                    ? 'bg-gray-100 border border-gray-200 rounded-tl-sm text-gray-800' 
                    : 'bg-blue-600 text-white rounded-tr-sm'
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
              className={`md:hidden px-4 rounded-2xl border flex items-center justify-center transition-colors ${
                isRecording ? 'bg-red-500 border-red-500 text-white' : 'bg-gray-100 border-gray-200 hover:bg-gray-200 text-gray-700'
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
              className="flex-grow bg-gray-100 border border-gray-200 rounded-2xl px-6 py-4 text-gray-900 outline-none focus:border-blue-500 resize-none h-[60px]"
            />
            <button 
              onClick={handleSend}
              disabled={isLoading}
              className={`px-8 rounded-2xl font-bold flex items-center justify-center transition-colors ${isLoading ? 'bg-gray-300 text-gray-500' : 'bg-gray-900 text-white hover:bg-black'}`}
            >
              {isLoading ? "ENVIANDO..." : "ENVIAR"}
            </button>
          </div>
        </main>
      </div>

      {/* Mobile Bottom Nav */}
      <div className="md:hidden fixed bottom-0 left-0 w-full bg-white border-t border-gray-200 flex justify-around p-4 z-50">
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
    <a href="#" className={`flex items-center gap-4 px-4 py-3 rounded-xl transition-colors ${active ? 'bg-blue-50 text-blue-600 font-bold' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'}`}>
      <Icon className="w-5 h-5" />
      <span>{label}</span>
    </a>
  );
}

function BottomNavItem({ icon: Icon, label, active }) {
  return (
    <a href="#" className={`flex flex-col items-center gap-1 ${active ? 'text-blue-400' : 'text-gray-400'}`}>
      <Icon className="w-6 h-6" />
      <span className="text-[0.65rem] font-bold tracking-wider">{label}</span>
    </a>
  );
}

// SVG Icons
const LogoTID = ({ className }) => (
  <svg viewBox="0 0 145 50" className={className} fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <rect x="0" y="0" width="145" height="12" />
    <rect x="20" y="12" width="12" height="38" />
    <rect x="65" y="12" width="12" height="38" />
    <path d="M 95 12 V 50 H 110 A 19 19 0 0 0 110 12 Z M 107 24 H 110 A 7 7 0 0 1 110 38 H 107 Z" fillRule="evenodd" />
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

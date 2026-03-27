import React, { useRef, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';
import { useChat } from './hooks/useChat';
import { Leaf, Menu, X, Settings, HelpCircle } from 'lucide-react';

function App() {
  const { 
    sessionId, 
    messages, 
    sessions, 
    isLoading, 
    sendMessage, 
    createNewSession, 
    switchSession 
  } = useChat();

  const [isSidebarOpen, setIsSidebarOpen] = React.useState(true);

  return (
    <div className="flex h-screen bg-[#0c0e12] text-gray-100 overflow-hidden font-inter selection:bg-green-500/30">
      
      {/* Sidebar - Desktop & Mobile */}
      <div className={`transition-all duration-300 ease-in-out ${isSidebarOpen ? 'w-72' : 'w-0'} overflow-hidden h-full`}>
        <Sidebar 
          onNewChat={createNewSession} 
          onSwitchSession={switchSession}
          currentSessionId={sessionId}
          sessions={sessions}
        />
      </div>
      
      <main className="flex-1 flex flex-col relative min-w-0 bg-gradient-to-b from-[#0c0e12] via-[#0c0e12] to-[#0a0c10]">
        <header className="h-20 border-b border-gray-800/40 flex items-center justify-between px-6 md:px-10 bg-[#0c0e12]/60 backdrop-blur-2xl z-20">
          <div className="flex items-center gap-4 lg:gap-8">
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2.5 rounded-2xl hover:bg-gray-800/50 transition-all duration-300 text-gray-400 hover:text-white border border-transparent hover:border-gray-700/50 group"
            >
              {isSidebarOpen ? <X size={20} className="group-hover:rotate-90 transition-transform" /> : <Menu size={20} />}
            </button>
            <div className="flex items-center gap-4">
              <div className="p-2.5 bg-green-500/10 rounded-2xl border border-green-500/20 shadow-inner">
                <Leaf className="w-5 h-5 text-green-500" />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-xl font-black bg-gradient-to-r from-green-400 via-emerald-400 to-green-500 bg-clip-text text-transparent tracking-tight">
                  AI Agri Assistant
                </h1>
                <p className="text-[10px] text-gray-500 font-black tracking-[0.2em] uppercase opacity-60">
                    Precision Farming Engine
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 mr-4">
                <div className="px-3 py-1.5 rounded-full bg-green-500/5 border border-green-500/10 text-[10px] text-green-500 font-black uppercase tracking-[0.2em]">
                    System Nominal
                </div>
            </div>
            <button className="p-2.5 rounded-2xl hover:bg-gray-800/50 transition-all duration-300 text-gray-400 hover:text-white border border-transparent hover:border-gray-700/50">
                <Settings size={20} />
            </button>
            <button className="p-2.5 rounded-2xl hover:bg-gray-800/50 transition-all duration-300 text-gray-400 hover:text-white border border-transparent hover:border-gray-700/50">
                <HelpCircle size={20} />
            </button>
          </div>
        </header>

        <ChatWindow messages={messages} isLoading={isLoading} onQuickAction={sendMessage} />
        
        <div className="pb-8 pt-4 px-6 md:px-12 w-full max-w-5xl mx-auto">
          <InputBar onSend={sendMessage} isLoading={isLoading} />
        </div>
      </main>
    </div>
  );
}

export default App;

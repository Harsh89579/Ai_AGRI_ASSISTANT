import React from 'react';
import { PlusCircle, MessageSquare, Book, ShieldAlert, Droplets, History, User } from 'lucide-react';

const Sidebar = ({ onNewChat, onSwitchSession, currentSessionId, sessions }) => {
  const categories = [
    { name: 'Fertilizer', icon: <Book className="w-4 h-4" />, color: 'text-green-400' },
    { name: 'Crop Advice', icon: <MessageSquare className="w-4 h-4" />, color: 'text-blue-400' },
    { name: 'Disease Help', icon: <ShieldAlert className="w-4 h-4" />, color: 'text-red-400' },
    { name: 'Irrigation', icon: <Droplets className="w-4 h-4" />, color: 'text-cyan-400' },
  ];

  const formatSessionTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <aside className="w-72 border-r border-gray-800/60 flex flex-col bg-[#0f1116] z-20 shrink-0">
      <div className="p-6">
        <button 
          onClick={onNewChat}
          className="w-full h-12 flex items-center justify-center gap-3 rounded-2xl bg-green-600 hover:bg-green-500 transition-all duration-300 text-white font-bold shadow-lg shadow-green-900/20 active:scale-95 border border-green-400/20 group"
        >
          <PlusCircle className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" />
          <span>New Consultation</span>
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto px-4 py-2 space-y-8 scrollbar-hide">
        <div>
          <h3 className="text-[10px] font-extrabold text-gray-500 uppercase tracking-[0.2em] mb-4 px-3 flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
            Categories
          </h3>
          <div className="space-y-1.5">
            {categories.map((cat) => (
              <button 
                key={cat.name}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-gray-400 hover:text-white hover:bg-gray-800/30 transition-all text-sm group border border-transparent hover:border-gray-800/50"
              >
                <div className={`${cat.color} p-2 rounded-xl bg-gray-900/80 group-hover:bg-gray-800 transition-colors shadow-inner`}>
                  {cat.icon}
                </div>
                <span className="font-semibold tracking-wide">{cat.name}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-4 px-3">
            <h3 className="text-[10px] font-extrabold text-gray-500 uppercase tracking-[0.2em] flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                Recent Activity
            </h3>
            <History className="w-3.5 h-3.5 text-gray-700" />
          </div>
          <div className="space-y-2.5 max-h-[400px] overflow-y-auto pr-1">
            {sessions.length > 0 ? (
                sessions.map((session) => (
                    <button
                        key={session.session_id}
                        onClick={() => onSwitchSession(session.session_id)}
                        className={`w-full text-left px-4 py-4 rounded-2xl transition-all duration-300 group border ${
                            currentSessionId === session.session_id 
                            ? 'bg-green-500/5 border-green-500/20 text-green-400 shadow-[0_0_20px_rgba(34,197,94,0.05)]' 
                            : 'bg-transparent border-transparent hover:bg-gray-800/20 text-gray-400 hover:border-gray-800/50'
                        }`}
                    >
                        <div className="flex items-center gap-4">
                            <div className={`p-2.5 rounded-xl transition-colors ${currentSessionId === session.session_id ? 'bg-green-500/10' : 'bg-gray-800/40 text-gray-600 group-hover:bg-gray-800'}`}>
                                <MessageSquare className="w-4 h-4" />
                            </div>
                            <div className="flex flex-col gap-0.5 overflow-hidden">
                                <span className="text-sm font-bold truncate tracking-tight">
                                    {session.session_id === currentSessionId ? 'Ongoing Chat' : `Session ${session.session_id.substring(0, 6)}`}
                                </span>
                                <span className="text-[10px] font-medium opacity-50 uppercase tracking-widest">
                                    {formatSessionTime(session.start_time)}
                                </span>
                            </div>
                        </div>
                    </button>
                ))
            ) : (
                <div className="px-4 py-12 text-center border border-dashed border-gray-800/50 rounded-[2rem] bg-gray-900/10">
                    <History className="w-8 h-8 text-gray-800 mx-auto mb-3 opacity-20" />
                    <p className="text-[11px] font-bold text-gray-700 uppercase tracking-widest leading-relaxed">No history<br/>found yet</p>
                </div>
            )}
          </div>
        </div>
      </nav>

      <div className="p-6 border-t border-gray-800/60 bg-[#0c0e12]/80 backdrop-blur-md">
        <div className="flex items-center gap-4 px-1">
          <div className="relative group cursor-pointer">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-green-600 to-emerald-700 flex items-center justify-center shadow-lg shadow-green-900/30 text-white transition-transform group-hover:scale-105">
                <User size={22} className="drop-shadow-md" />
            </div>
            <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-emerald-500 border-4 border-[#0c0e12] rounded-full shadow-lg shadow-green-900/40"></div>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-extrabold truncate tracking-tight">Farmer Harsh</p>
            <p className="text-[10px] text-green-500/90 font-bold tracking-[0.05em] flex items-center gap-1.5 uppercase">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]"></span>
                Premium User
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;

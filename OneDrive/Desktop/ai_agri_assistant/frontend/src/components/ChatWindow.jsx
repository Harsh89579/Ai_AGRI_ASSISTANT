import React, { useRef, useEffect } from 'react';
import MessageCard from './MessageCard';
import { motion, AnimatePresence } from 'framer-motion';
import { Leaf, Sparkles, Sprout, Wind } from 'lucide-react';

const ChatWindow = ({ messages, isLoading, onQuickAction }) => {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      const scrollHeight = scrollRef.current.scrollHeight;
      scrollRef.current.scrollTo({
        top: scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages, isLoading]);

  const quickActions = [
    { text: "Gehu ki unnat kismein", icon: <Sprout size={16} /> },
    { text: "Khaad ki sahi matra", icon: <Wind size={16} /> },
    { text: "Fasal ki bimariyaan", icon: <Leaf size={16} /> },
    { text: "Sinchai ka sahee samay", icon: <Sparkles size={16} /> },
  ];

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 md:px-12 lg:px-24 scrollbar-hide" ref={scrollRef}>
      <div className="max-w-4xl mx-auto space-y-6">
        <AnimatePresence initial={false} mode="popLayout">
          {messages.length === 0 && !isLoading && (
            <motion.div 
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-col items-center justify-center py-16 text-center"
            >
              <div className="relative mb-10 group">
                <div className="absolute inset-0 bg-green-500 blur-[80px] opacity-20 group-hover:opacity-30 transition-opacity animate-pulse"></div>
                <div className="relative w-28 h-28 bg-gradient-to-tr from-green-600 via-emerald-600 to-green-500 rounded-[2.5rem] flex items-center justify-center shadow-[0_20px_50px_rgba(22,163,74,0.3)] border border-green-400/30 transform group-hover:rotate-3 transition-transform duration-500">
                  <Leaf size={52} className="text-white drop-shadow-2xl" />
                </div>
                <motion.div 
                  animate={{ y: [0, -8, 0] }}
                  transition={{ repeat: Infinity, duration: 3 }}
                  className="absolute -top-3 -right-3 w-10 h-10 bg-[#1a1c23] border border-gray-800 rounded-2xl flex items-center justify-center text-sm shadow-xl"
                >
                    🌟
                </motion.div>
              </div>

              <h2 className="text-4xl md:text-5xl font-extrabold text-white mb-6 tracking-tight font-outfit leading-tight">
                Swagat hai, <span className="bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">Kisari Mitra!</span>
              </h2>
              <p className="text-gray-400 max-w-xl mx-auto text-lg font-medium leading-relaxed mb-14 px-4">
                Main aapka agriculture expert AI hoon. Fasal ki paidaawar badhane aur kheti se judi samasyaon ke liye mujhse puchein.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-2xl px-4">
                {quickActions.map((action, i) => (
                  <motion.button
                    key={i}
                    whileHover={{ 
                        scale: 1.03, 
                        backgroundColor: 'rgba(34, 197, 94, 0.08)',
                        borderColor: 'rgba(34, 197, 94, 0.3)'
                    }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => onQuickAction && onQuickAction(action.text)}
                    className="flex items-center gap-4 p-5 rounded-[2rem] bg-[#16191f]/40 border border-gray-800/80 text-left transition-all group shadow-sm backdrop-blur-sm"
                  >
                    <div className="p-3.5 rounded-2xl bg-gray-800/80 text-green-500 group-hover:bg-green-600 group-hover:text-white transition-all duration-300 shadow-inner group-hover:shadow-green-900/40">
                        {action.icon}
                    </div>
                    <span className="text-sm font-bold text-gray-300 group-hover:text-white tracking-wide">
                        {action.text}
                    </span>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}

          {messages.map((msg, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              layout
            >
              <MessageCard message={msg} onAction={onQuickAction} />
            </motion.div>
          ))}
          
          {isLoading && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex justify-start pl-2"
              layout
            >
              <div className="bg-[#16191f]/80 backdrop-blur-xl px-6 py-4 rounded-[2.5rem] border border-gray-800/60 flex items-center gap-4 shadow-2xl">
                <div className="flex gap-2">
                  {[0, 1, 2].map(i => (
                    <span 
                        key={i}
                        className="w-2.5 h-2.5 bg-green-500 rounded-full animate-bounce shadow-[0_0_10px_rgba(34,197,94,0.4)]" 
                        style={{ animationDelay: `${i * 150}ms` }}
                    ></span>
                  ))}
                </div>
                <span className="text-[10px] text-green-500/80 font-black uppercase tracking-[0.25em] italic">AI is thinking</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ChatWindow;

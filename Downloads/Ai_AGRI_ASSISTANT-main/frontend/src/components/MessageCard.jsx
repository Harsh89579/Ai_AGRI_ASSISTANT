import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, User, Share2, Copy, Check, Info, Sparkles, Database } from 'lucide-react';

const MessageCard = ({ message, onAction }) => {
  const isBot = message.role === 'bot';
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getSourceBadge = (source) => {
    switch(source) {
      case 'knowledge_base':
        return (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] text-emerald-500 font-black uppercase tracking-[0.1em]">
            <Database size={10} />
            Verified Knowledge
          </div>
        );
      case 'llm':
        return (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-[10px] text-blue-400 font-black uppercase tracking-[0.1em]">
            <Sparkles size={10} />
            AI Expert Advice
          </div>
        );
      case 'error':
        return (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-[10px] text-red-500 font-black uppercase tracking-[0.1em]">
            <Info size={10} />
            System Warning
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className={`flex w-full mb-2 ${isBot ? 'justify-start' : 'justify-end'}`}>
        <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            className={`flex gap-4 p-5 max-w-[85%] md:max-w-[75%] transition-all duration-300 group relative ${
                isBot 
                ? 'bg-[#16191f]/60 backdrop-blur-md border border-gray-800/80 rounded-t-[2rem] rounded-br-[2rem] rounded-bl-lg' 
                : 'bg-green-600/15 border border-green-500/30 rounded-t-[2rem] rounded-bl-[2rem] rounded-br-lg'
            } shadow-lg hover:shadow-xl hover:border-gray-700/50`}
        >
            {isBot && (
                <div className="w-10 h-10 rounded-2xl shrink-0 flex items-center justify-center bg-gradient-to-tr from-gray-800 to-gray-700 text-green-400 shadow-xl border border-gray-700/50 hidden md:flex">
                    <Bot size={20} />
                </div>
            )}

            <div className="flex-1 space-y-2.5 min-w-0">
                <div className="flex items-center justify-between mb-1">
                    <span className={`text-[10px] font-black uppercase tracking-[0.2em] ${isBot ? 'text-green-500' : 'text-blue-400'}`}>
                        {isBot ? 'Agri Assistant' : 'Your Query'}
                    </span>
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                        <button 
                            onClick={handleCopy}
                            className="p-1.5 rounded-lg hover:bg-white/5 text-gray-500 hover:text-white transition-all"
                            title="Copy text"
                        >
                            {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                        </button>
                        <button className="p-1.5 rounded-lg hover:bg-white/5 text-gray-500 hover:text-white transition-all">
                            <Share2 size={14} />
                        </button>
                    </div>
                </div>

                <p className={`text-[15px] md:text-base leading-relaxed font-medium ${isBot ? 'text-gray-100' : 'text-green-50'}`}>
                    {message.content}
                </p>

                {isBot && (
                    <div className="space-y-4 pt-1">
                        {message.source && getSourceBadge(message.source)}
                        
                        {message.follow_ups && message.follow_ups.length > 0 && (
                            <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-800/50">
                                {message.follow_ups.map((q, i) => (
                                    <button
                                        key={i}
                                        onClick={() => onAction && onAction(q)}
                                        className="text-[11px] font-bold px-4 py-2 bg-gray-800/40 hover:bg-green-500/10 text-green-400/90 hover:text-green-400 rounded-xl border border-gray-700/50 hover:border-green-500/40 transition-all duration-300 active:scale-95 shadow-sm"
                                    >
                                        {q}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {!isBot && (
                <div className="w-10 h-10 rounded-2xl shrink-0 flex items-center justify-center bg-gradient-to-tr from-green-500 to-emerald-600 text-white shadow-xl shadow-green-900/20 hidden md:flex">
                    <User size={20} />
                </div>
            )}
        </motion.div>
    </div>
  );
};

export default MessageCard;

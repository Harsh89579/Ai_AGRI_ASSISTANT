import React, { useState, useEffect } from 'react';
import { Send, Leaf, Command, Mic, MicOff } from 'lucide-react';
import { motion } from 'framer-motion';

const InputBar = ({ onSend, isLoading }) => {
  const [text, setText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = false;
      rec.lang = 'hi-IN'; // Suitable for Hinglish/Hindi

      rec.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setText((prev) => prev ? prev + ' ' + transcript : transcript);
      };

      rec.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        setIsListening(false);
      };

      rec.onend = () => {
        setIsListening(false);
      };

      setRecognition(rec);
    }
  }, []);

  const toggleListening = (e) => {
    e.preventDefault();
    if (isListening) {
      recognition?.stop();
    } else {
      recognition?.start();
      setIsListening(true);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim() && !isLoading) {
      onSend(text);
      setText('');
    }
  };

  return (
    <form 
      onSubmit={handleSubmit}
      className="max-w-4xl mx-auto relative group"
    >
      <div className="absolute inset-y-0 left-7 flex items-center pointer-events-none z-10">
        <div className={`p-2 rounded-xl transition-all duration-500 shadow-sm ${text.trim() ? 'bg-green-500/20 text-green-400 scale-110 shadow-green-500/20' : 'bg-gray-800/40 text-gray-600'}`}>
            <Leaf className={`w-5 h-5 ${text.trim() ? 'animate-pulse' : ''}`} />
        </div>
      </div>
      
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={isLoading}
        placeholder="Apna sawal yahan likhein (e.g. Mitti ki jaanch kaise karein?)..."
        className="w-full h-20 bg-[#16191f]/40 backdrop-blur-2xl border border-gray-800/80 focus:border-green-500/40 focus:ring-[15px] focus:ring-green-500/5 rounded-[2.5rem] pl-20 pr-32 text-gray-100 text-lg placeholder:text-gray-600 transition-all duration-500 outline-none shadow-2xl overflow-hidden font-medium"
      />
      
      <div className="absolute right-3.5 top-1/2 -translate-y-1/2 flex items-center gap-2.5">
        {recognition && (
            <motion.button
              type="button"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={toggleListening}
              className={`p-3.5 rounded-2xl transition-all duration-500 border ${
                isListening 
                ? 'bg-red-500/20 text-red-500 border-red-500/40 shadow-[0_0_15px_rgba(239,68,68,0.3)] animate-pulse' 
                : 'bg-gray-800/60 hover:bg-gray-700 text-gray-400 hover:text-white border-gray-700/50'
              }`}
              title={isListening ? 'Listening...' : 'Use Voice Input'}
            >
              {isListening ? <MicOff size={20} /> : <Mic size={20} />}
            </motion.button>
        )}
        
        <button
            type="submit"
            disabled={!text.trim() || isLoading}
            className={`p-4 rounded-2xl transition-all duration-500 shadow-2xl flex items-center justify-center border group/btn ${
                !text.trim() || isLoading
                ? 'bg-gray-800/40 text-gray-700 border-gray-800/50 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-500 text-white border-green-400/30 shadow-green-900/30 active:scale-90'
            }`}
        >
            <Send className={`w-6 h-6 transition-transform duration-500 ${!text.trim() ? '' : 'group-hover/btn:translate-x-1 group-hover/btn:-translate-y-1'} ${isLoading ? 'animate-pulse' : ''}`} />
        </button>
      </div>

      <div className="mt-8 px-10 flex justify-between items-center opacity-70 hover:opacity-100 transition-opacity">
        <div className="flex items-center gap-4">
            <div className="flex -space-x-2.5">
                {[1, 2, 3].map(i => (
                    <div key={i} className={`w-6 h-6 rounded-full border-2 border-[#0c0e12] bg-gray-900 flex items-center justify-center shadow-md`}>
                        <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)]"></div>
                    </div>
                ))}
            </div>
            <p className="text-[10px] text-gray-500 font-extrabold uppercase tracking-[0.2em]">
                Secure Hybrid Engine
            </p>
        </div>
        <div className="flex items-center gap-2 group cursor-help">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]"></div>
          <span className="text-[10px] text-gray-500 font-black uppercase tracking-[0.2em] group-hover:text-emerald-400 transition-colors">
            End-to-end encrypted
          </span>
        </div>
      </div>
    </form>
  );
};

export default InputBar;

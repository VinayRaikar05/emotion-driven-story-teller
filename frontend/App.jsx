import React, { useRef, useEffect } from "react";
import StoryInput from "./components/StoryInput";
import Navbar from "./components/Navbar";
import Typed from "typed.js";

function App() {
  const typingRef = useRef(null);

  useEffect(() => {
    const typed = new Typed(typingRef.current, {
      strings: [
        "Welcome to Emotion Driven Storytelling",
        "Where AI Brings Stories to Life",
        "Discover the Power of Emotional Narratives",
        "Create Interactive Story Experiences",
        "Transform Your Stories with AI",
      ],
      typeSpeed: 60,
      backSpeed: 40,
      backDelay: 1500,
      loop: true,
      cursorChar: '✨',
    });

    return () => {
      typed.destroy();
    };
  }, []);

  return (
    <div className="App min-h-screen pt-24 pb-12 px-4 md:px-0">
      <Navbar />
      <header className="max-w-4xl mx-auto text-center mb-16 space-y-4 animate-fade-in">
        <div className="inline-block p-1 rounded-full bg-gradient-to-r from-primary-400/20 to-secondary-400/20 backdrop-blur-md border border-glass-border mb-4">
          <span className="px-4 py-1 text-xs font-mono text-primary-300">AI-Powered Immersion</span>
        </div>
        <h1 className="text-4xl md:text-6xl font-display font-bold leading-tight">
          <span ref={typingRef} className="bg-clip-text text-transparent bg-gradient-to-r from-primary-200 via-white to-secondary-200 drop-shadow-[0_0_15px_rgba(255,255,255,0.3)]"></span>
        </h1>
        <p className="text-gray-400 text-lg md:text-xl font-light max-w-2xl mx-auto">
          Experience stories that <span className="text-primary-400 font-semibold">feel</span> real. Powered by Gemini Pro and ElevenLabs.
        </p>
      </header>
      <main>
        <StoryInput />
      </main>
    </div>
  );
}

export default App;

import React, { useRef, useEffect } from "react";
import "./App.css";
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
      typeSpeed: 80,
      backSpeed: 50,
      backDelay: 1000,
      loop: true,
    });

    return () => {
      typed.destroy();
    };
  }, []);

  return (
    <div className="App">
      <Navbar />
      <header className="App-header">
        <h1 className="text-5xl font-serif">
          <span ref={typingRef}></span>
        </h1>
      </header>
      <main>
        <StoryInput />
      </main>
    </div>
  );
}

export default App;

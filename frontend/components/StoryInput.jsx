import React, { useState } from "react";

const StoryInput = () => {
  const [story, setStory] = useState("");
  const [fileContent, setFileContent] = useState("");
  const [extractedInfo, setExtractedInfo] = useState({ dialogues: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
  const [playlist, setPlaylist] = useState([]);
  const [currentTrackIndex, setCurrentTrackIndex] = useState(0);
  const audioRef = React.useRef(null);

  // Auto-play when audioUrl changes
  React.useEffect(() => {
    if (audioUrl && audioRef.current) {
      audioRef.current.load(); // Reload the element with new source
      audioRef.current.play().catch(e => console.error("Autoplay failed:", e));
    }
  }, [audioUrl]);

  // Helper to convert base64 to blob
  const base64ToBlob = (base64, type = "audio/mpeg") => {
    const binaryString = window.atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return new Blob([bytes], { type });
  };

  const API_KEY = import.meta.env.VITE_GEMINI_API_KEY || "";
  if (!API_KEY) {
    console.error("Missing VITE_GEMINI_API_KEY environment variable");
  }
  const API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${API_KEY}`;

  // Use environment variable for backend URL, default to localhost
  const BACKEND_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  // 📌 Handle File Upload
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsLoading(true);

    if (file.type === "application/pdf") {
      try {
        const formData = new FormData();
        formData.append("file", file);

        // Updated endpoint to match the backend
        // Updated endpoint to match the backend
        const response = await fetch(`${BACKEND_URL}/upload-script`, {
          method: "POST",
          body: formData,
          headers: {
            Accept: "application/json",
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        // Update the extracted info directly with the response
        setExtractedInfo({ dialogues: data });
        setFileContent(file.name);
      } catch (error) {
        console.error("Error processing PDF:", error);
        alert(`Error uploading file: ${error.message}`);
      } finally {
        setIsLoading(false);
      }
    }
  };

  // 📌 Generate Story using Gemini API
  // Format story text by removing stars and formatting scene narrations
  const formatStoryText = (text) => {
    // Remove standalone stars
    let formattedText = text.replace(/^\s*\*+\s*$/gm, "");

    // Format scene titles and settings
    formattedText = formattedText.replace(/^\*{2}([^*]+)\*{2}$/gm, "$1");

    // Remove extra newlines
    formattedText = formattedText.replace(/\n{3,}/g, "\n\n");

    return formattedText.trim();
  };

  const generateStory = async () => {
    try {
      setIsLoading(true);

      const requestBody = {
        contents: [
          {
            parts: [
              {
                text: "Generate a short story with multiple characters and a narrator. The story should have clear character interactions, MULTIPLE emotions, and narrative descriptions. Generate this story in a play/drama-like script format where character dialogues are marked as 'Character Name: [dialogue]' and narrative descriptions are marked as 'Narrator: [description]'. Include narrative descriptions between dialogues to set scenes and describe actions. Ensure proper formatting with each entry on a new line. Make sure you generate maximum of 6 dialogues and not more than that.",
              },
            ],
          },
        ],
      };

      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log("API Response:", data);

      // Extract and format the generated story text
      const rawStory =
        data.candidates?.[0]?.content?.parts?.[0]?.text ||
        "No story generated.";
      const formattedStory = formatStoryText(rawStory);
      setStory(formattedStory);

      // Extract character details from the formatted story
      await extractInformation(formattedStory);
    } catch (error) {
      console.error("Error generating story:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // 📌 Extract Characters & Dialogues (Without Gender Field)
  const extractInformation = async (text) => {
    try {
      // First, use Gemini API to extract dialogues
      const requestBody = {
        contents: [
          {
            parts: [
              {
                text: `Analyze the following story and extract all dialogues and narrative descriptions in the order they appear. 
                        Return ONLY a JSON array where each entry represents either a character's dialogue or a narrator's description. 
                        Use this exact JSON format:
                        
                        {"dialogues": [
                            {"id": 1, "name": "Speaker Name", "dialogue": "Spoken dialogue", "predicted_gender": "Male/Female"},
                            {"id": 2, "name": "Narrator", "dialogue": "Narrative description or scene setting", "predicted_gender": "Male/Female"},
                            {"id": 3, "name": "Next Speaker", "dialogue": "Next spoken dialogue", "predicted_gender": "Male/Female"}
                        ]}
                        
                        Treat narrative descriptions as dialogues with "Narrator" as the speaker name. Make sure that the gender of the Narrator is always "Male".
                        Do NOT return any explanations, markdown formatting, or additional text.

                        Story: ${text}`,
              },
            ],
          },
        ],
      };

      const geminiResponse = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!geminiResponse.ok) {
        throw new Error(
          `Gemini API Error: ${geminiResponse.status} ${geminiResponse.statusText}`
        );
      }

      const geminiData = await geminiResponse.json();
      const analysisText =
        geminiData.candidates?.[0]?.content?.parts?.[0]?.text || "{}";

      // Clean the response and parse JSON
      const cleanJson = analysisText.replace(/```json\n|\n```|```/g, "").trim();
      const initialAnalysis = JSON.parse(cleanJson);
      setExtractedInfo(initialAnalysis);
    } catch (error) {
      console.error("Error analyzing story:", error);
      setExtractedInfo({ dialogues: [] });
    }
  };

  // 📌 Proceed to Emotion Detection
  const proceedToEmotionDetection = async () => {
    try {
      setIsLoading(true);
      const dialogueList = {
        dialogues: extractedInfo.dialogues.map((d) => ({
          name: d.name,
          dialogue: d.dialogue,
          predicted_gender: d.predicted_gender || null,
          emotion: null,
        })),
      };
      const response = await fetch(`${BACKEND_URL}/detect-emotions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(dialogueList),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const updatedDialogues = await response.json();
      setExtractedInfo({ dialogues: updatedDialogues });
    } catch (error) {
      console.error("Error detecting emotions:", error);
      alert(`Error detecting emotions: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Add this function to handle audio generation
  // 📌 Handle Audio Generation with Async Polling
  const handleGenerateAudio = async () => {
    setIsGeneratingAudio(true);
    setAudioUrl(null);

    try {
      // 1. Start the job
      const response = await fetch(`${BACKEND_URL}/generate-audio`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Check content type first
      const contentType = response.headers.get("content-type");

      // If backend returns a file directly (legacy mode / NO_REDIS), handle it
      if (contentType && contentType.includes("audio")) {
        const audioBlob = await response.blob();
        // Create blob with explicit type to ensure browser plays it
        const typedBlob = new Blob([audioBlob], { type: "audio/mpeg" });
        const url = URL.createObjectURL(typedBlob);
        setAudioUrl(url);
        setIsGeneratingAudio(false);
        return;
      }

      // Otherwise expect JSON response
      const data = await response.json();

      // Handle Playlist Response (NO_REDIS + No FFmpeg)
      if (data.type === "audio_playlist") {
        const segments = data.data; // Array of base64 strings
        const urls = segments.map(b64 => URL.createObjectURL(base64ToBlob(b64)));

        setPlaylist(urls);
        setCurrentTrackIndex(0);
        setAudioUrl(urls[0]);
        setIsGeneratingAudio(false);
        return;
      }

      // 2. Poll for completion (Async job details)

      // 2. Poll for completion
      const jobId = data.job_id;
      if (!jobId) throw new Error("No job ID returned");

      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(`${BACKEND_URL}/jobs/${jobId}`);
          const statusData = await statusRes.json();

          if (statusData.status === "completed") {
            clearInterval(pollInterval);

            // If download_url is provided (S3), use it. Otherwise construct local URL
            let downloadUrl = statusData.download_url;

            // If local dev and no S3, we might need to fetch the file blob
            if (!downloadUrl) {
              console.error("No download URL provided in completed job");
              alert("Audio generated but no download URL found.");
              return;
            }

            setAudioUrl(downloadUrl);
            setIsGeneratingAudio(false);
          } else if (statusData.status === "failed") {
            clearInterval(pollInterval);
            throw new Error(statusData.error || "Job failed");
          }
          // If queued or processing, continue polling
        } catch (err) {
          console.error("Polling error:", err);
          clearInterval(pollInterval);
          setIsGeneratingAudio(false);
          alert("Error checking job status");
        }
      }, 2000); // Poll every 2 seconds

    } catch (error) {
      console.error("Error generating audio:", error);
      alert("Error generating audio. Please try again.");
      setIsGeneratingAudio(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8 animate-fade-in">
      <h2 className="text-4xl font-bold text-primary-300 mb-8 animate-slide-up">
        Story Input
      </h2>
      {/* File Upload Section */}
      <div className="card flex flex-col items-center justify-center">
        <h3 className="text-2xl font-semibold text-primary-200 mb-4 text-center">
          Upload Story File
        </h3>
        <label className="block w-full max-w-md text-center">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            className="input-field w-full file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-primary-600 file:text-white hover:file:bg-primary-700 cursor-pointer text-center"
          />
        </label>
      </div>
      {/* Story Generation Section */}
      <div className="card">
        <h3 className="text-2xl font-semibold text-primary-200 mb-4">
          Or Generate Story
        </h3>
        <button
          onClick={generateStory}
          disabled={isLoading}
          className="btn-primary w-full md:w-auto disabled:opacity-50 disabled:cursor-not-allowed animate-pulse-slow"
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Generating...
            </span>
          ) : (
            "Generate Story"
          )}
        </button>
      </div>
      {/* Story Preview Section */}
      {(fileContent || story) && (
        <div className="space-y-6 animate-slide-up">
          <div className="card">
            <h3 className="text-2xl font-semibold text-primary-200 mb-4">
              Story Content
            </h3>
            <div className="text-gray-300 text-left font-mono space-y-4">
              {extractedInfo.dialogues.map((entry, index) => (
                <div key={index} className="flex items-start space-x-4 mb-2">
                  {entry.name === "Narrator" ? (
                    <div className="flex-grow italic">[{entry.dialogue}]</div>
                  ) : (
                    <>
                      <div className="w-24 flex-shrink-0 font-bold text-blue-400">
                        {entry.name}:
                      </div>
                      <div className="flex-grow">{entry.dialogue}</div>
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Extracted Character Info */}
          <div className="card">
            <h3 className="text-2xl font-semibold text-primary-200 mb-4">
              Extracted Dialogues
            </h3>
            <pre className="bg-gray-900 p-4 rounded-lg overflow-x-auto text-sm text-gray-300">
              {JSON.stringify(extractedInfo, null, 2)}
            </pre>
          </div>

          {/* Proceed Button */}
          <button
            onClick={proceedToEmotionDetection}
            className="btn-primary w-full md:w-auto mx-auto block mt-8 text-lg animate-pulse-slow"
          >
            Proceed to Emotion Detection
          </button>
        </div>
      )}
      {/* // Add this JSX after your emotion detection results */}
      {extractedInfo.dialogues.length > 0 && (
        <div className="mt-8 flex flex-col items-center gap-4 animate-fade-in">
          <button
            onClick={handleGenerateAudio}
            disabled={isGeneratingAudio}
            className={`px-6 py-3 bg-accent-red rounded-full 
        transition-all duration-300 hover:bg-accent-red/80
        disabled:opacity-50 disabled:cursor-not-allowed
        flex items-center justify-center gap-2
        ${isGeneratingAudio ? "animate-pulse" : ""}`}
          >
            {isGeneratingAudio ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Generating Audio...
              </>
            ) : (
              <>
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15.536a5 5 0 001.414 1.414m2.828-9.9a9 9 0 012.728-2.728"
                  />
                </svg>
                Generate Audio
              </>
            )}
          </button>

          {audioUrl && (
            <div className="w-full max-w-md animate-fade-in">
              <audio
                key={audioUrl}
                controls
                autoPlay
                className="w-full mt-4"
                src={audioUrl}
                onEnded={() => {
                  if (currentTrackIndex < playlist.length - 1) {
                    const nextIndex = currentTrackIndex + 1;
                    setCurrentTrackIndex(nextIndex);
                    setAudioUrl(playlist[nextIndex]);
                  }
                }}
              >
                Your browser does not support the audio element.
              </audio>
              {/* Only show download if it's a single file, or maybe just disable download for playlist because it's tricky? 
                  With playlist, audioUrl changes. It's fine to download individual segments. */}
              {playlist.length === 0 && (
                <a
                  href={audioUrl}
                  download="story_audio.mp3"
                  className="mt-2 text-accent-red hover:text-accent-red/80 flex items-center justify-center gap-2"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                  Download Audio
                </a>
              )}
              {playlist.length > 0 && (
                <p className="text-sm text-gray-400 text-center mt-2">
                  Playing segment {currentTrackIndex + 1} of {playlist.length} (Playlist Mode)
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StoryInput;

// Add these state variables at the top of your component

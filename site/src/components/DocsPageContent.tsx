import Link from "next/link";
import Image from "next/image"; 
import { BookOpen, Zap, Settings, Share2, Smartphone, Layers, Play, ExternalLink, Lightbulb, Construction, History } from "lucide-react"; // Added more icons

const SectionTitle: React.FC<{ title: string; icon?: React.ReactNode; id?: string }> = ({ title, icon, id }) => (
  <h2 id={id} className="text-3xl font-bold mt-12 mb-6 pb-3 border-b border-slate-700 flex items-center scroll-mt-20">
    {icon && <span className="mr-3">{icon}</span>}
    {title}
  </h2>
);

const SubTitle: React.FC<{ title: string; id?: string }> = ({ title, id }) => (
  <h3 id={id} className="text-2xl font-semibold mt-8 mb-4 text-sky-400 scroll-mt-20">
    {title}
  </h3>
);

const CodeBlock: React.FC<{ language?: string; children: string }> = ({ language = "bash", children }) => (
  <pre className="bg-slate-800 p-4 rounded-md overflow-x-auto my-4">
    <code className={`language-${language} text-sm text-slate-200 font-mono`}>{children.trim()}</code>
  </pre>
);

const ListItem: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <li className="mb-2 ml-4 list-disc text-slate-300 leading-relaxed">{children}</li>
);

export default function DocsPageContent() {
  return (
    <div className="container mx-auto px-4 md:px-8 py-12 text-slate-200 max-w-4xl">
      <header className="text-center mb-16">
        <h1 className="text-5xl font-extrabold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-blue-500">
          Orka Documentation
        </h1>
        <p className="text-xl text-slate-400">
          Your comprehensive guide to understanding, setting up, and using the Orka framework.
        </p>
      </header>

      {/* Table of Contents will keep this dynamiic later*/}
      <nav className="bg-slate-800/50 p-6 rounded-lg mb-12 top-20 z-10 backdrop-blur-md">
        <h3 className="text-xl font-semibold mb-3 text-slate-100">On this page</h3>
        <ul className="space-y-1.5 text-sm">
            <li><Link href="#what-is-orka" className="text-sky-300 hover:text-sky-200 hover:underline">What is Orka?</Link></li>
            <li><Link href="#getting-started" className="text-sky-300 hover:text-sky-200 hover:underline">Getting Started</Link></li>
            <li><Link href="#modes-of-operation" className="text-sky-300 hover:text-sky-200 hover:underline">Modes of Operation</Link></li>
            <li><Link href="#features" className="text-sky-300 hover:text-sky-200 hover:underline">Core Features</Link></li>
            <li><Link href="#api-reference" className="text-sky-300 hover:text-sky-200 hover:underline">API Reference</Link></li>
            <li><Link href="#configuration" className="text-sky-300 hover:text-sky-200 hover:underline">Configuration</Link></li>
            <li><Link href="#cross-platform-support" className="text-sky-300 hover:text-sky-200 hover:underline">Cross-Platform Support</Link></li>
            <li><Link href="#use-cases" className="text-sky-300 hover:text-sky-200 hover:underline">Use Cases</Link></li>
            <li><Link href="#development" className="text-sky-300 hover:text-sky-200 hover:underline">Development & History</Link></li>
        </ul>
      </nav>

      <SectionTitle title="What is Orka?" icon={<BookOpen className="w-7 h-7 text-sky-400" />} id="what-is-orka" />
      <p className="text-slate-300 leading-relaxed mb-4">
        Orka (Orchestrator Kernel for Agents) is a Python framework for building and controlling modular AI agents across multiple platforms including Linux, Android (via Termux), Raspberry Pi, and potentially microcontrollers.
      </p>
      <p className="text-slate-300 leading-relaxed">
        It provides a flexible infrastructure for:
      </p>
      <ul className="list-disc list-inside text-slate-300 my-4 space-y-2">
        <li>Creating AI agents with configurable personas and behaviors.</li>
        <li>Running on various hardware platforms from smartphones to embedded systems.</li>
        <li>Supporting multiple LLM providers (currently focusing on Gemini).</li>
        <li>Enabling hardware interaction (audio, camera, sensors) across platforms.</li>
        <li>Providing a unified interface regardless of underlying hardware.</li>
      </ul>

      <SectionTitle title="Getting Started" icon={<Play className="w-7 h-7 text-green-400" />} id="getting-started" />
      <SubTitle title="Prerequisites" id="prerequisites" />
      <ul className="list-disc list-inside text-slate-300 mb-4">
        <li>Python 3.8 or higher</li>
        <li>pip (Python package installer)</li>
        <li>Git</li>
      </ul>

      <SubTitle title="1. Clone the Repository" id="clone-repo" />
      <CodeBlock language="bash">
        {`git clone https://github.com/mostlyKIGuess/Orka.git
cd Orka`}
      </CodeBlock>

      <SubTitle title="2. API Key Setup" id="api-key-setup" />
      <p className="text-slate-300">
        Orka uses the Gemini API for its LLM capabilities.
      </p>
      <ul className="list-disc list-inside text-slate-300 my-2">
        <li>Obtain a Gemini API key from <Link href="https://aistudio.google.com/" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">Google AI Studio <ExternalLink className="inline w-4 h-4 ml-1" /></Link>.</li>
        <li>Create a <code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">.env</code> file in the project root directory.</li>
        <li>Add your API key to the <code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">.env</code> file:</li>
      </ul>
      <CodeBlock language="dotenv">GEMINI_API_KEY=YOUR_API_KEY_HERE</CodeBlock>

      <SubTitle title="3. Installation" id="installation" />
      <p className="text-slate-300">Install the core dependencies for all platforms:</p>
      <CodeBlock language="bash">pip install -r requirements.txt</CodeBlock>
      <p className="text-slate-300 mt-2">
        For platform-specific setup (Android/Termux, Raspberry Pi, Linux Desktop), please refer to the <Link href="#cross-platform-support" className="text-sky-400 hover:underline">Cross-Platform Support</Link> section below or the detailed instructions in the 
        <Link href="https://github.com/mostlyKIGuess/Orka#readme" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline"> main README.md <ExternalLink className="inline w-4 h-4 ml-1" /></Link>.
      </p>

      <SectionTitle title="Modes of Operation" icon={<Layers className="w-7 h-7 text-orange-400" />} id="modes-of-operation" />
      <p className="text-slate-300 mb-4">Orka can operate in two primary modes: client-server (distributed) and standalone (local).</p>

      <SubTitle title="1. Client-Server Mode" id="client-server-mode" />
      <p className="text-slate-300 leading-relaxed">
        In this mode, multiple clients (agents) connect to a central server for orchestration and remote control. The server provides a web dashboard for monitoring and interaction.
      </p>
      <p className="text-slate-300 font-semibold mt-3 mb-1">Running the Server:</p>
      <CodeBlock language="bash">{`python server/main_server.py\n# Or for development with auto-reload:\n# uvicorn server.main_server:app --reload --host 0.0.0.0 --port 8000`}</CodeBlock>
      <p className="text-slate-300">Access the dashboard at <Link href="http://localhost:8000/dashboard" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">http://localhost:8000/dashboard <ExternalLink className="inline w-4 h-4 ml-1" /></Link>.</p>
      
      <p className="text-slate-300 font-semibold mt-3 mb-1">Running a Client:</p>
      <CodeBlock language="bash">python client/main_client.py --server ws://&lt;server-ip&gt;:8000/&lt;client_name&gt;</CodeBlock>
      <p className="text-slate-300">Replace <code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">&lt;server-ip&gt;</code> with your server&apos;s IP address and <code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">&lt;client_name&gt;</code> with a unique name for the client.</p>

      <SubTitle title="2. Standalone Mode" id="standalone-mode" />
      <p className="text-slate-300 leading-relaxed">
        The agent operates independently on a single device without connecting to a central server. This is useful for personal assistants, offline tasks, or rapid prototyping.
      </p>
      <p className="text-slate-300 font-semibold mt-3 mb-1">Running in Standalone Mode:</p>
      <CodeBlock language="bash">python client/main_client.py --standalone</CodeBlock>
      <p className="text-slate-300">This is equivalent to running the <code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">main.py</code> script in the project root.</p>

      <SubTitle title="3. Both Modes (Client & Server on one machine)" id="both-modes" />
       <p className="text-slate-300 leading-relaxed">
        For development or testing on a single machine, you can run both the server and a client that connects to it.
      </p>
      <CodeBlock language="bash">python client/main_client.py --both --server ws://localhost:8000</CodeBlock>

      <SubTitle title="Switching Between Modes" id="switching-modes" />
      <p className="text-slate-300">
        Use command-line arguments with <code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">client/main_client.py</code>:
      </p>
      <ul className="list-disc list-inside text-slate-300 my-2">
        <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">--server ws://YOUR_SERVER_IP:8000/YOUR_CLIENT_NAME</code>: Client mode.</li>
        <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">--standalone</code>: Standalone mode.</li>
        <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">--both --server ws://localhost:8000/YOUR_CLIENT_NAME</code>: Runs both server and client locally.</li>
      </ul>
      <p className="text-slate-300">Configuration for each mode can also be set in <Link href="#configuration" className="text-sky-400 hover:underline">config.py</Link> or overridden via command-line arguments.</p>

      <SectionTitle title="Core Features" icon={<Zap className="w-7 h-7 text-purple-400" />} id="features" />
      <SubTitle title="1. Remote Client Management" id="feature-remote-management"/>
      <ListItem>Register and monitor clients: Clients connect via WebSocket, register with name, platform, and capabilities.</ListItem>
      <ListItem>Live dashboard: View all connected clients, their status, last seen, and capabilities in real time.</ListItem>
      <ListItem>Client detail panel: Inspect individual clients, their streams, and control them via the web UI.</ListItem>
      
      <SubTitle title="2. Remote Commands & Automation" id="feature-remote-commands"/>
      <ListItem>Text-to-Speech: Send text to a client for speech output (if supported).</ListItem>
      <ListItem>Image Capture: Remotely trigger a client to capture and upload an image.</ListItem>
      <ListItem>Video Streaming: Start/stop video streams from clients, view stream status, and record streams on the server.</ListItem>

      <SubTitle title="3. Media Handling" id="feature-media-handling"/>
      <ListItem>Image saving: Images captured from clients are saved on the server.</ListItem>
      <ListItem>Video recording: Video streams can be recorded and saved as MP4 files.</ListItem>
      <ListItem>Stream status: Monitor and control recording state for each stream.</ListItem>

      <SubTitle title="4. Web UI" id="feature-web-ui"/>
      <ListItem>Dashboard: Real-time, auto-refreshing dashboard for all clients.</ListItem>
      <ListItem>Client cards: Quick view of client status, capabilities, and active streams.</ListItem>
      <ListItem>Stream viewer: View stream info, control recording, and see stream health (SLAM visualization is currently generated and not functional).</ListItem>
      <ListItem>AJAX updates: UI updates client cards and stream status without full page reloads.</ListItem>
      
      <SectionTitle title="API Reference" icon={<Share2 className="w-7 h-7 text-teal-400" />} id="api-reference" />
      <SubTitle title="WebSocket API" id="websocket-api" />
      <p className="text-slate-300">
        Main endpoint for clients: <code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">ws://&lt;server-ip&gt;:8000/&lt;client_name&gt;</code>
      </p>
      <p className="text-slate-300 font-semibold mt-3 mb-1">Key Message Types:</p>
      <ul className="list-disc list-inside text-slate-300 my-2 space-y-1">
        <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">register</code>: Client registration (first message, with payload: client_name, platform, capabilities).</li>
        <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">command</code>: Server-to-client command (payload: action, params).</li>
        <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">command_response</code>: Client-to-server command response (payload: command_id, status, data, error_message).</li>
        <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">ping</code> / <code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">pong</code>: Heartbeat messages.</li>
        <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">stream_status</code>: Client stream status updates.</li>
        <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">media_ack</code>: Server acknowledges receipt of binary media.</li>
      </ul>
       <p className="text-slate-300 font-semibold mt-3 mb-1">Binary Media Format:</p>
       <ul className="list-disc list-inside text-slate-300 my-2 space-y-1">
        <li>Prefix (4 bytes): &quot;IMG:&quot; or &quot;VID:&quot;</li>
        <li>Sequence (4 bytes, big-endian)</li>
        <li>Stream ID (null-terminated UTF-8 string)</li>
        <li>Media payload (image or video frame bytes)</li>
      </ul>

      <SubTitle title="HTTP REST API" id="http-api" />
      <p className="text-slate-300 my-2">
        Access the auto-generated OpenAPI documentation by running the Orka server and navigating to 
        <Link href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline"> http://localhost:8000/docs <ExternalLink className="inline w-4 h-4 ml-1" /></Link> in your browser.
      </p>
      <div className="my-6 p-4 bg-slate-800 rounded-lg shadow-md">
        <Image src="/docs.png" alt="Orka FastAPI Docs Screenshot" width={800} height={500} className="rounded-md" />
      </div>
      <p className="text-slate-300 font-semibold mt-3 mb-1">Key Endpoints:</p>
      <ul className="list-disc list-inside text-slate-300 my-2">
        <li>Client Management:
          <ul className="list-disc list-inside ml-6 my-1">
            <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">GET /clients</code>: List all connected clients.</li>
            <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">GET /clients/{'{client_id}'}</code>: Get details for a specific client (UI).</li>
          </ul>
        </li>
        <li>Command Endpoints:
          <ul className="list-disc list-inside ml-6 my-1">
            <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">POST /clients/{'{client_id}'}/commands/{'{command_action}'}</code>: Send a command (e.g., speak_text, capture_image). Body: JSON params.</li>
          </ul>
        </li>
        <li>Stream Endpoints:
          <ul className="list-disc list-inside ml-6 my-1">
            <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">GET /streams/{'{stream_id}'}</code>: View stream info (UI).</li>
            <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">GET /streams/{'{stream_id}'}/status</code>: Get status of a specific stream (JSON).</li>
            <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">POST /streams/{'{stream_id}'}/record/{'{on|off}'}</code>: Start/stop recording.</li>
          </ul>
        </li>
         <li>Dashboard & UI Support:
          <ul className="list-disc list-inside ml-6 my-1">
            <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">GET /dashboard</code>: Main web dashboard.</li>
            <li><code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">GET /client_card_html/{'{client_id}'}</code>: HTML for a single client card (AJAX).</li>
          </ul>
        </li>
      </ul>

      <SectionTitle title="Configuration" icon={<Settings className="w-7 h-7 text-gray-400" />} id="configuration" />
      <p className="text-slate-300 leading-relaxed">
        Customize your agent by modifying <code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">config.py</code>:
      </p>
      <ul className="list-disc list-inside text-slate-300 my-4 space-y-2">
        <li>Change the agent&apos;s active persona (e.g., ROASTYY, HELPER, ANALYTICS).</li>
        <li>Configure different LLM models (vision and text models for Gemini).</li>
        <li>Adjust platform-specific settings (e.g., temp directories, microphone index).</li>
        <li>Define default capabilities for agents.</li>
      </ul>
      <p className="text-slate-300">
        Many settings can also be overridden via command-line arguments when launching server or client scripts. Check script help (<code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">-h</code> or <code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm">--help</code>) for available options.
      </p>

      <SectionTitle title="Cross-Platform Support" icon={<Smartphone className="w-7 h-7 text-lime-400" />} id="cross-platform-support" />
      <SubTitle title="Android with Termux" id="platform-android" />
      <p className="text-slate-300">1. Install <Link href="https://f-droid.org/packages/com.termux/" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">Termux <ExternalLink className="inline w-4 h-4 ml-1" /></Link> and <Link href="https://f-droid.org/packages/com.termux.api/" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">Termux:API <ExternalLink className="inline w-4 h-4 ml-1" /></Link>.</p>
      <p className="text-slate-300">2. Install required packages:</p>
      <CodeBlock language="bash">{`pkg update && pkg upgrade\npkg install python git termux-api\npip install -r requirements.txt`}</CodeBlock>
      <p className="text-slate-300">3. Grant necessary permissions (camera, microphone, storage) via Termux:API.</p>
      
      <SubTitle title="Raspberry Pi Setup" id="platform-rpi" />
      <p className="text-slate-300">1. Install system dependencies:</p>
      <CodeBlock language="bash">{`sudo apt-get update\nsudo apt-get install espeak python3-pip git portaudio19-dev`}</CodeBlock>
      <p className="text-slate-300">2. For camera support (choose one):</p>
      <ul className="list-disc list-inside text-slate-300 my-2">
        <li>RPi Camera Module: <CodeBlock language="bash">pip install picamera2</CodeBlock></li>
        <li>USB Webcam: <CodeBlock language="bash">pip install opencv-python</CodeBlock></li>
      </ul>
      <p className="text-slate-300">3. For audio support:</p>
      <CodeBlock language="bash">pip install pyttsx3 SpeechRecognition PyAudio</CodeBlock>

      <SubTitle title="Linux Desktop Setup" id="platform-linux" />
      <p className="text-slate-300">1. Install system dependencies:</p>
      <CodeBlock language="bash">{`sudo apt-get update\nsudo apt-get install espeak python3-pip git portaudio19-dev`}</CodeBlock>
      <p className="text-slate-300">2. Install audio and camera libraries:</p>
      <CodeBlock language="bash">pip install pyttsx3 SpeechRecognition PyAudio opencv-python</CodeBlock>

      <SectionTitle title="Use Cases" icon={<Lightbulb className="w-7 h-7 text-yellow-400" />} id="use-cases" />
      <ul className="list-disc list-inside text-slate-300 my-4 space-y-2">
        <li>Personal assistant on a smartphone or Raspberry Pi.</li>
        <li>Remote monitoring and control of devices (e.g., home automation, security cameras).</li>
        <li>Interactive AI assistants on smartphones or embedded systems.</li>
        <li>Real-time data processing and analysis from multiple sources.</li>
        <li>Multi-agent systems for tasks like distributed environmental mapping or data collection.</li>
        <li>Educational tool for experiments with distributed AI and remote sensing.</li>
        <li>Content creation aid (e.g., automate lecture recording, note-taking).</li>
      </ul>
      
      <SectionTitle title="Development & History" icon={<Construction className="w-7 h-7 text-amber-500" />} id="development" />
      <p className="text-slate-300 leading-relaxed mb-2">
        Orka is under active development. While core functionalities are in place, some features like fully operational SLAM are still being refined.
      </p>
      <p className="text-slate-300 leading-relaxed">
        The project is designed to be extensible, welcoming contributions for:
      </p>
      <ul className="list-disc list-inside text-slate-300 my-4 space-y-2">
        <li>Additional LLM providers beyond Gemini.</li>
        <li>More hardware interactions and sensor support.</li>
        <li>Broader platform compatibility.</li>
      </ul>
      <SubTitle title="A Bit of History" id="history" />
       <p className="text-slate-300 leading-relaxed">
        <History className="inline w-5 h-5 mr-1 mb-1 text-slate-400" />
        Orka started as &quot;Roastyy&quot; a project aimed at creating a bot that could observe and humorously comment on its surroundings. It has since evolved into a more general-purpose agentic framework, focusing on modularity and extensibility. The early commit history reflects this origin. Lol but I never knew I would be doing this.
      </p>


      <div className="mt-20 text-center">
        <p className="text-slate-400">
          For more details, contributions, or to report issues, please visit the 
          <Link href="https://github.com/mostlyKIGuess/Orka" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline"> Orka GitHub repository <ExternalLink className="inline w-4 h-4 ml-1" /></Link>.
        </p>
      </div>
    </div>
  );
}

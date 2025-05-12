import {  Cpu, Layers, MonitorPlay, TerminalSquare, Zap, Code, DatabaseZap, Share2 } from "lucide-react"; 

const features = [
  {
    icon: <Layers className="w-8 h-8 text-sky-400" />,
    title: "Remote Client Management",
    description: "Live dashboard to monitor, inspect, and manage all connected AI agents in real-time. View client status, capabilities, and active streams.",
    link: "#features"
  },
  {
    icon: <TerminalSquare className="w-8 h-8 text-emerald-400" />,
    title: "Remote Commands & Automation",
    description: "Send commands for Text-to-Speech, image capture, video streaming, and trigger custom agent actions remotely.",
    link: "#features"
  },
  {
    icon: <MonitorPlay className="w-8 h-8 text-violet-400" />,
    title: "Advanced Media Handling",
    description: "Capture, save, and manage images and video recordings from your agents. Monitor and control recording state for each stream.",
    link: "#features"
  },
  {
    icon: <Cpu className="w-8 h-8 text-amber-400" />,
    title: "Cross-Platform Compatibility",
    description: "Run Orka agents seamlessly on Linux, Android (Termux), Raspberry Pi, and other platforms supporting Python.",
    link: "#features"
  },
  {
    icon: <Zap className="w-8 h-8 text-rose-400" />,
    title: "Real-time Web UI",
    description: "AJAX-powered dashboard with client cards, stream viewers, and controls for a responsive user experience without full page reloads.",
    link: "#features"
  },
];

// Updated use cases data based on README
const useCases = [
    { name: "Personal AI Assistants", description: "On smartphones (Android/Termux) or Raspberry Pi for on-the-go or embedded tasks." },
    { name: "Remote Monitoring & Control", description: "For home automation, security cameras, or managing fleets of IoT devices." },
    { name: "Multi-Agent Systems", description: "Deploy multiple agents for tasks like distributed environmental mapping or data collection." },
    { name: "Interactive Kiosks & Robotics", description: "Power interactive AI on various hardware platforms, enabling voice and vision capabilities." },
    { name: "Educational & Research Tool", description: "Facilitate experiments with distributed AI, agent communication, and remote sensing." },
    { name: "Content Creation Aid", description: "Automate lecture recording, note-taking, or generate content based on real-time agent input."}
];

const apiHighlights = [
  {
    icon: <Share2 className="w-7 h-7 mr-3 text-teal-400"/>,
    title: "WebSocket API",
    description: "Real-time, bidirectional communication. Clients register, send responses, and stream status updates. Server issues commands.",
    points: ["Client Registration (`client_name`, `platform`, `capabilities`)", "Server-to-Client Commands (`action`, `params`)", "Client-to-Server Responses (`command_id`, `status`, `data`)"]
  },
  {
    icon: <DatabaseZap className="w-7 h-7 mr-3 text-lime-400"/>,
    title: "HTTP REST API",
    description: "Manage clients, send commands, and control streams programmatically. Auto-generated OpenAPI docs available.",
    points: ["`GET /clients` - List clients", "`POST /clients/{id}/commands/{action}` - Send command", "`GET /streams/{id}/status` - Stream status"]
  },
  {
    icon: <Code className="w-7 h-7 mr-3 text-fuchsia-400"/>,
    title: "Modular Message System",
    description: "Leverages Pydantic models for clear, validated message structures between server and clients.",
    points: ["Defined models for `Command`, `CommandResponse`, `StreamStatusUpdate`, etc.", "Extensible for custom message types."]
  }
];

import Navbar from "@/components/Navbar";
import HeroSection from "@/components/HeroSection";
import FeaturesSection from "@/components/FeaturesSection";
import ArchitectureSection from "@/components/ArchitectureSection";
import UseCasesSection from "@/components/UseCasesSection";
import ApiOverviewSection from "@/components/ApiOverviewSection";
import GettingStartedSection from "@/components/GettingStartedSection";
import Footer from "@/components/Footer";


export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-slate-50 flex flex-col">
      <Navbar />
      <main className="flex-grow">
        <HeroSection />
        <FeaturesSection features={features} title={""} subtitle={""} />
        <ArchitectureSection />
        <UseCasesSection useCases={useCases} />
        <ApiOverviewSection apiHighlights={apiHighlights} />
        <GettingStartedSection />
      </main>
      <Footer />
    </div>
  );
}

import { Layers, Smartphone, Server, Zap, Database, ShieldCheck } from "lucide-react"; 

export default function ArchitectureSection() {
  return (
    <section id="architecture" className="py-16 md:py-24 bg-slate-800/40 text-slate-100">
      <div className="container mx-auto px-6 md:px-10">
        <div className="text-center mb-14">
          <h2 className="text-4xl md:text-5xl font-bold mb-5">Flexible Architecture</h2>
          <p className="text-lg text-slate-400 max-w-3xl mx-auto">
            Orka is designed with a versatile architecture to support various deployment scenarios, from complex multi-agent systems to simple standalone applications.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 lg:gap-10 items-stretch">
          {/* Client-Server Mode Card */}
          <div className="bg-slate-700/50 p-8 rounded-xl shadow-xl hover:shadow-teal-500/30 transition-all duration-300 ease-in-out transform hover:-translate-y-1 flex flex-col">
            <div className="flex items-center mb-5">
              <div className="p-3 bg-teal-600/20 rounded-lg mr-4 flex-shrink-0">
                <Layers className="w-7 h-7 text-teal-400" />
              </div>
              <h3 className="text-2xl font-semibold text-slate-50">Client-Server Mode</h3>
            </div>
            <p className="text-slate-300 text-sm mb-6 flex-grow leading-relaxed">
              A central FastAPI server orchestrates multiple Python clients connected via WebSockets. This mode enables comprehensive remote management, real-time monitoring, and command execution across all connected agents through a unified web dashboard.
            </p>
            <ul className="space-y-2.5 text-sm">
              <li className="flex items-start text-slate-300">
                <Server className="w-4 h-4 mr-2.5 mt-0.5 text-teal-400 flex-shrink-0" />
                Centralized control & monitoring via FastAPI server
              </li>
              <li className="flex items-start text-slate-300">
                <Zap className="w-4 h-4 mr-2.5 mt-0.5 text-teal-400 flex-shrink-0" />
                Real-time WebSocket communication for commands & data
              </li>
              <li className="flex items-start text-slate-300">
                <Database className="w-4 h-4 mr-2.5 mt-0.5 text-teal-400 flex-shrink-0" />
                Scalable for managing multiple, distributed agents
              </li>
            </ul>
          </div>

          {/* Standalone Mode Card */}
          <div className="bg-slate-700/50 p-8 rounded-xl shadow-xl hover:shadow-sky-500/30 transition-all duration-300 ease-in-out transform hover:-translate-y-1 flex flex-col">
            <div className="flex items-center mb-5">
              <div className="p-3 bg-sky-600/20 rounded-lg mr-4 flex-shrink-0">
                <Smartphone className="w-7 h-7 text-sky-400" />
              </div>
              <h3 className="text-2xl font-semibold text-slate-50">Standalone Mode</h3>
            </div>
            <p className="text-slate-300 text-sm mb-6 flex-grow leading-relaxed">
              Run Orka agents independently on a single device without requiring a central server. This mode is perfect for personal AI assistants, embedded applications, or scenarios where offline operation and rapid prototyping are key.
            </p>
            <ul className="space-y-2.5 text-sm">
              <li className="flex items-start text-slate-300">
                <Smartphone className="w-4 h-4 mr-2.5 mt-0.5 text-sky-400 flex-shrink-0" />
                On-device operation, no server connection needed
              </li>
              <li className="flex items-start text-slate-300">
                <Zap className="w-4 h-4 mr-2.5 mt-0.5 text-sky-400 flex-shrink-0" />
                Ideal for embedded systems & personal AI assistants
              </li>
              <li className="flex items-start text-slate-300">
                <ShieldCheck className="w-4 h-4 mr-2.5 mt-0.5 text-sky-400 flex-shrink-0" />
                Simplified setup for single agent deployment
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}

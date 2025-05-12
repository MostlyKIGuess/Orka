import Link from "next/link";
import { ArrowRight, GitFork, KeyRound, PackageCheck, Play } from "lucide-react";
import {JSX} from "react";

interface CommandDetail {
  label: string;
  code: string;
}
interface Step {
  icon: JSX.Element;
  title: string;
  description?: string;
  command?: string;
  commands?: CommandDetail[];
}

export default function GettingStartedSection() {
  const steps: Step[] = [
    {
      icon: <GitFork className="w-6 h-6 text-indigo-400" />,
      title: "Clone the Repository",
      command: "git clone https://github.com/mostlyKIGuess/Orka.git\ncd Orka",
    },
    {
      icon: <KeyRound className="w-6 h-6 text-indigo-400" />,
      title: "Set Up API Key",
      description: "Create a .env file in the project root and add your GEMINI_API_KEY.",
      command: "GEMINI_API_KEY=YOUR_API_KEY_HERE",
    },
    {
      icon: <PackageCheck className="w-6 h-6 text-indigo-400" />,
      title: "Install Dependencies",
      command: "pip install -r requirements.txt",
      description: "Ensure you also follow any platform-specific setup instructions in the README for Android, Raspberry Pi, etc.",
    },
    {
      icon: <Play className="w-6 h-6 text-indigo-400" />,
      title: "Run Orka",
      description: "Start the server for client-server mode, or run a client in standalone or both modes.",
      commands: [
        { label: "Server:", code: "python server/main_server.py" },
        { label: "Client (to server):", code: "python client/main_client.py --server ws://<server_ip>:8000/<client_name>" },
        { label: "Standalone Client:", code: "python client/main_client.py --standalone" },
        { label: "Both (local server & client):", code: "python client/main_client.py --both --server ws://localhost:8000/<client_name>" },
      ],
    },
  ];

  return (
    <section id="getting-started" className="py-16 md:py-24 bg-slate-900 text-slate-100">
      <div className="container mx-auto px-6 md:px-10">
        <div className="text-center mb-14">
          <h2 className="text-4xl md:text-5xl font-bold mb-5">Get Started with Orka</h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            Ready to build and control your own AI agents? It&apos;s easy to get Orka up and running.
          </p>
        </div>

        <div className="max-w-4xl mx-auto bg-slate-800/70 p-6 md:p-10 rounded-xl shadow-2xl">
          <ol className="space-y-8">
            {steps.map((step, index) => (
              <li key={step.title} className="flex items-start space-x-4 sm:space-x-5">
                <div className="flex-shrink-0 w-10 h-10 sm:w-12 sm:h-12 bg-indigo-500/20 text-indigo-400 rounded-full flex items-center justify-center text-lg sm:text-xl font-bold">
                  {index + 1}
                </div>
                <div className="flex-grow pt-0.5 sm:pt-1">
                  <div className="flex items-center mb-2">
                    <span className="flex-shrink-0">{step.icon}</span>
                    <h4 className="font-semibold text-lg sm:text-xl ml-2 text-slate-50">{step.title}</h4>
                  </div>
                  {step.description && (
                    <p className="text-slate-300 text-sm mb-3 leading-relaxed">{step.description}</p>
                  )}
                  {step.command && !step.commands && (
                    <pre className="block bg-slate-700/80 text-slate-200 p-3.5 rounded-md text-sm overflow-x-auto font-mono whitespace-pre-wrap">
                      <code>{step.command}</code>
                    </pre>
                  )}
                  {step.commands && (
                    <div className="space-y-3">
                      {step.commands.map(cmd => (
                        <div key={cmd.label}>
                           <p className="text-slate-300 text-sm mb-1 font-medium">{cmd.label}</p>
                           <pre className="block bg-slate-700/80 text-slate-200 p-3.5 rounded-md text-sm overflow-x-auto font-mono whitespace-pre-wrap">
                             <code>{cmd.code}</code>
                           </pre>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ol>
          <div className="mt-12 text-center">
            <Link
              href="/docs#getting-started" 
              className="text-indigo-400 hover:text-indigo-300 font-semibold inline-flex items-center group text-lg"
            >
              View Full Documentation <ArrowRight className="w-5 h-5 ml-2 transition-transform duration-200 group-hover:translate-x-1" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

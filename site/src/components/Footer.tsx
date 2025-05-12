import Link from "next/link";
import { Bot, Github } from "lucide-react"; 

export default function Footer() {
  return (
    <footer className="py-10 md:py-12 border-t border-slate-700/50 bg-slate-900 text-slate-400">
      <div className="container mx-auto px-6 md:px-10">
        <div className="grid md:grid-cols-3 gap-8 items-center">
          <div className="flex items-center justify-center md:justify-start">
            <Link href="/" className="text-xl font-bold flex items-center text-slate-200 hover:text-blue-400 transition-colors">
              <Bot className="w-7 h-7 mr-2 text-blue-400" />
              Orka
            </Link>
          </div>

          <div className="text-center text-sm">
            <p>&copy; {new Date().getFullYear()} Orka Project. All rights reserved.</p>
            <p className="text-xs mt-2 text-slate-500">
              Orka: Orchestrator Kernel for Agents.
            </p>
          </div>

          <div className="flex justify-center md:justify-end space-x-4">
            <a 
              href="https://github.com/mostlyKIGuess/Orka" 
              target="_blank" 
              rel="noopener noreferrer" 
              aria-label="GitHub Repository"
              className="text-slate-400 hover:text-blue-400 transition-colors"
            >
              <Github className="w-6 h-6" />
            </a>
            {/* other socials*/}
          </div>
        </div>
      </div>
    </footer>
  );
}


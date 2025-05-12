import Link from "next/link";
import { Bot } from "lucide-react";

export default function Navbar() {
  return (
    <header className="py-4 px-6 md:px-10 sticky top-0 z-50 bg-slate-900/70 backdrop-blur-lg border-b border-slate-700/50">
      <nav className="container mx-auto flex justify-between items-center">
        <Link href="/" className="text-2xl font-bold flex items-center hover:text-blue-400 transition-colors">
          <Bot className="w-8 h-8 mr-2 text-blue-400" />
          Orka
        </Link>
        <div className="space-x-5 md:space-x-6 flex items-center">
          <Link href="/#features" className="text-slate-300 hover:text-blue-400 transition-colors">Features</Link>
          <Link href="/#use-cases" className="text-slate-300 hover:text-blue-400 transition-colors">Use Cases</Link>
          <Link href="/#api-overview" className="text-slate-300 hover:text-blue-400 transition-colors">API</Link>
          <a
            href="https://github.com/mostlyKIGuess/Orka"
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-300 hover:text-blue-400 transition-colors"
          >
            GitHub
          </a>
          <Link
            href="/docs" 
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg transition-colors text-sm"
          >
            Full API Docs
          </Link>
        </div>
      </nav>
    </header>
  );
}

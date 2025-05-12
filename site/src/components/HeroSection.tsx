import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function HeroSection() {
  return (
    <section className="container mx-auto px-6 md:px-10 py-24 md:py-36 text-center">
      <h1 className="text-5xl sm:text-6xl md:text-7xl font-extrabold mb-8 leading-tight">
        Orchestrate Your AI Agents.
        <br />
        <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-teal-300">
          Anywhere, Anytime.
        </span>
      </h1>
      <p className="text-lg md:text-xl text-slate-300 mb-12 max-w-3xl mx-auto">
        Orka is a Python framework for building and controlling modular AI agents
        across diverse platforms. Unify your agent management with a powerful web UI and robust API.
      </p>
      <div className="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-6">
        <Link
          href="#getting-started"
          className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-semibold px-8 py-3.5 rounded-lg text-lg transition-all duration-300 ease-in-out inline-flex items-center shadow-lg hover:shadow-blue-500/50 transform hover:scale-105"
        >
          Get Started <ArrowRight className="w-5 h-5 ml-2.5" />
        </Link>
        <a
          href="https://github.com/mostlyKIGuess/Orka"
          target="_blank"
          rel="noopener noreferrer"
          className="bg-slate-700 hover:bg-slate-600 text-white font-semibold px-8 py-3.5 rounded-lg text-lg transition-colors duration-300 ease-in-out inline-flex items-center shadow-md hover:shadow-slate-500/40 transform hover:scale-105"
        >
          View on GitHub
        </a>
      </div>
    </section>
  );
}

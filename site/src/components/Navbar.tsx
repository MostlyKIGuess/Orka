"use client";
import Link from "next/link";
import { Bot, Menu, X, Github } from "lucide-react";
import { useState } from "react";
export default function Navbar() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const navLinks = [
    { href: "/#features", label: "Features" },
    { href: "/#use-cases", label: "Use Cases" },
    { href: "/#api-overview", label: "API" },
    { href: "https://github.com/mostlyKIGuess/Orka", label: "GitHub", target: "_blank" },
    { href: "/docs", label: "Full API Docs", isButton: true },
  ];

  return (
    <header className="py-4 px-6 md:px-10 sticky top-0 z-50 bg-slate-900/80 backdrop-blur-lg border-b border-slate-700/50">
      <nav className="container mx-auto flex justify-between items-center">
        <Link href="/" className="text-2xl font-bold flex items-center hover:text-blue-400 transition-colors">
          <Bot className="w-8 h-8 mr-2 text-blue-400" />
          Orka
        </Link>

        <div className="hidden md:flex space-x-5 md:space-x-6 items-center">
          {navLinks.map((link) =>
            link.href.startsWith("http") || link.target === "_blank" ? (
              <a
                key={link.label}
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-300 hover:text-blue-400 transition-colors"
              >
                {link.label === "GitHub" ? <Github className="w-5 h-5 inline mr-1" /> : null}
                {link.label}
              </a>
            ) : link.isButton ? (
              <Link
                key={link.label}
                href={link.href}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg transition-colors text-sm"
              >
                {link.label}
              </Link>
            ) : (
              <Link key={link.label} href={link.href} className="text-slate-300 hover:text-blue-400 transition-colors">
                {link.label}
              </Link>
            )
          )}
        </div>

        <div className="md:hidden">
          <button
            onClick={toggleMobileMenu}
            aria-label="Toggle menu"
            className="text-slate-300 hover:text-blue-400 focus:outline-none"
          >
            {isMobileMenuOpen ? <X className="w-7 h-7" /> : <Menu className="w-7 h-7" />}
          </button>
        </div>
      </nav>

      {isMobileMenuOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 bg-slate-900/95 backdrop-blur-md shadow-lg z-40 border-t border-slate-700/50">
          <div className="container mx-auto px-6 py-4 flex flex-col space-y-3">
            {navLinks.map((link) =>
              link.href.startsWith("http") || link.target === "_blank" ? (
                <a
                  key={link.label}
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-200 hover:text-blue-400 py-2 text-center text-lg"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  {link.label}
                </a>
              ) : link.isButton ? (
                <Link
                  key={link.label}
                  href={link.href}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-3 rounded-lg transition-colors text-center text-lg"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  {link.label}
                </Link>
              ) : (
                <Link
                  key={link.label}
                  href={link.href}
                  className="text-slate-200 hover:text-blue-400 py-2 text-center text-lg"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  {link.label}
                </Link>
              )
            )}
          </div>
        </div>
      )}
    </header>
  );
}

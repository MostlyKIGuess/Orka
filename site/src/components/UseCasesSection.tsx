import { CheckSquare } from "lucide-react"; 
import {JSX } from "react"; 

interface UseCaseItem {
  name: string;
  description: string;
  icon?: JSX.Element; // Optional icon for each use case
}

interface UseCasesSectionProps {
  useCases: UseCaseItem[];
}

export default function UseCasesSection({ useCases }: UseCasesSectionProps) {
  return (
    <section id="use-cases" className="py-16 md:py-24 bg-slate-800/30 text-slate-100">
      <div className="container mx-auto px-6 md:px-10">
        <div className="text-center mb-14">
          <h2 className="text-4xl md:text-5xl font-bold mb-5">Versatile Use Cases</h2>
          <p className="text-lg text-slate-400 max-w-3xl mx-auto">
            From personal assistants to complex multi-agent systems, Orka adapts to a wide range of applications.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {useCases.map((uc) => (
            <div 
              key={uc.name} 
              className="bg-slate-700/60 p-7 rounded-xl shadow-lg hover:shadow-teal-500/30 transition-all duration-300 ease-in-out transform hover:-translate-y-1"
            >
              <div className="flex items-start mb-3">
                {uc.icon ? <span className="mr-3 mt-1 text-teal-400 flex-shrink-0">{uc.icon}</span> : <CheckSquare className="w-6 h-6 mr-3 text-teal-400 flex-shrink-0 mt-1" />}
                <h3 className="text-xl font-semibold text-slate-50">{uc.name}</h3>
              </div>
              <p className="text-slate-300 text-sm leading-relaxed">{uc.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

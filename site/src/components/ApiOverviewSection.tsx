import Link from "next/link";
import { ArrowRight, CheckCircle } from "lucide-react";
import { JSX } from "react";

interface ApiHighlight {
  icon: JSX.Element;
  title: string;
  description: string;
  points: string[];
}

interface ApiOverviewSectionProps {
  apiHighlights: ApiHighlight[];
}

export default function ApiOverviewSection({ apiHighlights }: ApiOverviewSectionProps) {
  return (
    <section id="api-overview" className="py-16 md:py-24 bg-slate-800/60">
      <div className="container mx-auto px-6 md:px-10">
        <div className="text-center mb-14">
          <h2 className="text-4xl md:text-5xl font-bold mb-5">Powerful & Flexible API</h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            Integrate and extend Orka агентов with a comprehensive API suite, designed for robust control and real-time interaction.
          </p>
        </div>

        <div className="grid md:grid-cols-1 lg:grid-cols-3 gap-8">
          {apiHighlights.map((highlight) => (
            <div 
              key={highlight.title} 
              className="bg-slate-700/50 p-7 rounded-xl shadow-xl hover:shadow-blue-500/30 transition-all duration-300 ease-in-out transform hover:-translate-y-1 flex flex-col"
            >
              <div className="flex items-center mb-5">
                {highlight.icon}
                <h3 className="text-2xl font-semibold text-slate-100">{highlight.title}</h3>
              </div>
              <p className="text-slate-300 text-sm mb-5 flex-grow">{highlight.description}</p>
              <ul className="space-y-2.5 mb-6">
                {highlight.points.map((point, index) => (
                  <li key={index} className="flex items-start text-sm text-slate-300">
                    <CheckCircle className="w-4 h-4 mr-2.5 mt-0.5 text-green-400 flex-shrink-0" />
                    {point}
                  </li>
                ))}
              </ul>
              <Link 
                href="/docs" // Link to your full API docs
                className="mt-auto text-blue-400 hover:text-blue-300 text-sm font-medium inline-flex items-center group"
              >
                Explore Full API Docs <ArrowRight className="w-4 h-4 ml-1.5 transition-transform duration-200 group-hover:translate-x-1" />
              </Link>
            </div>
          ))}
        </div>
         <div className="text-center mt-16">
            <p className="text-slate-400">
                For detailed endpoint specifications, message formats, and examples, please visit our comprehensive API documentation.
            </p>
        </div>
      </div>
    </section>
  );
}

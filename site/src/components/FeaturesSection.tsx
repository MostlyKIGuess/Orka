import Link from "next/link";
import { ArrowRight} from "lucide-react"; 
import { JSX } from "react";

interface FeatureItem {
  icon: JSX.Element;
  title: string;
  description: string;
  link?: string;
  linkText?: string;
}

interface FeaturesSectionProps {
  title: string;
  subtitle: string;
  features: FeatureItem[];
  ctaLink?: string;
  ctaText?: string;
}

export default function FeaturesSection({ title, subtitle, features, ctaLink, ctaText }: FeaturesSectionProps) {
  return (
    <section id="features" className="py-16 md:py-24 bg-slate-900 text-slate-100">
      <div className="container mx-auto px-6 md:px-10">
        <div className="text-center mb-14">
          <h2 className="text-4xl md:text-5xl font-bold mb-5">{title}</h2>
          <p className="text-lg text-slate-400 max-w-3xl mx-auto">
            {subtitle}
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => (
            <div 
              key={feature.title} 
              className="bg-slate-800/70 p-7 rounded-xl shadow-lg hover:shadow-purple-500/30 transition-all duration-300 ease-in-out transform hover:-translate-y-1 flex flex-col"
            >
              <div className="flex items-center mb-5">
                <div className="p-3 bg-purple-600/20 rounded-lg mr-4">
                  {feature.icon}
                </div>
                <h3 className="text-2xl font-semibold text-slate-50">{feature.title}</h3>
              </div>
              <p className="text-slate-300 text-sm mb-5 flex-grow">{feature.description}</p>
              {feature.link && feature.linkText && (
                <Link 
                  href={feature.link}
                  className="mt-auto text-purple-400 hover:text-purple-300 text-sm font-medium inline-flex items-center group"
                >
                  {feature.linkText} <ArrowRight className="w-4 h-4 ml-1.5 transition-transform duration-200 group-hover:translate-x-1" />
                </Link>
              )}
            </div>
          ))}
        </div>

        {ctaLink && ctaText && (
          <div className="text-center mt-16">
            <Link
              href={ctaLink}
              className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-8 rounded-lg text-lg transition-colors duration-300"
            >
              {ctaText}
            </Link>
          </div>
        )}
      </div>
    </section>
  );
}

/*
const exampleFeatures: FeatureItem[] = [
  {
    icon: <Zap className="w-6 h-6 text-purple-400" />,
    title: "Real-time Control",
    description: "Instantly send commands and receive feedback from connected agents, enabling dynamic interaction and control.",
    link: "/docs/real-time",
    linkText: "Learn More"
  },
  {
    icon: <ShieldCheck className="w-6 h-6 text-purple-400" />,
    title: "Secure Communication",
    description: "Ensures all data exchanged between the server and agents is encrypted and secure, protecting sensitive information.",
  },
  {
    icon: <Code className="w-6 h-6 text-purple-400" />,
    title: "Extensible API",
    description: "Leverage a comprehensive API to integrate Orka with your existing systems or build custom functionalities.",
    link: "/docs/api",
    linkText: "Explore API"
  },
  {
    icon: <SlidersHorizontal className="w-6 h-6 text-purple-400" />,
    title: "Configurable Agents",
    description: "Customize agent capabilities and behaviors through flexible configuration options to suit diverse operational needs.",
  },
  {
    icon: <Share2 className="w-6 h-6 text-purple-400" />,
    title: "Multi-Client Management",
    description: "Efficiently manage and monitor multiple connected agents from a centralized dashboard.",
  },
  {
    icon: <Brain className="w-6 h-6 text-purple-400" />,
    title: "SLAM Integration",
    description: "Supports Simultaneous Localization and Mapping (SLAM) for agents equipped with visual sensors, enabling spatial awareness.",
    link: "/docs/slam",
    linkText: "SLAM Details"
  }
];

<FeaturesSection 
  title="Core Capabilities"
  subtitle="Orka provides a robust set of features to manage and interact with your remote agents effectively and securely."
  features={exampleFeatures}
  ctaText="Get Started with Orka"
  ctaLink="/docs/getting-started"
/>
*/

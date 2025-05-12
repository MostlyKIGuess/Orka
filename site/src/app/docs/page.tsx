import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import DocsPageContent from "@/components/DocsPageContent";

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-slate-50 flex flex-col">
      <Navbar />
      <main className="flex-grow">
        <DocsPageContent />
      </main>
      <Footer />
    </div>
  );
}

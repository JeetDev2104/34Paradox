
import React from "react";
import Header from "@/components/Header";
import Dashboard from "@/components/Dashboard";

const Index = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto">
        <Dashboard />
      </main>
      
      <footer className="py-6 border-t mt-12 text-center text-sm text-gray-500">
        <div className="container mx-auto">
          <p>© 2025 NewsSense - Financial Market Analysis</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;

import React from "react";

const Header: React.FC = () => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <span className="text-blue-600 font-bold text-xl">NewsSense</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;

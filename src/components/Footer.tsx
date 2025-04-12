import React from "react";

const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-gray-200 py-4 mt-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-500">
            © 2023 NewsSense. All rights reserved.
          </div>
          <div className="flex space-x-6">
            <a href="#" className="text-sm text-gray-500 hover:text-blue-600">
              Terms
            </a>
            <a href="#" className="text-sm text-gray-500 hover:text-blue-600">
              Privacy
            </a>
            <a href="#" className="text-sm text-gray-500 hover:text-blue-600">
              Help
            </a>
            <a href="#" className="text-sm text-gray-500 hover:text-blue-600">
              Contact
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

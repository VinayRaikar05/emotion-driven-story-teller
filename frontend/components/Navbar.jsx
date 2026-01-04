import React, { useState } from "react";

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);

  const navLinks = ["About", "Pricing", "Technology", "Contact"];

  return (
    <nav className="fixed w-full z-50 top-0 start-0 border-b border-glass-border bg-glass-100 backdrop-blur-lg">
      <div className="max-w-screen-xl flex flex-wrap items-center justify-between mx-auto p-4">
        {/* Logo */}
        <a href="#" className="flex items-center space-x-3 rtl:space-x-reverse group">
          <div className="relative w-8 h-8 bg-gradient-to-br from-primary-400 to-secondary-500 rounded-lg flex items-center justify-center shadow-lg group-hover:shadow-primary-500/50 transition-all duration-300">
            <span className="text-white font-bold text-xl">M</span>
          </div>
          <span className="self-center text-2xl font-display font-semibold whitespace-nowrap bg-clip-text text-transparent bg-gradient-to-r from-white to-primary-200">
            Multivox
          </span>
        </a>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          type="button"
          className="inline-flex items-center p-2 w-10 h-10 justify-center text-sm text-gray-300 rounded-lg md:hidden hover:bg-glass-200 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors"
          aria-expanded={isOpen}
        >
          <span className="sr-only">Open main menu</span>
          <svg className="w-5 h-5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 17 14">
            <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M1 1h15M1 7h15M1 13h15" />
          </svg>
        </button>

        {/* Menu Items */}
        <div className={`${isOpen ? 'block' : 'hidden'} w-full md:block md:w-auto`} id="navbar-default">
          <ul className="font-medium flex flex-col p-4 md:p-0 mt-4 border border-glass-border rounded-lg bg-glass-200 md:flex-row md:space-x-8 rtl:space-x-reverse md:mt-0 md:border-0 md:bg-transparent">
            {navLinks.map((link) => (
              <li key={link}>
                <a href="#" className="block py-2 px-3 text-gray-300 rounded hover:text-white hover:bg-glass-200 md:hover:bg-transparent md:border-0 md:hover:text-primary-300 md:p-0 transition-all duration-200 relative group">
                  {link}
                  <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary-400 transition-all duration-300 group-hover:w-full"></span>
                </a>
              </li>
            ))}
            <li>
              <a href="#" className="block py-2 px-3 text-white bg-gradient-to-r from-primary-600 to-secondary-600 rounded md:bg-transparent md:text-transparent md:bg-clip-text md:font-bold md:p-0">
                Sign In
              </a>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;

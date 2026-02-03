import React from 'react';

interface IconProps {
  name: string;
  className?: string;
  size?: number;
}

const Icon: React.FC<IconProps> = ({ name, className = '', size = 24 }) => {
  return (
    <span 
      className={`material-symbols-outlined select-none ${className}`} 
      style={{ fontSize: `${size}px` }}
    >
      {name}
    </span>
  );
};

export default Icon;
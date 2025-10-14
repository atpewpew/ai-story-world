import React from 'react';

const LoadingSpinner = ({ size = 16, className = '' }) => {
  return (
    <div className={`spinner ${className}`} style={{ width: size, height: size }}>
      <div className="spinner-inner"></div>
    </div>
  );
};

export default LoadingSpinner;


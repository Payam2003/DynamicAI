import React, { useState } from "react";  
import "../css/SliderBlock.css";


function SliderBlock({ component, stepId, onSubmitAction, disabled }) {
  const min = component.min_value ?? 0;
  const max = component.max_value ?? 10;
  const [value, setValue] = useState(Math.floor((min + max) / 2));

  const handleSubmitSlider = () => {
    onSubmitAction({
      stepId,
      actionType: "slider_submit",
      payload: {
        value,
      },
    });
  };

  return (
    <div className="dynamic-ui-block">
      {component.label && (
        <p className="dynamic-ui-label">{component.label}</p>
      )}

      <div className="slider-block">
        <input
          type="range"
          min={min}
          max={max}
          value={value}
          onChange={(e) => setValue(Number(e.target.value))}
          disabled={disabled}
        />
        <span className="slider-value">{value}</span>
      </div>

      <button
        type="button"
        className="option-btn slider-submit-btn"
        onClick={handleSubmitSlider}
        disabled={disabled}
      >
        Conferma valore
      </button>
    </div>
  );
}

export default SliderBlock;
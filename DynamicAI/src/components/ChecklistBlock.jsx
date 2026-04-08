import React, { useState } from "react";
import "../css/ChecklistBlock.css";

function ChecklistBlock({ component, stepId, onSubmitAction, disabled }) {
  const [selected, setSelected] = useState([]);

  const toggleOption = (option) => {
    setSelected((prev) =>
      prev.includes(option)
        ? prev.filter((item) => item !== option)
        : [...prev, option]
    );
  };

  const handleSubmitChecklist = () => {
    if (!selected.length) return;

    onSubmitAction({
      stepId,
      actionType: "checklist_submit",
      payload: {
        selected_options: selected,
      },
    });
  };

  return (
    <div className="dynamic-ui-block">
      {component.label && (
        <p className="dynamic-ui-label">{component.label}</p>
      )}

      <div className="checklist-options">
        {component.options?.map((option) => (
          <label key={option} className="checklist-option">
            <input
              type="checkbox"
              checked={selected.includes(option)}
              onChange={() => toggleOption(option)}
              disabled={disabled}
            />
            <span>{option}</span>
          </label>
        ))}
      </div>

      <button
        type="button"
        className="option-btn checklist-submit-btn"
        onClick={handleSubmitChecklist}
        disabled={disabled || !selected.length}
      >
        Conferma selezione
      </button>
    </div>
  );
}

export default ChecklistBlock;
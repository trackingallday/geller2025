/**
 * Conditional Logic Engine for Dynamic Forms
 * Handles show/hide logic based on question responses
 */

class ConditionalLogicEngine {
    constructor() {
        this.rules = new Map();
        this.formData = new Map();
        this.observers = [];
        this.init();
    }

    init() {
        this.setupFormObservers();
        this.loadExistingRules();
    }

    /**
     * Add a conditional rule
     * @param {Object} rule - The conditional rule
     * @param {string} rule.id - Unique rule identifier
     * @param {string} rule.sourceField - Field that triggers the condition
     * @param {string} rule.operator - Comparison operator (equals, not_equals, contains, etc.)
     * @param {string|Array} rule.value - Value(s) to compare against
     * @param {string|Array} rule.targetFields - Field(s) to show/hide
     * @param {string} rule.action - Action to take (show, hide, require, unrequire)
     */
    addRule(rule) {
        if (!rule.id || !rule.sourceField || !rule.operator || !rule.targetFields) {
            console.error('Invalid rule: missing required properties', rule);
            return false;
        }

        this.rules.set(rule.id, {
            ...rule,
            targetFields: Array.isArray(rule.targetFields) ? rule.targetFields : [rule.targetFields],
            value: rule.value
        });

        this.evaluateRule(rule.id);
        return true;
    }

    /**
     * Remove a conditional rule
     * @param {string} ruleId - Rule identifier to remove
     */
    removeRule(ruleId) {
        const rule = this.rules.get(ruleId);
        if (rule) {
            // Reset target fields to visible state
            rule.targetFields.forEach(fieldId => {
                this.setFieldVisibility(fieldId, true);
                this.setFieldRequired(fieldId, false);
            });
            this.rules.delete(ruleId);
        }
    }

    /**
     * Update form data and trigger rule evaluation
     * @param {string} fieldId - Field identifier
     * @param {any} value - Field value
     */
    updateFormData(fieldId, value) {
        const oldValue = this.formData.get(fieldId);
        this.formData.set(fieldId, value);

        // Only re-evaluate if value actually changed
        if (oldValue !== value) {
            this.evaluateRulesForField(fieldId);
        }
    }

    /**
     * Evaluate all rules that depend on a specific field
     * @param {string} fieldId - Field that changed
     */
    evaluateRulesForField(fieldId) {
        this.rules.forEach((rule, ruleId) => {
            if (rule.sourceField === fieldId) {
                this.evaluateRule(ruleId);
            }
        });
    }

    /**
     * Evaluate a specific rule
     * @param {string} ruleId - Rule to evaluate
     */
    evaluateRule(ruleId) {
        const rule = this.rules.get(ruleId);
        if (!rule) return;

        const sourceValue = this.formData.get(rule.sourceField);
        const conditionMet = this.evaluateCondition(sourceValue, rule.operator, rule.value);

        rule.targetFields.forEach(fieldId => {
            this.applyRuleAction(fieldId, rule.action, conditionMet);
        });

        // Notify observers
        this.notifyObservers(ruleId, rule, conditionMet);
    }

    /**
     * Evaluate a condition
     * @param {any} sourceValue - Current field value
     * @param {string} operator - Comparison operator
     * @param {any} targetValue - Value to compare against
     * @returns {boolean} - Whether condition is met
     */
    evaluateCondition(sourceValue, operator, targetValue) {
        // Handle null/undefined values
        if (sourceValue == null) sourceValue = '';
        if (targetValue == null) targetValue = '';

        // Convert to strings for most comparisons
        const sourceStr = String(sourceValue).toLowerCase().trim();
        const targetStr = String(targetValue).toLowerCase().trim();

        switch (operator) {
            case 'equals':
                return sourceStr === targetStr;
            case 'not_equals':
                return sourceStr !== targetStr;
            case 'contains':
                return sourceStr.includes(targetStr);
            case 'not_contains':
                return !sourceStr.includes(targetStr);
            case 'starts_with':
                return sourceStr.startsWith(targetStr);
            case 'ends_with':
                return sourceStr.endsWith(targetStr);
            case 'is_empty':
                return sourceStr === '';
            case 'is_not_empty':
                return sourceStr !== '';
            case 'greater_than':
                return parseFloat(sourceValue) > parseFloat(targetValue);
            case 'less_than':
                return parseFloat(sourceValue) < parseFloat(targetValue);
            case 'in_list':
                const targetList = Array.isArray(targetValue) ? targetValue : [targetValue];
                return targetList.some(val => String(val).toLowerCase().trim() === sourceStr);
            case 'not_in_list':
                const excludeList = Array.isArray(targetValue) ? targetValue : [targetValue];
                return !excludeList.some(val => String(val).toLowerCase().trim() === sourceStr);
            default:
                console.warn('Unknown operator:', operator);
                return false;
        }
    }

    /**
     * Apply rule action to target field
     * @param {string} fieldId - Target field
     * @param {string} action - Action to apply
     * @param {boolean} conditionMet - Whether condition is satisfied
     */
    applyRuleAction(fieldId, action, conditionMet) {
        switch (action) {
            case 'show':
                this.setFieldVisibility(fieldId, conditionMet);
                break;
            case 'hide':
                this.setFieldVisibility(fieldId, !conditionMet);
                break;
            case 'require':
                this.setFieldRequired(fieldId, conditionMet);
                break;
            case 'unrequire':
                this.setFieldRequired(fieldId, !conditionMet);
                break;
            case 'enable':
                this.setFieldEnabled(fieldId, conditionMet);
                break;
            case 'disable':
                this.setFieldEnabled(fieldId, !conditionMet);
                break;
        }
    }

    /**
     * Set field visibility
     * @param {string} fieldId - Field identifier
     * @param {boolean} visible - Whether field should be visible
     */
    setFieldVisibility(fieldId, visible) {
        const fieldContainer = this.getFieldContainer(fieldId);
        if (fieldContainer) {
            fieldContainer.style.display = visible ? '' : 'none';
            
            // Clear field value if hiding
            if (!visible) {
                const field = this.getField(fieldId);
                if (field) {
                    this.clearFieldValue(field);
                }
            }
        }
    }

    /**
     * Set field required status
     * @param {string} fieldId - Field identifier
     * @param {boolean} required - Whether field should be required
     */
    setFieldRequired(fieldId, required) {
        const field = this.getField(fieldId);
        if (field) {
            field.required = required;
            
            // Update visual indicators
            const label = this.getFieldLabel(fieldId);
            if (label) {
                const requiredIndicator = label.querySelector('.required-indicator');
                if (required && !requiredIndicator) {
                    const span = document.createElement('span');
                    span.className = 'required-indicator text-danger';
                    span.textContent = ' *';
                    label.appendChild(span);
                } else if (!required && requiredIndicator) {
                    requiredIndicator.remove();
                }
            }
        }
    }

    /**
     * Set field enabled status
     * @param {string} fieldId - Field identifier
     * @param {boolean} enabled - Whether field should be enabled
     */
    setFieldEnabled(fieldId, enabled) {
        const field = this.getField(fieldId);
        if (field) {
            field.disabled = !enabled;
            field.classList.toggle('disabled', !enabled);
        }
    }

    /**
     * Get field element
     * @param {string} fieldId - Field identifier
     * @returns {Element|null} - Field element
     */
    getField(fieldId) {
        return document.getElementById(fieldId) || 
               document.querySelector(`[name="${fieldId}"]`) ||
               document.querySelector(`[data-field-id="${fieldId}"]`);
    }

    /**
     * Get field container element
     * @param {string} fieldId - Field identifier
     * @returns {Element|null} - Field container
     */
    getFieldContainer(fieldId) {
        const field = this.getField(fieldId);
        if (!field) return null;

        // Look for various container patterns
        return field.closest('.form-group') ||
               field.closest('.question-container') ||
               field.closest('.field-container') ||
               field.closest('.form-field') ||
               field.parentElement;
    }

    /**
     * Get field label element
     * @param {string} fieldId - Field identifier
     * @returns {Element|null} - Label element
     */
    getFieldLabel(fieldId) {
        const field = this.getField(fieldId);
        if (!field) return null;

        return document.querySelector(`label[for="${fieldId}"]`) ||
               field.closest('.form-group')?.querySelector('label') ||
               field.closest('.question-container')?.querySelector('label');
    }

    /**
     * Clear field value
     * @param {Element} field - Field element
     */
    clearFieldValue(field) {
        if (!field) return;

        const tagName = field.tagName.toLowerCase();
        const type = field.type;

        if (tagName === 'input') {
            if (type === 'checkbox' || type === 'radio') {
                field.checked = false;
            } else {
                field.value = '';
            }
        } else if (tagName === 'select') {
            field.selectedIndex = -1;
        } else if (tagName === 'textarea') {
            field.value = '';
        }

        // Update form data
        this.updateFormData(field.id || field.name, '');
    }

    /**
     * Setup form observers to watch for changes
     */
    setupFormObservers() {
        document.addEventListener('input', (e) => {
            if (e.target.matches('input, select, textarea')) {
                const fieldId = e.target.id || e.target.name || e.target.dataset.fieldId;
                if (fieldId) {
                    let value = e.target.value;
                    
                    // Handle different input types
                    if (e.target.type === 'checkbox') {
                        value = e.target.checked;
                    } else if (e.target.type === 'radio') {
                        value = e.target.checked ? e.target.value : null;
                    }
                    
                    this.updateFormData(fieldId, value);
                }
            }
        });

        document.addEventListener('change', (e) => {
            if (e.target.matches('select, input[type="radio"], input[type="checkbox"]')) {
                const fieldId = e.target.id || e.target.name || e.target.dataset.fieldId;
                if (fieldId) {
                    let value = e.target.value;
                    
                    if (e.target.type === 'checkbox') {
                        value = e.target.checked;
                    } else if (e.target.type === 'radio') {
                        value = e.target.checked ? e.target.value : this.getRadioGroupValue(e.target.name);
                    }
                    
                    this.updateFormData(fieldId, value);
                }
            }
        });
    }

    /**
     * Get selected radio button value for a group
     * @param {string} name - Radio group name
     * @returns {string|null} - Selected value
     */
    getRadioGroupValue(name) {
        const selected = document.querySelector(`input[type="radio"][name="${name}"]:checked`);
        return selected ? selected.value : null;
    }

    /**
     * Load existing form values
     */
    loadExistingRules() {
        // Load from form fields that have values
        const fields = document.querySelectorAll('input, select, textarea');
        fields.forEach(field => {
            const fieldId = field.id || field.name || field.dataset.fieldId;
            if (fieldId && field.value) {
                let value = field.value;
                if (field.type === 'checkbox') {
                    value = field.checked;
                } else if (field.type === 'radio' && !field.checked) {
                    return; // Skip unchecked radio buttons
                }
                this.updateFormData(fieldId, value);
            }
        });

        // Load rules from JSON data if available
        const rulesData = document.getElementById('conditional-rules-data');
        if (rulesData) {
            try {
                const rules = JSON.parse(rulesData.textContent);
                rules.forEach(rule => this.addRule(rule));
            } catch (e) {
                console.error('Error loading conditional rules:', e);
            }
        }
    }

    /**
     * Add observer for rule changes
     * @param {Function} callback - Callback function
     */
    addObserver(callback) {
        this.observers.push(callback);
    }

    /**
     * Remove observer
     * @param {Function} callback - Callback function to remove
     */
    removeObserver(callback) {
        const index = this.observers.indexOf(callback);
        if (index > -1) {
            this.observers.splice(index, 1);
        }
    }

    /**
     * Notify observers of rule evaluation
     * @param {string} ruleId - Rule that was evaluated
     * @param {Object} rule - Rule object
     * @param {boolean} conditionMet - Whether condition was met
     */
    notifyObservers(ruleId, rule, conditionMet) {
        this.observers.forEach(callback => {
            try {
                callback(ruleId, rule, conditionMet);
            } catch (e) {
                console.error('Error in conditional logic observer:', e);
            }
        });
    }

    /**
     * Get all current form data
     * @returns {Object} - Form data as object
     */
    getFormData() {
        const data = {};
        this.formData.forEach((value, key) => {
            data[key] = value;
        });
        return data;
    }

    /**
     * Validate all visible required fields
     * @returns {Array} - Array of validation errors
     */
    validateForm() {
        const errors = [];
        
        this.rules.forEach((rule, ruleId) => {
            rule.targetFields.forEach(fieldId => {
                const field = this.getField(fieldId);
                const container = this.getFieldContainer(fieldId);
                
                if (field && container && field.required) {
                    // Check if field is visible
                    const isVisible = container.style.display !== 'none';
                    
                    if (isVisible && !this.hasValue(field)) {
                        errors.push({
                            fieldId: fieldId,
                            message: `${this.getFieldLabel(fieldId)?.textContent || fieldId} is required`
                        });
                    }
                }
            });
        });
        
        return errors;
    }

    /**
     * Check if field has a value
     * @param {Element} field - Field element
     * @returns {boolean} - Whether field has value
     */
    hasValue(field) {
        if (!field) return false;
        
        const type = field.type;
        
        if (type === 'checkbox' || type === 'radio') {
            return field.checked;
        } else if (field.tagName.toLowerCase() === 'select') {
            return field.selectedIndex >= 0 && field.value !== '';
        } else {
            return field.value.trim() !== '';
        }
    }

    /**
     * Reset all rules and form state
     */
    reset() {
        this.rules.clear();
        this.formData.clear();
        
        // Reset all fields to visible and not required
        const fields = document.querySelectorAll('input, select, textarea');
        fields.forEach(field => {
            const fieldId = field.id || field.name || field.dataset.fieldId;
            if (fieldId) {
                this.setFieldVisibility(fieldId, true);
                this.setFieldRequired(fieldId, false);
                this.setFieldEnabled(fieldId, true);
            }
        });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConditionalLogicEngine;
} else {
    window.ConditionalLogicEngine = ConditionalLogicEngine;
}

// Auto-initialize if in browser
if (typeof window !== 'undefined') {
    window.conditionalLogic = new ConditionalLogicEngine();
}
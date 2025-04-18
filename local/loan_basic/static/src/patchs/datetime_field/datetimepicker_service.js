/** @odoo-module **/

import { markRaw, reactive } from "@odoo/owl";
import { areDatesEqual, formatDate, parseDate } from "@web/core/l10n/dates";
import { makePopover } from "@web/core/popover/popover_hook";
import { registry } from "@web/core/registry";
import { ensureArray, zip, zipWith } from "@web/core/utils/arrays";
import { deepCopy, shallowEqual } from "@web/core/utils/objects";
import { DateTimePicker } from "@web/core/datetime/datetime_picker";
import { DateTimePickerPopover } from "@web/core/datetime/datetime_picker_popover";
import { localization } from "@web/core/l10n/localization";
const { DateTime, Settings } = luxon;



/**
 * @typedef {luxon.DateTime} DateTime
 *
 * @typedef DateTimePickerHookParams
 * @property {string} [format]
 * @property {(value: DateTimePickerProps["value"]) => any} [onChange] callback
 *  invoked every time the hook updates the reactive value, either through the inputs
 *  or the picker.
 * @property {(value: DateTimePickerProps["value"]) => any} [onApply] callback
 *  invoked once the value is committed: this is either when all inputs received
 *  a "change" event or when the datetime picker popover has been closed.
 * @property {DateTimePickerProps} [pickerProps]
 * @property {string | ReturnType<typeof import("@odoo/owl").useRef>} [target]
 *
 * @typedef {import("./datetime_picker").DateTimePickerProps} DateTimePickerProps
 */

/**
 * @template {HTMLElement} T
 * @typedef {{ el: T | null }} OwlRef
 */

/** @type {typeof shallowEqual} */
const arePropsEqual = (obj1, obj2) =>
    shallowEqual(obj1, obj2, (a, b) => areDatesEqual(a, b) || shallowEqual(a, b));

const FOCUS_CLASSNAME = "text-primary";

const MIN_VALID_DATE = DateTime.fromObject({ year: 1000 });
const MAX_VALID_DATE = DateTime.fromObject({ year: 9999 }).endOf("year");

function isInRange(value, range) {
    if (!value || !range) {
        return false;
    }
    if (Array.isArray(value)) {
        const actualValues = value.filter(Boolean);
        if (actualValues.length < 2) {
            return isInRange(actualValues[0], range);
        }
        return (
            (value[0] <= range[0] && range[0] <= value[1]) ||
            (range[0] <= value[0] && value[0] <= range[1])
        );
    } else {
        return range[0] <= value && value <= range[1];
    }
}

function isValidDate(date) {
    return date && date.isValid && isInRange(date, [MIN_VALID_DATE, MAX_VALID_DATE]);
}

const formatters = {
    date: formatDate,
    datetime: function (value, timeZone, options = {}) {
        if (!value) {
            return "";
        }
        const format = options.format || localization.dateTimeFormat;
        return value.setZone(timeZone).toFormat(format);
    }
};

const parsers = {
    date: parseDate,
    datetime: function (value, timeZone, options = {}) {
        if (!value) {
            return false;
        }
    
        const fmt = options.format || localization.dateTimeFormat;
        const parseOpts = {
            setZone: true,
            zone: timeZone,
        };
        const switchToLatin = Settings.defaultNumberingSystem !== "latn" && /[0-9]/.test(value);
    
        // Force numbering system to latin if actual numbers are found in the value
        if (switchToLatin) {
            parseOpts.numberingSystem = "latn";
        }
    
        // Base case: try parsing with the given format and options
        let result = DateTime.fromFormat(value, fmt, parseOpts);
    
        // Try parsing as a smart date
        if (!isValidDate(result)) {
            result = parseSmartDateInput(value);
        }
    
        // Try parsing with partial date parts
        if (!isValidDate(result)) {
            const fmtWoZero = stripAlphaDupes(fmt);
            result = DateTime.fromFormat(value, fmtWoZero, parseOpts);
        }
    
        // Try parsing with custom shorthand date parts
        if (!isValidDate(result)) {
            // Luxon is not permissive regarding delimiting characters in the format.
            // So if the value to parse has less characters than the format, we would
            // try to parse without the delimiting characters.
            const digitList = value.split(nonDigitRegex).filter(Boolean);
            const fmtList = fmt.split(nonAlphaRegex).filter(Boolean);
            const valWoSeps = digitList.join("");
    
            // This is the weird part: we try to adapt the given format to comply with
            // the amount of digits in the given value. To do this we split the format
            // and the value on non-letter and non-digit characters respectively. This
            // should create the same amount of grouping parameters, and the format
            // groups are trimmed according to the length of their corresponding
            // digit group. The 'carry' variable allows for the length of a digit
            // group to overflow to the next format group. This is typically the case
            // when the given value doesn't have non-digit separators and generates
            // one big digit group instead.
            let carry = 0;
            const fmtWoSeps = fmtList
                .map((part, i) => {
                    const digitLength = (digitList[i] || "").length;
                    const actualPart = part.slice(0, digitLength + carry);
                    carry += digitLength - actualPart.length;
                    return actualPart;
                })
                .join("");
    
            result = DateTime.fromFormat(valWoSeps, fmtWoSeps, parseOpts);
        }
    
        // Try with defaul ISO or SQL formats
        if (!isValidDate(result)) {
            // Also try some fallback formats, but only if value counts more than
            // four digit characters as this could get misinterpreted as the time of
            // the actual date.
            const valueDigits = value.replace(nonDigitRegex, "");
            if (valueDigits.length > 4) {
                result = DateTime.fromISO(value, parseOpts); // ISO8601
                if (!isValidDate(result)) {
                    result = DateTime.fromSQL(value, parseOpts); // last try: SQL
                }
            }
        }
    
        // No working parsing methods: throw an error
        if (!isValidDate(result)) {
            throw new ConversionError(_t("'%s' is not a correct date or datetime", value));
        }
    
        // Revert to original numbering system
        if (switchToLatin) {
            result = result.reconfigure({
                numberingSystem: Settings.defaultNumberingSystem,
            });
        }
    
        return result.setZone(timeZone);
    },
};

export const datetimePickerService1 = {
    dependencies: ["popover"],
    start(env, { popover: popoverService }) {
        return {
            /**
             * @param {DateTimePickerHookParams} hookParams
             */
            create: (
                hookParams,
                getInputs = () => [hookParams.target, null],
                createPopover = (...args) => makePopover(popoverService, ...args)
            ) => {
                const popover = createPopover(DateTimePickerPopover, {
                    onClose: () => {
                        if (!allowOnClose) {
                            return;
                        }
                        updateValueFromInputs();
                        apply();
                        setFocusClass(null);
                        if (restoreTargetMargin) {
                            restoreTargetMargin();
                            restoreTargetMargin = null;
                        }
                    },
                });
                // Hook methods

                /**
                 * Wrapper method on the "onApply" callback to only call it when the
                 * value has changed, and set other internal variables accordingly.
                 */
                const apply = () => {
                    if (areDatesEqual(lastInitialProps?.value, deepCopy(pickerProps.value))) {
                        return;
                    }

                    lastInitialProps = null; // Next pickerProps are considered final
                    inputsChanged = ensureArray(pickerProps.value).map(() => false);

                    hookParams.onApply?.(pickerProps.value);
                };

                const computeBasePickerProps = () => {
                    const nextInitialProps = markValuesRaw(hookParams.pickerProps);
                    const propsCopy = deepCopy(nextInitialProps);

                    if (lastInitialProps && arePropsEqual(lastInitialProps, propsCopy)) {
                        return;
                    }

                    lastInitialProps = propsCopy;
                    inputsChanged = ensureArray(lastInitialProps.value).map(() => false);

                    for (const [key, value] of Object.entries(nextInitialProps)) {
                        if (pickerProps[key] !== value && !areDatesEqual(pickerProps[key], value)) {
                            pickerProps[key] = value;
                        }
                    }
                };

                /**
                 * Ensures the current focused input (indicated by `pickerProps.focusedDateIndex`)
                 * is actually focused.
                 */
                const focusActiveInput = () => {
                    const inputEl = getInput(pickerProps.focusedDateIndex);
                    if (!inputEl) {
                        shouldFocus = true;
                        return;
                    }

                    const { activeElement } = inputEl.ownerDocument;
                    if (activeElement !== inputEl) {
                        inputEl.focus();
                    }

                    setInputFocus(inputEl);
                };

                /**
                 * @param {number} valueIndex
                 * @returns {HTMLInputElement | null}
                 */
                const getInput = (valueIndex) => {
                    const el = getInputs()[valueIndex];
                    if (el && document.body.contains(el)) {
                        return el;
                    }
                    return null;
                };

                /**
                 * Returns the appropriate root element to attach the popover:
                 * - if the value is a range: the closest common parent of the two inputs
                 * - if not: the first input
                 */
                const getPopoverTarget = () => {
                    if (hookParams.target) {
                        return hookParams.target;
                    }
                    if (pickerProps.range) {
                        let parentElement = getInput(0).parentElement;
                        const inputEls = getInputs();
                        while (
                            parentElement &&
                            !inputEls.every((inputEl) => parentElement.contains(inputEl))
                        ) {
                            parentElement = parentElement.parentElement;
                        }
                        return parentElement || getInput(0);
                    } else {
                        return getInput(0);
                    }
                };

                /**
                 * @template {object} T
                 * @param {T} obj
                 */
                const markValuesRaw = (obj) => {
                    /** @type {T} */
                    const copy = {};
                    for (const [key, value] of Object.entries(obj)) {
                        if (value && typeof value === "object") {
                            copy[key] = markRaw(value);
                        } else {
                            copy[key] = value;
                        }
                    }
                    return copy;
                };

                /**
                 * Inputs "change" event handler. This will trigger an "onApply" callback if
                 * one of the following is true:
                 * - there is only one input;
                 * - the popover is closed;
                 * - the other input has also changed.
                 *
                 * @param {Event} ev
                 */
                const onInputChange = (ev) => {
                    updateValueFromInputs();
                    inputsChanged[ev.target === getInput(1) ? 1 : 0] = true;
                    if (!popover.isOpen || inputsChanged.every(Boolean)) {
                        saveAndClose();
                    }
                };

                /**
                 * @param {PointerEvent} ev
                 */
                const onInputClick = ({ target }) => {
                    openPicker(target === getInput(1) ? 1 : 0);
                };

                /**
                 * @param {FocusEvent} ev
                 */
                const onInputFocus = ({ target }) => {
                    pickerProps.focusedDateIndex = target === getInput(1) ? 1 : 0;
                    setInputFocus(target);
                };

                /**
                 * @param {KeyboardEvent} ev
                 */
                const onInputKeydown = (ev) => {
                    switch (ev.key) {
                        case "Enter":
                        case "Escape": {
                            return saveAndClose();
                        }
                        case "Tab": {
                            if (
                                !getInput(0) ||
                                !getInput(1) ||
                                ev.target !== getInput(ev.shiftKey ? 1 : 0)
                            ) {
                                return saveAndClose();
                            }
                        }
                    }
                };

                /**
                 * @param {number} inputIndex Input from which to open the picker
                 */
                const openPicker = (inputIndex) => {
                    pickerProps.focusedDateIndex = inputIndex;

                    if (!popover.isOpen) {
                        const popoverTarget = getPopoverTarget();
                        if (env.isSmall) {
                            const { marginBottom } = popoverTarget.style;
                            // Adds enough space for the popover to be displayed below the target
                            // even on small screens.
                            popoverTarget.style.marginBottom = `100vh`;
                            popoverTarget.scrollIntoView(true);
                            restoreTargetMargin = async () => {
                                popoverTarget.style.marginBottom = marginBottom;
                            };
                        }
                        popover.open(popoverTarget, { pickerProps });
                    }

                    focusActiveInput();
                };

                /**
                 * @template {"format" | "parse"} T
                 * @param {T} operation
                 * @param {T extends "format" ? DateTime : string} value
                 * @returns {[T extends "format" ? string : DateTime, null] | [null, Error]}
                 */
                const safeConvert = (operation, value) => {
                    const timeZone = env.services.user.tz;
                    const { type } = pickerProps;
                    const convertFn = (operation === "format" ? formatters : parsers)[type];
                    try {
                        return [convertFn(value, timeZone, { format: hookParams.format }), null];
                    } catch (error) {
                        if (error?.name === "ConversionError") {
                            return [null, error];
                        } else {
                            throw error;
                        }
                    }
                };

                /**
                 * Wrapper method to ensure the "onApply" callback is called, either:
                 * - by closing the popover (if any);
                 * - or by directly calling "apply", without updating the values.
                 */
                const saveAndClose = () => {
                    if (popover.isOpen) {
                        // apply will be done in the "onClose" callback
                        popover.close();
                    } else {
                        apply();
                    }
                };

                /**
                 * Updates class names on given inputs according to the currently selected input.
                 *
                 * @param {HTMLInputElement | null} input
                 */
                const setFocusClass = (input) => {
                    for (const el of getInputs()) {
                        if (el) {
                            el.classList.toggle(FOCUS_CLASSNAME, popover.isOpen && el === input);
                        }
                    }
                };

                /**
                 * Applies class names to all inputs according to whether they are focused or not.
                 *
                 * @param {HTMLInputElement} inputEl
                 */
                const setInputFocus = (inputEl) => {
                    inputEl.selectionStart = 0;
                    inputEl.selectionEnd = inputEl.value.length;

                    setFocusClass(inputEl);

                    shouldFocus = false;
                };

                /**
                 * Synchronizes the given input with the given value.
                 *
                 * @param {HTMLInputElement} el
                 * @param {DateTime} value
                 */
                const updateInput = (el, value) => {
                    if (!el) {
                        return;
                    }
                    const [formattedValue] = safeConvert("format", value);
                    el.value = formattedValue || "";
                };

                /**
                 * @param {DateTimePickerProps["value"]} value
                 */
                const updateValue = (value) => {
                    const previousValue = pickerProps.value;
                    pickerProps.value = value;

                    if (areDatesEqual(previousValue, pickerProps.value)) {
                        return;
                    }

                    if (pickerProps.range) {
                        // When in range: compare each individual value
                        const [prevStart, prevEnd] = ensureArray(previousValue);
                        const [nextStart, nextEnd] = ensureArray(pickerProps.value);
                        if (
                            (pickerProps.focusedDateIndex === 0 &&
                                areDatesEqual(prevEnd, nextEnd)) ||
                            (pickerProps.focusedDateIndex === 1 &&
                                areDatesEqual(prevStart, nextStart))
                        ) {
                            pickerProps.focusedDateIndex =
                                pickerProps.focusedDateIndex === 1 ? 0 : 1;
                        }
                    }

                    hookParams.onChange?.(pickerProps.value);
                };

                const updateValueFromInputs = () => {
                    const values = zipWith(
                        getInputs(),
                        ensureArray(pickerProps.value),
                        (el, currentValue) => {
                            if (!el) {
                                return currentValue;
                            }
                            const [parsedValue, error] = safeConvert("parse", el.value);
                            if (error) {
                                updateInput(el, currentValue);
                                return currentValue;
                            } else {
                                return parsedValue;
                            }
                        }
                    );
                    updateValue(values.length === 2 ? values : values[0]);
                };

                // Hook variables

                /** @type {DateTimePickerProps} */
                const rawPickerProps = {
                    ...DateTimePicker.defaultProps,
                    rounding: 1,
                    onSelect: (value) => {
                        value &&= markRaw(value);
                        if (value) {
                            const timeZone = env.services.user.tz;
                            if(Array.isArray(value)){
                                value = value.map((v) => {
                                    if (!v) {

                                        return v;
                                    }
                                    return v.setZone(timeZone);
                                })
                            }else{
                                value = value.setZone(timeZone);
                            }
                        }
                        updateValue(value);
                        if (!pickerProps.range && pickerProps.type === "date") {
                            saveAndClose();
                        }
                    },
                    ...markValuesRaw(hookParams.pickerProps),
                };
                const pickerProps = reactive(rawPickerProps, () => {
                    // Resets the popover position when switching from single date to a range
                    // or vice-versa
                    const currentIsRange = pickerProps.range;
                    if (popover.isOpen && lastIsRange !== currentIsRange) {
                        allowOnClose = false;
                        popover.open(getPopoverTarget(), { pickerProps });
                        allowOnClose = true;
                    }
                    lastIsRange = currentIsRange;

                    // Update inputs
                    for (const [el, value] of zip(
                        getInputs(),
                        ensureArray(pickerProps.value),
                        true
                    )) {
                        if (el) {
                            updateInput(el, value);
                        }
                    }

                    shouldFocus = true;
                });

                /** Decides whether the popover 'onClose' callback can be called */
                let allowOnClose = true;
                /** @type {boolean[]} */
                let inputsChanged = [];
                /** @type {DateTimePickerProps | null} */
                let lastInitialProps = null;
                let lastIsRange = pickerProps.range;
                /** @type {(() => void) | null} */
                let restoreTargetMargin = null;
                let shouldFocus = false;

                /**
                 * @param {HTMLElement} el
                 * @param {string} type
                 * @param {(ev: Event) => any} listener
                 */
                const addListener = (el, type, listener) => {
                    el.addEventListener(type, listener);
                    return () => el.removeEventListener(type, listener);
                };

                return {
                    state: pickerProps,
                    open: openPicker,
                    computeBasePickerProps,
                    focusIfNeeded() {
                        if (popover.isOpen && shouldFocus) {
                            focusActiveInput();
                        }
                    },
                    enable() {
                        let editableInputs = 0;
                        const cleanups = [];
                        for (const [el, value] of zip(
                            getInputs(),
                            ensureArray(pickerProps.value),
                            true
                        )) {
                            updateInput(el, value);
                            if (el && !el.disabled && !el.readOnly) {
                                cleanups.push(addListener(el, "change", onInputChange));
                                cleanups.push(addListener(el, "click", onInputClick));
                                cleanups.push(addListener(el, "focus", onInputFocus));
                                cleanups.push(addListener(el, "keydown", onInputKeydown));
                                editableInputs++;
                            }
                        }
                        const calendarIconGroupEl = getInput(0)?.parentElement
                            .querySelector(".input-group-text .fa-calendar")?.parentElement;
                        if (calendarIconGroupEl) {
                            // TODO: Remove this line and the `pe-none` class
                            // from templates in master
                            calendarIconGroupEl.classList.remove("pe-none");
                            calendarIconGroupEl.classList.add("cursor-pointer");
                            cleanups.push(addListener(calendarIconGroupEl, "click", () => {
                                openPicker(0);
                            }));
                        }
                        if (!editableInputs && popover.isOpen) {
                            saveAndClose();
                        }
                        return () => cleanups.forEach((cleanup) => cleanup());
                    },
                    get isOpen() {
                        return popover.isOpen;
                    },
                };
            },
        };
    },
};

registry.category("services").add("datetime_picker1", datetimePickerService1);

/** @odoo-module **/

import { Component, onWillRender, useState } from "@odoo/owl";
import { useDateTimePicker } from "@web/core/datetime/datetime_hook";
import {
    areDatesEqual,
    deserializeDate,
    deserializeDateTime,
    serializeDateTime,
    formatDate,
    formatDateTime,
    today,
} from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { ensureArray } from "@web/core/utils/arrays";
import { archParseBoolean } from "@web/views/utils";
import { standardFieldProps } from "@web/views/fields/standard_field_props";


export class SearchDateTimeField extends Component {
    static props = {
        ...standardFieldProps,
        endDateField: { type: String, optional: true },
        maxDate: { type: String, optional: true },
        minDate: { type: String, optional: true },
        alwaysRange: { type: Boolean, optional: true },
        placeholder: { type: String, optional: true },
        required: { type: Boolean, optional: true },
        rounding: { type: Number, optional: true },
        startDateField: { type: String, optional: true },
        warnFuture: { type: Boolean, optional: true },
    };

    static template = "SearchDateTimeField";

    //-------------------------------------------------------------------------
    // Getters
    //-------------------------------------------------------------------------

    get endDateField() {
        return 'end_date';
    }

    get field() {
        return this.props.record.fields[this.props.name];
    }

    get startDateField() {
        return 'start_date';
    }

    get values() {
        return ensureArray(this.state.value);
    }

    //-------------------------------------------------------------------------
    // Lifecycle
    //-------------------------------------------------------------------------

    setup() {
        const getPickerProps = () => {
            const value = this.props.record.search_date[this.props.name];
            const pickerProps = {
                value,
                type: this.field.type,
                range: true,
            };
            if (this.props.maxDate) {
                pickerProps.maxDate = this.parseLimitDate(this.props.maxDate);
            }
            if (this.props.minDate) {
                pickerProps.minDate = this.parseLimitDate(this.props.minDate);
            }
            if (!isNaN(this.props.rounding)) {
                pickerProps.rounding = this.props.rounding;
            }
            return pickerProps;
        };

        const dateTimePicker = useDateTimePicker({
            target: "root",
            get pickerProps() {
                return getPickerProps();
            },
            onChange: () => {
                this.state.range = true;
            },
            onApply: () => {
                this.props.record.search_date[this.props.name] = this.state.value
            },
        });
        // Subscribes to changes made on the picker state
        this.state = useState(dateTimePicker.state);
        this.openPicker = dateTimePicker.open;
        
        onWillRender(() => this.triggerIsDirty());
    }

    //-------------------------------------------------------------------------
    // Methods
    //-------------------------------------------------------------------------

    /**
     * @param {number} valueIndex
     */
    async addDate(valueIndex) {
        const values = this.values;
        values[valueIndex] = values[valueIndex ? 0 : 1];

        this.state.focusedDateIndex = valueIndex;
        this.state.value = values;
        this.state.range = true;

        this.openPicker(valueIndex);
    }

    /**
     * @param {number} valueIndex
     */
    getFormattedValue(valueIndex) {
        const value = this.values[valueIndex];
        return value
            ? this.field.type === "date"
                ? formatDate(value)
                : formatDateTime(value)
            : "";
    }

    /**
     * @returns {DateTimePickerProps["value"]}
     */
    getRecordValue() {
        return [false, false]
    }

    /**
     * @param {number} index
     */
    isDateInTheFuture(index) {
        return this.values[index] > today();
    }

    /**
     * @param {string} fieldName
     */
    isEmpty(fieldName) {
        return fieldName === this.startDateField ? !this.values[0] : !this.values[1];
    }

    /**
     * @param {string} value
     */
    parseLimitDate(value) {
        if (value === "today") {
            return value;
        }
        return this.field.type === "date" ? deserializeDate(value) : deserializeDateTime(value);
    }

    /**
     * The given props are used to compute the current value and compare it to
     * the state handled by the datetime hook.
     *
     * @param {boolean} [isDirty]
     */
    triggerIsDirty(isDirty) {
        this.props.record.model.bus.trigger(
            "FIELD_IS_DIRTY",
            isDirty ?? !areDatesEqual(this.getRecordValue(), this.state.value)
        );
    }

    //-------------------------------------------------------------------------
    // Handlers
    //-------------------------------------------------------------------------

    onInput() {
        this.triggerIsDirty(true);
    }
}


const START_DATE_FIELD_OPTION = "start_date_field";
const END_DATE_FIELD_OPTION = "end_date_field";

export const searchDateField = {
    component: SearchDateTimeField,
    displayName: _t("Date"),
    supportedOptions: [
        {
            label: _t("Earliest accepted date"),
            name: "min_date",
            type: "string",
            help: _t(`ISO-formatted date (e.g. "2018-12-31") or "%s".`, "today"),
        },
        {
            label: _t("Latest accepted date"),
            name: "max_date",
            type: "string",
            help: _t(`ISO-formatted date (e.g. "2018-12-31") or "%s".`, "today"),
        },
        {
            label: _t("Warning for future dates"),
            name: "warn_future",
            type: "boolean",
            help: _t(`Displays a warning icon if the input dates are in the future.`),
        },
    ],
    supportedTypes: ["date"],
    extractProps: ({ attrs, options }, dynamicInfo) => ({
        endDateField: options[END_DATE_FIELD_OPTION],
        maxDate: options.max_date,
        minDate: options.min_date,
        alwaysRange: archParseBoolean(options.always_range),
        placeholder: attrs.placeholder,
        required: dynamicInfo.required,
        rounding: options.rounding && parseInt(options.rounding, 10),
        startDateField: options[START_DATE_FIELD_OPTION],
        warnFuture: archParseBoolean(options.warn_future),
    }),
    fieldDependencies: ({ type, attrs, options }) => {
        const deps = [];
        if (options[START_DATE_FIELD_OPTION]) {
            deps.push({
                name: options[START_DATE_FIELD_OPTION],
                type,
                readonly: false,
                ...attrs,
            });
            if (options[END_DATE_FIELD_OPTION]) {
                console.warn(
                    `A field cannot have both ${START_DATE_FIELD_OPTION} and ${END_DATE_FIELD_OPTION} options at the same time`
                );
            }
        } else if (options[END_DATE_FIELD_OPTION]) {
            deps.push({
                name: options[END_DATE_FIELD_OPTION],
                type,
                readonly: false,
                ...attrs,
            });
        }
        return deps;
    },
};

export const searchDateTimeField = {
    ...searchDateField,
    displayName: _t("Date & Time"),
    supportedOptions: [
        ...searchDateField.supportedOptions,
        {
            label: _t("Time interval"),
            name: "rounding",
            type: "number",
            default: 5,
            help: _t(
                `Control the number of minutes in the time selection. E.g. set it to 15 to work in quarters.`
            ),
        },
    ],
    supportedTypes: ["datetime"],
};

export const searchDateRangeField = {
    ...searchDateTimeField,
    displayName: _t("Date Range"),
    supportedOptions: [
        ...searchDateTimeField.supportedOptions,
        {
            label: _t("Start date field"),
            name: START_DATE_FIELD_OPTION,
            type: "field",
            availableTypes: ["date", "datetime"],
        },
        {
            label: _t("End date field"),
            name: END_DATE_FIELD_OPTION,
            type: "field",
            availableTypes: ["date", "datetime"],
        },
        {
            label: _t("Always range"),
            name: "always_range",
            type: "boolean",
            default: true,
            help: _t(
                `Set to true the full range input has to be display by default, even if empty.`
            ),
        },
    ],
    supportedTypes: ["date", "datetime"],
};

registry.category("fields").add("search_date", searchDateRangeField)

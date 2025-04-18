/** @odoo-module **/

import { onWillRender, useState } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { localization } from "@web/core/l10n/localization";
import {DateTimeField} from "@web/views/fields/datetime/datetime_field";
import {useDateTimePicker1} from "./datetime_hook"

import {
    areDatesEqual,
    deserializeDate,
    deserializeDateTime
} from "@web/core/l10n/dates";


patch(DateTimeField.prototype, {
    setup() {
        const getPickerProps = () => {
            const value = this.getRecordValue();
            /** @type {DateTimePickerProps} */
            const pickerProps = {
                value,
                type: this.field.type,
                range: this.isRange(value),
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
        const dateTimePicker = useDateTimePicker1({
            target: "root",
            get pickerProps() {
                return getPickerProps();
            },
            onChange: () => {
                this.state.range = this.isRange(this.state.value);
            },
            onApply: () => {
                const toUpdate = {};
                if (Array.isArray(this.state.value)) {
                    // Value is already a range
                    [toUpdate[this.startDateField], toUpdate[this.endDateField]] = this.state.value;
                } else {
                    toUpdate[this.props.name] = this.state.value;
                }
                // when startDateField and endDateField are set, and one of them has changed, we keep
                // the unchanged one to make sure ORM protects both fields from being recomputed by the
                // server, ORM team will handle this properly on master, then we can remove unchanged values
                if (!this.startDateField || !this.endDateField) {
                    // If startDateField or endDateField are not set, delete unchanged fields
                    for (const fieldName in toUpdate) {
                        if (areDatesEqual(toUpdate[fieldName], this.props.record.data[fieldName])) {
                            delete toUpdate[fieldName];
                        }
                    }
                } else {
                    // If both startDateField and endDateField are set, check if they haven't changed
                    if (areDatesEqual(toUpdate[this.startDateField], this.props.record.data[this.startDateField]) &&
                        areDatesEqual(toUpdate[this.endDateField], this.props.record.data[this.endDateField])) {
                        delete toUpdate[this.startDateField];
                        delete toUpdate[this.endDateField];
                    }
                }

                if (Object.keys(toUpdate).length) {
                    this.props.record.update(toUpdate);
                }
            },
        });
        // Subscribes to changes made on the picker state
        this.state = useState(dateTimePicker.state);
        this.openPicker = dateTimePicker.open;

        onWillRender(() => this.triggerIsDirty());
    }, 
    formatDate(value, options = {}) {
        if (!value) {
            return "";
        }
        const zone = this.env.model.user.tz || "default"
        const format = options.format || localization.dateFormat;
        return value.setZone(zone).toFormat(format);
    },

    formatDateTime(value, options = {}) {
        if (!value) {
            return "";
        }
        const zone = this.env.model.user.tz || "default"
        const format = options.format || localization.dateTimeFormat;
        return value.setZone(zone).toFormat(format);
    },

    parseLimitDate(value) {
        if (value === "today") {
            return value;
        }
        return this.field.type === "date" ? deserializeDate(value) : deserializeDateTime(value);
    },

    getFormattedValue(valueIndex) {
        const value = this.values[valueIndex];
        return value
            ? this.field.type === "date"
                ? this.formatDate(value)
                : this.formatDateTime(value)
            : "";
    },
    getRecordValue() {
        const zone = this.env.model.user.tz || "default"
        if (this.relatedField) {
            return [
                this.props.record.data[this.startDateField].setZone(zone),
                this.props.record.data[this.endDateField].setZone(zone),
            ];
        } else {
            const  value = this.props.record.data[this.props.name];
            
            if(value){
                return value.setZone(zone);
            }
            
            return value;
        }
    }


})



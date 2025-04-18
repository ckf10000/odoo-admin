/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import {DateTimePicker} from "@web/core/datetime/datetime_picker";
import { ensureArray } from "@web/core/utils/arrays";
import {
    MAX_VALID_DATE,
    MIN_VALID_DATE,
    clampDate,
    today,
} from "@web/core/l10n/dates";
const { DateTime, Info } = luxon;

const numberRange = (min, max) => [...Array(max - min)].map((_, i) => i + min);
const HOURS = numberRange(0, 24).map((hour) => [hour, String(hour)]);
const MINUTES = numberRange(0, 60).map((minute) => [minute, String(minute || 0).padStart(2, "0")]);
const SECONDS = [...MINUTES];

const parseLimitDate = (value, defaultValue) =>
    clampDate(value === "today" ? today() : value || defaultValue, MIN_VALID_DATE, MAX_VALID_DATE);

patch(DateTimePicker.prototype, {
    onPropsUpdated(props) {
        /** @type {[NullableDateTime] | NullableDateRange} */
        this.values = ensureArray(props.value).map((value) =>
            value && !value.isValid ? null : value
        );
        this.availableHours = HOURS;
        this.availableMinutes = MINUTES.filter((minute) => !(minute[0] % props.rounding));
        this.availableSeconds = props.rounding ? [] : SECONDS;
        this.allowedPrecisionLevels = this.filterPrecisionLevels(
            props.minPrecision,
            props.maxPrecision
        );

        this.additionalMonth = props.range && !this.env.isSmall;
        this.maxDate = parseLimitDate(props.maxDate, MAX_VALID_DATE);
        this.minDate = parseLimitDate(props.minDate, MIN_VALID_DATE);
        if (this.props.type === "date") {
            this.maxDate = this.maxDate.endOf("day");
            this.minDate = this.minDate.startOf("day");
        }

        if (this.maxDate < this.minDate) {
            throw new Error(`DateTimePicker error: given "maxDate" comes before "minDate".`);
        }

        const tz = this.env.services.user.tz;
        if(!this.state.focusDate) {
            var now = DateTime.fromObject({hour: 0, minute: 0, second: 0}, { zone: tz });
            this.state.focusDate = now;
        }else{
            now = this.state.focusDate.setZone(tz);
        }
        // const tz = this.env.services.user.tz;
        // const now = DateTime.fromObject({hour: 12, minute: 0, second: 0}, { zone: tz });
        // this.state.focusDate = now;

        var timeValues = this.values.map((val) => {
            if (!val){
                val = now;
            }
            return [
                val.hour,
                val.minute,
                val.second,
            ]
        });
        if (props.range) {
            this.state.timeValues = timeValues;
        } else {
            this.state.timeValues = [];
            this.state.timeValues[props.focusedDateIndex] = timeValues[props.focusedDateIndex];
        }

        this.shouldAdjustFocusDate = !props.range;
        this.adjustFocus(this.values, props.focusedDateIndex);
        this.handle12HourSystem();
        this.state.timeValues = this.state.timeValues.map((timeValue) => timeValue.map(String));
    }
})



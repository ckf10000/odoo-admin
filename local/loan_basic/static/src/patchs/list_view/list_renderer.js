/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { getFormattedValue } from "@web/views/utils";
import { localization } from "@web/core/l10n/localization";
import {ListRenderer} from "@web/views/list/list_renderer";


patch(ListRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        this.user = useService("user");
    },

    // get hasSelectors() {
    //     // return this.props.allowSelectors && !this.env.isSmall && (this.env.searchModel.tools.showSelector || Object.values(this.env.searchModel.searchItems).length===0 || this.env.inDialog);
    //     return this.props.allowSelectors && !this.env.isSmall && (this.env.searchModel.tools.showSelector || this.env.inDialog);
    // },

    shouldReverseHeader(column) {
        return false;
    },

    getFormattedValue(column, record) {
        const fieldName = column.name;
        if (column.options.enable_formatting === false) {
            return record.data[fieldName];
        }
        console.log(fieldName, record.data[fieldName])
        if (record.fields[fieldName].type === "datetime" && record.data[fieldName]){
            const zone = this.user.tz || "default"
            const format = localization.dateTimeFormat;
            return record.data[fieldName].setZone(zone).toFormat(format);
        }
        return getFormattedValue(record, fieldName, column.attrs);
    }
})

// ListRenderer.template='jhy.ListRenderer'
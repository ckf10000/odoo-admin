/** @odoo-module **/

import { standardFieldProps } from "@web/views/fields/standard_field_props";

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

import { Component } from "@odoo/owl";

export class BooleanSelectionField extends Component {
    static template = "BooleanSelectionField";
    static props = {
        ...standardFieldProps,
        selection: { type: Array, optional: true},
    };
    static defaultProps = {
        selection: [
            ['', ''],
            ['0', _t("No")],
            ['1', _t("Yes")]
        ],
    };
    get options() {
        return this.props.selection;
    }

    get string() {
        const value = this.props.record.data[this.props.name];
        const string = this.options.find((o) => o[0] === value)
        return string ? string[1] : '';
    }
    get value() {
        const record_vlaue = this.props.record.data[this.props.name];
        if( record_vlaue === true){
            return '1'
        }else if(record_vlaue === false){
            return '0'
        }else{
            return ''
        }
        return record_vlaue
    }

    /**
     * @param {Event} ev
     */
    onChange(ev) {
        const value = ev.target.value;
        if(value === '1'){
            this.props.record.update({ [this.props.name]: true });
        }else if(value === '0'){
            this.props.record.update({ [this.props.name]: false });
        }else{
            this.props.record.update({ [this.props.name]: '' });
        }
    }
    
}

export const booleanSelectionField = {
    component: BooleanSelectionField,
    displayName: _t("Boolean Selection"),
    supportedTypes: ["boolean"],
    isEmpty: (record, fieldName) => record.data[fieldName] === false,
    extractProps: (fieldInfo, dynamicInfo) => ({
        selection: fieldInfo.options.selection,
    })
};

registry.category("fields").add("boolean_selection", booleanSelectionField);
